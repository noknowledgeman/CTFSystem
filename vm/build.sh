#!/bin/bash
# Prepare phase: boot each challenge VM, load its docker images (pull registry
# images + build local ones) into the VM's qcow2 disk, then power it off.
# Deploy reboots those disks offline. One bad sample does NOT abort the rest.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

PROJECTS_DIR="${1:-../samples}"
mkdir -p "$VM_DIR"

# Copy compose + build context into the VM, then pull registry images and build
# local ones so nothing needs the network at deploy time.
# --ignore-buildable: services with a build: section are built, not pulled — a
# build-only image tag (e.g. a private GHCR ref) would otherwise fail pull with
# "unauthorized".
load_images() {
  local name="$1"
  local dir="$2"
  local ip="$3"

  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" "mkdir -p /root/$name"
  scp -r $SSH_OPTS -i "$SSH_KEY" "$dir/." "root@$ip:/root/$name/"

  local attempts=0
  until ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "cd /root/$name && docker compose pull --ignore-buildable && docker compose build"; do
    attempts=$((attempts + 1))
    if [[ $attempts -ge 5 ]]; then
      echo "image load failed after 5 attempts on $name" >&2
      return 1
    fi
    log "Image load failed, retrying ($attempts/5)..."
    sleep 5
  done
}

# --- Main ---

ensure_vm_nat

declare -A PIDS
declare -A IPS
declare -A NAMES_TO_DIRS

index=0
for dir in "$PROJECTS_DIR"/*/; do
  [[ -f "$dir/compose.yaml" || -f "$dir/compose.yml" || -f "$dir/docker-compose.yaml" || -f "$dir/docker-compose.yml" ]] || continue
  name=$(basename "$dir")
  ip="$IP_BASE.$((IP_START + index))"
  mac=$(derive_mac "$name")

  log "Booting VM for: $name (ip=$ip mac=$mac)"
  clone_disk "$name"
  pid=$(boot_vm "$name" "$ip" "$mac")

  PIDS[$name]=$pid
  IPS[$name]=$ip
  NAMES_TO_DIRS[$name]=$dir
  index=$((index + 1))
done

# Load images per VM, then power it off. Failures are isolated: log, skip state,
# still power the VM down, keep going.
> "$STATE_FILE"
declare -a FAILED=()
for name in "${!PIDS[@]}"; do
  dir="${NAMES_TO_DIRS[$name]}"
  ip="${IPS[$name]}"
  pid="${PIDS[$name]}"

  log "Waiting for SSH: $name ($ip)"
  if ! wait_for_ssh "$ip"; then
    log "SSH never came up for $name — skipping"
    FAILED+=("$name")
    kill -9 "$pid" 2>/dev/null || true
    continue
  fi
  sleep 3

  log "Growing root fs on $name"
  grow_root "$ip"

  log "Setting MTU $VM_MTU on $name"
  set_mtu "$ip"

  log "Loading images: $name"
  if ! load_images "$name" "$dir" "$ip"; then
    log "Image load failed for $name — skipping (not added to state)"
    FAILED+=("$name")
    shutdown_vm "$name" "$ip" "$pid"
    continue
  fi

  shutdown_vm "$name" "$ip" "$pid"
  echo "VM_IP_${name}=${ip}" >> "$STATE_FILE"
done

if [[ ${#FAILED[@]} -gt 0 ]]; then
  log "Build finished with failures: ${FAILED[*]}"
  log "State (successful VMs) written to $STATE_FILE"
  exit 1
fi

log "Build complete. All VMs prepared and powered off. State at $STATE_FILE"
