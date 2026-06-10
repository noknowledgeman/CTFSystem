#!/bin/bash
# Shared config + functions for build.sh (prepare images) and deploy.sh (run them).
# Both boot VMs on libvirt's virbr0, so the boot/ssh/nat/mtu logic lives here once.

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Config ---
BASE_IMAGE="$LIB_DIR/base.qcow2"
# Per-VM disk size. Base stays small; each clone is grown to this and the guest
# root partition is expanded online (growpart) on boot. Bigger than base default
# so image builds (apt/pip) don't hit "no space left on device".
VM_DISK_SIZE="${VM_DISK_SIZE:-5G}"
VM_DIR="$LIB_DIR/vms"
SSH_KEY="$LIB_DIR/../secrets/id_ed25519"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o ServerAliveInterval=15 -o ServerAliveCountMax=20"
IP_BASE="192.168.122"
IP_START=100
STATE_FILE="$VM_DIR/state.env"
VM_SUBNET="$IP_BASE.0/24"
# Host uplink (e.g. iPhone/USB tether) can force a low path MTU. VMs default to
# 1500 -> oversized TLS packets blackhole on docker pull. Clamp to the safe
# floor. 1280 is the IPv6 minimum: always fits, mild efficiency cost.
VM_MTU="${VM_MTU:-1280}"

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

derive_mac() {
  echo "$1" | md5sum | sed 's/\(..\)\(..\)\(..\)\(..\)\(..\).*/52:54:00:\3:\4:\5/'
}

# Re-assert libvirt NAT/forward/MSS rules for the VM subnet. Docker daemon
# (re)start sets FORWARD policy DROP and flushes these, killing VM egress.
# Idempotent: -C checks before adding.
ensure_vm_nat() {
  log "Ensuring NAT/forward rules for $VM_SUBNET"

  sudo sysctl -q -w net.ipv4.ip_forward=1

  # Masquerade VM traffic leaving the host (skip intra-subnet)
  sudo iptables -t nat -C POSTROUTING -s "$VM_SUBNET" ! -d "$VM_SUBNET" -j MASQUERADE 2>/dev/null \
    || sudo iptables -t nat -A POSTROUTING -s "$VM_SUBNET" ! -d "$VM_SUBNET" -j MASQUERADE

  # Punch VM subnet through Docker's FORWARD policy DROP (insert at top)
  sudo iptables -C FORWARD -s "$VM_SUBNET" -j ACCEPT 2>/dev/null \
    || sudo iptables -I FORWARD -s "$VM_SUBNET" -j ACCEPT
  sudo iptables -C FORWARD -d "$VM_SUBNET" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null \
    || sudo iptables -I FORWARD -d "$VM_SUBNET" -m state --state RELATED,ESTABLISHED -j ACCEPT

  # Clamp TCP MSS to path MTU — fixes TLS resets when host egress MTU < 1500
  sudo iptables -t mangle -C FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null \
    || sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
}

# Fresh COW disk backed by the base image, grown to VM_DISK_SIZE. Used by build.
# Only the block device is enlarged here (grub-safe); the guest partition is
# expanded online by grow_root after boot.
clone_disk() {
  local name="$1"
  local vm_img="$VM_DIR/$name.qcow2"
  rm -f "$vm_img"
  log "Cloning base image -> $vm_img ($VM_DISK_SIZE)"
  qemu-img create -f qcow2 -b "$BASE_IMAGE" -F qcow2 "$vm_img" >/dev/null
  qemu-img resize "$vm_img" "$VM_DISK_SIZE" >/dev/null
}

# Grow the guest root partition + filesystem to fill the resized disk. Done live
# in-guest (growpart + resize2fs): no data moved, bootloader untouched — unlike
# virt-resize, which desyncs GRUB and drops to grub rescue.
grow_root() {
  local ip="$1"
  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "growpart /dev/vda 1 && resize2fs /dev/vda1" \
    || log "Warning: failed to grow root fs on $ip"
}

# Register the MAC->IP DHCP lease and boot qemu against an existing disk.
# Echoes the qemu PID. Disk must already exist (clone_disk for build, the
# image-loaded disk for deploy).
boot_vm() {
  local name="$1"
  local ip="$2"
  local mac="$3"
  local vm_img="$VM_DIR/$name.qcow2"

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

# Clamp the VM's default-route interface to VM_MTU.
set_mtu() {
  local ip="$1"
  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" \
    "ip link set dev \$(ip route show default | grep -o 'dev [^ ]*' | cut -d' ' -f2) mtu $VM_MTU" \
    || log "Warning: failed to set MTU on $ip"
}

# Graceful poweroff so the qcow2 (with its cached images) closes cleanly.
# Falls back to killing just this VM's PID after a timeout — never pkills all.
shutdown_vm() {
  local name="$1"
  local ip="$2"
  local pid="$3"

  log "Powering off $name"
  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" "poweroff" 2>/dev/null || true

  local waited=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 2
    waited=$((waited + 2))
    if [[ $waited -ge 60 ]]; then
      log "  $name did not power off in 60s; killing pid $pid"
      kill -9 "$pid" 2>/dev/null || true
      break
    fi
  done
  log "  $name down"
}
