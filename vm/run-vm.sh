#!/bin/bash

VM=$1

qemu-system-x86_64 \
  -cpu host \
  -machine type=q35 \
  -enable-kvm \
  -m 2048 \
  -smp 2 \
  -nographic \
  -netdev id=net0,type=bridge,br=virbr0 \
  -device virtio-net-pci,netdev=net0 \
  -drive if=virtio,format=qcow2,file=$VM
