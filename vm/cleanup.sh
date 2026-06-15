#!/bin/bash
# Two independent actions, pick one:
#   cleanup.sh shutdown   kill running QEMU VMs (leaves disks intact)
#   cleanup.sh images     remove VM disk images (.qcow2)

VM_DIR="$(cd "$(dirname "$0")" && pwd)/vms"

shutdown_vms() {
  echo "Killing QEMU processes..."
  pkill -f qemu-system-x86_64 2>/dev/null || true
  echo "Done."
}

remove_images() {
  echo "Removing VM disk images..."
  rm -f "$VM_DIR"/*.qcow2
  echo "Done."
}

case "${1:-}" in
  shutdown) shutdown_vms ;;
  images)   remove_images ;;
  *)
    echo "Usage: $0 {shutdown|images}" >&2
    echo "  shutdown  kill running QEMU VMs" >&2
    echo "  images    remove VM disk images (.qcow2)" >&2
    exit 1
    ;;
esac
