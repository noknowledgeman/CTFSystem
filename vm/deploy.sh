#!/bin/bash
# Run phase: boot the VM disks prepared by build.sh (images already cached on
# disk, no pull needed), then docker compose up -d. VMs stay running to serve
# the challenges. One bad sample does NOT abort the rest.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

PROJECTS_DIR="${1:-../samples}"
ENV_FILE="${2:-../.env}"

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No state file found at $STATE_FILE — run build.sh first" >&2
  exit 1
fi

run_compose() {
  local name="$1"
  local ip="$2"

  local attempts=0
  until ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "cd /root/$name && docker compose up -d"; do
    attempts=$((attempts + 1))
    if [[ $attempts -ge 5 ]]; then
      echo "docker compose up failed after 5 attempts on $name" >&2
      return 1
    fi
    log "Compose up failed, retrying ($attempts/5)..."
    sleep 5
  done
}

# --- Main ---

ensure_vm_nat

declare -A GROUP_MAP=()
declare -a FAILED=()

# Read state on FD 3 so ssh inside the loop can't drain it (ssh reads stdin,
# which would swallow every line after the first).
while IFS='=' read -r key val <&3; do
  [[ "$key" =~ ^VM_IP_(.+)$ ]] || continue
  name="${BASH_REMATCH[1]}"
  ip="$val"

  if [[ ! -f "$VM_DIR/$name.qcow2" ]]; then
    log "Warning: no prepared disk for $name at $VM_DIR/$name.qcow2 — run build.sh; skipping"
    FAILED+=("$name")
    continue
  fi

  mac=$(derive_mac "$name")
  log "Booting prepared VM: $name ($ip)"
  boot_vm "$name" "$ip" "$mac" >/dev/null

  log "Waiting for SSH: $name ($ip)"
  if ! wait_for_ssh "$ip"; then
    log "SSH never came up for $name — skipping"
    FAILED+=("$name")
    continue
  fi
  set_mtu "$ip"

  log "Deploying: $name ($ip)"
  if ! run_compose "$name" "$ip"; then
    log "Deploy failed for $name — skipping"
    FAILED+=("$name")
    continue
  fi

  GROUP_MAP[$name]=$ip
done 3< "$STATE_FILE"

# Write env file
json="{"
first=true
for name in "${!GROUP_MAP[@]}"; do
  ip="${GROUP_MAP[$name]}"
  if $first; then
    json+="\"$name\":\"$ip\""
    first=false
  else
    json+=",\"$name\":\"$ip\""
  fi
done
json+="}"

if grep -q "^VAL_GROUP_VM_MAP=" "$ENV_FILE" 2>/dev/null; then
  sed -i "s|^VAL_GROUP_VM_MAP=.*|VAL_GROUP_VM_MAP=$json|" "$ENV_FILE"
else
  echo "VAL_GROUP_VM_MAP=$json" >> "$ENV_FILE"
fi
echo "Written to $ENV_FILE"
grep "VAL_GROUP_VM_MAP" "$ENV_FILE"

if [[ ${#FAILED[@]} -gt 0 ]]; then
  log "Deploy finished with failures: ${FAILED[*]}"
  exit 1
fi
log "Deploy complete. VMs running."
