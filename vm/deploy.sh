#!/bin/bash

set -e

# --- Config ---
BASE_IMAGE="/home/os1to/Honours/DProj/vm/base.qcow2"
PROJECTS_DIR="${1:-../samples}"
ENV_FILE="${2:-../.env}"
VM_DIR="$(pwd)/vms"
SSH_KEY="../secrets/id_ed25519"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"

mkdir -p "$VM_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

cleanup() {
  if [[ $? -ne 0 ]]; then
    log "Error — killing QEMU processes..."
    sudo pkill -f qemu-system-x86_64 2>/dev/null || true
  fi
}
trap cleanup EXIT

declare -A GROUP_MAP

boot_vm() {
  local name="$1"
  local vm_img="$VM_DIR/$name.qcow2"

  # Clone base image
  log "Cloning base image -> $vm_img"
  qemu-img create -f qcow2 -b "$BASE_IMAGE" -F qcow2 "$vm_img"

  # Generate a deterministic MAC from the name so we can query DHCP later
  local mac
  mac=$(echo "$name" | md5sum | sed 's/\(..\)\(..\)\(..\)\(..\)\(..\).*/52:54:00:\3:\4:\5/')

  # Boot VM in background
  log "Starting qemu for $name (mac=$mac)"
  qemu-system-x86_64 \
    -cpu host \
    -machine q35,accel=kvm \
    -m 2048 \
    -smp 2 \
    -nographic \
    -netdev id=net0,type=bridge,br=virbr0 \
    -device virtio-net-pci,netdev=net0,mac="$mac" \
    -drive if=virtio,format=qcow2,file="$vm_img" \
    -serial file:"$VM_DIR/$name.serial.log" \
    -monitor none \
    >"$VM_DIR/$name.log" 2>&1 &

  local qpid=$!
  log "QEMU PID=$qpid, logs at $VM_DIR/$name.log"
  echo "$qpid"
}

get_ip_for_mac() {
  local mac="$1"
  local ip=""
  local attempts=0

  while [[ -z "$ip" && $attempts -lt 30 ]]; do
    ip=$(sudo virsh net-dhcp-leases default 2>/dev/null \
      | grep -i "$mac" \
      | awk '{print $5}' \
      | cut -d'/' -f1)
    if [[ -z "$ip" ]]; then
      log "  IP poll attempt $attempts/30 for $mac..."
      sleep 2
      attempts=$((attempts + 1))
    fi
  done

  echo "$ip"
}

wait_for_ssh() {
  local ip="$1"
  local attempts=0

  while ! ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" true 2>/dev/null; do
    log "  SSH attempt $attempts/30 on $ip..."
    sleep 2
    attempts=$((attempts+1))
    if [[ $attempts -gt 30 ]]; then
      echo "Timeout waiting for SSH on $ip" >&2
      return 1
    fi
  done
}

copy_and_run() {
  local name="$1"
  local dir="$2"
  local ip="$3"

  # Copy project files into VM
  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" "mkdir -p /root/$name"
  scp -r $SSH_OPTS -i "$SSH_KEY" "$dir/." "root@$ip:/root/$name/"

  # Run docker compose inside VM
  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "cd /root/$name && docker compose up -d"
}

# --- Main ---

declare -A PIDS
declare -A MACS
declare -A NAMES_TO_DIRS

# Boot all VMs
for dir in "$PROJECTS_DIR"/*/; do
  [[ -f "$dir/compose.yaml" || -f "$dir/compose.yml" || -f "$dir/docker-compose.yaml" || -f "$dir/docker-compose.yml" ]] || continue
  name=$(basename "$dir")

  log "Booting VM for: $name"
  pid=$(boot_vm "$name")
  mac=$(echo "$name" | md5sum | sed 's/\(..\)\(..\)\(..\)\(..\)\(..\).*/52:54:00:\3:\4:\5/')

  PIDS[$name]=$pid
  MACS[$name]=$mac
  NAMES_TO_DIRS[$name]=$dir
done

# Wait for each VM, copy files, run compose
for name in "${!PIDS[@]}"; do
  dir="${NAMES_TO_DIRS[$name]}"
  mac="${MACS[$name]}"

  log "Waiting for IP: $name ($mac)"
  ip=$(get_ip_for_mac "$mac")

  if [[ -z "$ip" ]]; then
    echo "Failed to get IP for $name, skipping" >&2
    continue
  fi

  log "$name -> $ip"

  log "Waiting for SSH: $name ($ip)"
  wait_for_ssh "$ip"

  log "Copying files and starting compose: $name"
  copy_and_run "$name" "$dir" "$ip"

  GROUP_MAP[$name]=$ip
done

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

echo "VAL_GROUP_VM_MAP=$json" > "$ENV_FILE"
echo "Written to $ENV_FILE"
cat "$ENV_FILE"