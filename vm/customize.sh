#! /bin/bash

sudo virt-customize -a base.qcow2 \
  --ssh-inject root:file:../secrets/id_ed25519.pub \
  --install ca-certificates,curl,openssh-server \
  --run-command 'install -m 0755 -d /etc/apt/keyrings' \
  --run-command 'curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc' \
  --run-command 'chmod a+r /etc/apt/keyrings/docker.asc' \
  --run-command 'printf "Types: deb\nURIs: https://download.docker.com/linux/debian\nSuites: trixie\nComponents: stable\nArchitectures: amd64\nSigned-By: /etc/apt/keyrings/docker.asc\n" > /etc/apt/sources.list.d/docker.sources' \
  --update \
  --install docker-ce,docker-ce-cli,containerd.io,docker-compose-plugin \
  --run-command 'systemctl enable docker' \
  --run-command 'systemctl enable ssh'
