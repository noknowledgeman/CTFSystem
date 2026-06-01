#!/bin/bash

set -e

# --- Config ---
PROJECTS_DIR="${1:-../samples}"
ENV_FILE="${2:-../.env}"
VM_DIR="$(pwd)/vms"
SSH_KEY="../secrets/id_ed25519"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o ServerAliveInterval=15 -o ServerAliveCountMax=20"
STATE_FILE="$VM_DIR/state.env"

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No state file found at $STATE_FILE — run build.sh first" >&2
  exit 1
fi

run_compose() {
  local name="$1"
  local dir="$2"
  local ip="$3"

  ssh $SSH_OPTS -i "$SSH_KEY" root@"$ip" "mkdir -p /root/$name"
  scp -r $SSH_OPTS -i "$SSH_KEY" "$dir/." "root@$ip:/root/$name/"

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

declare -A GROUP_MAP

while IFS='=' read -r key val; do
  [[ "$key" =~ ^VM_IP_(.+)$ ]] || continue
  name="${BASH_REMATCH[1]}"
  ip="$val"

  dir="$PROJECTS_DIR/$name/"
  if [[ ! -d "$dir" ]]; then
    log "Warning: no directory for $name at $dir, skipping"
    continue
  fi

  log "Deploying: $name ($ip)"
  run_compose "$name" "$dir" "$ip"

  GROUP_MAP[$name]=$ip
done < "$STATE_FILE"

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
