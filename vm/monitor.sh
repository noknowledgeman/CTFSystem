#!/bin/bash

VM_DIR="$(cd "$(dirname "$0")" && pwd)/vms"
SESSION="vm-monitor"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 220 -y 50

first=true
for serial in "$VM_DIR"/*.serial.log; do
  [[ -f "$serial" ]] || continue
  name=$(basename "$serial" .serial.log)

  if $first; then
    tmux rename-window -t "$SESSION:0" "$name-serial"
    tmux send-keys -t "$SESSION:0" "tail -f '$serial'" Enter
    first=false
  else
    tmux new-window -t "$SESSION" -n "$name-serial"
    tmux send-keys -t "$SESSION" "tail -f '$serial'" Enter
  fi

  # QEMU stderr log in a split pane
  qemu_log="$VM_DIR/$name.log"
  if [[ -f "$qemu_log" ]]; then
    tmux split-window -t "$SESSION" -v "tail -f '$qemu_log'"
    tmux select-pane -t "$SESSION" -U
  fi
done

if $first; then
  echo "No serial logs found in $VM_DIR — run deploy.sh first"
  exit 1
fi

tmux attach -t "$SESSION"
