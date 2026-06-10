#!/bin/bash

VM_DIR="$(cd "$(dirname "$0")" && pwd)/vms"

echo "Killing QEMU processes..."
pkill -f qemu-system-x86_64 2>/dev/null || true

echo "Removing VM disk images..."
rm -f "$VM_DIR"/*.qcow2

echo "Done."
