#!/bin/bash

set -e

# --- Config ---
BASE_IMAGE="/home/os1to/Honours/DProj/vm/base.qcow2"
PROJECTS_DIR="${1:-../samples}"
VM_DIR="$(pwd)/vms"
SSH_KEY="../secrets/id_ed25519"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o ServerAliveInterval=15 -o ServerAliveCountMax=20"
IP_BASE="192.168.122"
IP_START=100
STATE_FILE="$VM_DIR/state.env"

mkdir -p "$VM_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

cleanup() {
  if [[ $? -ne 0 ]]; then
    log "Error — killing QEMU processes..."
    sudo pkill -f qemu-system-x86_64 2>/dev/null || true
  fi
}
trap cleanup EXIT

derive_mac() {
  echo "$1" | md5sum | sed 's/\(..\)\(..\)\(..\)\(..\)\(..\).*/52:54:00:\3:\4:\5/'
}

boot_vm() {
  local name="$1"
  local ip="$2"
  local mac="$3"
  local vm_img="$VM_DIR/$name.qcow2"

  log "Cloning base image -> $vm_img"
  qemu-img create -f qcow2 -b "$BASE_IMAGE" -F qcow2 "$vm_img"

  sudo virsh net-update default delete ip-dhcp-host \
    "<host mac='$mac'/>" --live --config 2>/dev/null || true
  sudo virsh net-update default add ip-dhcp-host \
    "<host mac='$mac' ip='$ip'/>" --live --config

  log "Starting qemu for $name (mac=$mac ip=$ip)"
  qemu-system-x86_64 \
    -cpu host \
    -machine q35,accel=kvm \
    -m 4096 \
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

wait_for_ssh() {
  local ip="$1"
  local attempts=0

  while ! ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" true 2>/dev/null; do
    log "  SSH attempt $attempts/60 on $ip..."
    sleep 5
    attempts=$((attempts + 1))
    if [[ $attempts -gt 60 ]]; then
      echo "Timeout waiting for SSH on $ip" >&2
      return 1
    fi
  done
}

pull_images() {
  local name="$1"
  local dir="$2"
  local ip="$3"

  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" "mkdir -p /root/$name"
  scp -r $SSH_OPTS -i "$SSH_KEY" "$dir/." "root@$ip:/root/$name/"

  local attempts=0
  until ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "cd /root/$name && docker compose pull"; do
    attempts=$((attempts + 1))
    if [[ $attempts -ge 5 ]]; then
      echo "docker compose pull failed after 5 attempts on $name" >&2
      return 1
    fi
    log "Pull failed, retrying ($attempts/5)..."
    sleep 5
  done
}

# --- Main ---

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
  pid=$(boot_vm "$name" "$ip" "$mac")

  PIDS[$name]=$pid
  IPS[$name]=$ip
  NAMES_TO_DIRS[$name]=$dir
  index=$((index + 1))
done

# Wait for SSH and pull images
> "$STATE_FILE"
for name in "${!PIDS[@]}"; do
  dir="${NAMES_TO_DIRS[$name]}"
  ip="${IPS[$name]}"

  log "Waiting for SSH: $name ($ip)"
  wait_for_ssh "$ip"
  sleep 3

  log "Pulling images: $name"
  pull_images "$name" "$dir" "$ip"

  echo "VM_IP_${name}=${ip}" >> "$STATE_FILE"
done

log "Build complete. State written to $STATE_FILE"
