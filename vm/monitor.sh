#!/bin/bash

VM_DIR="$(cd "$(dirname "$0")" && pwd)/vms"
SESSION="vm-monitor"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 220 -y 50

logs=()
for log in "$VM_DIR"/*.serial.log; do
  [[ -f "$log" ]] || continue
  logs+=("$log")
done

if [[ ${#logs[@]} -eq 0 ]]; then
  echo "No serial logs found in $VM_DIR — run deploy.sh first"
  exit 1
fi

# First VM in initial pane
name=$(basename "${logs[0]}" .serial.log)
tmux rename-window -t "$SESSION:0" "vms"
tmux send-keys -t "$SESSION:0" "tail -f '${logs[0]}'" Enter
tmux select-pane -t "$SESSION:0" -T "$name"

# Each additional VM gets a vertical split
for log in "${logs[@]:1}"; do
  name=$(basename "$log" .serial.log)
  tmux split-window -t "$SESSION:0" -h "tail -f '$log'"
  tmux select-pane -T "$name"
done

tmux select-layout -t "$SESSION:0" even-horizontal

tmux attach -t "$SESSION"
