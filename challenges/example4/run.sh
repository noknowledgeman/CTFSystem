#!/bin/bash

# Stop the script immediately if any command fails
set -e

echo "[-] Cleaning up old container..."
# Try to remove the container, suppress errors if it doesn't exist
docker rm -f challenge9 2>/dev/null || true

echo "[+] Building image (No Cache)..."
docker build --no-cache -t challenge9 .

echo "[+] Starting container..."
docker run -d \
  --name challenge9 \
  -p 8080:8080 \
  -p 21:21 \
  -p 30000-30010:30000-30010 \
  -v "$(pwd)/src:/app" \
  challenge9

echo "[SUCCESS] Challenge is running on http://localhost:8080"
echo "[SUCCESS] FTP (anonymous) is available on port 21"