# Student Submission Guide

## Required ZIP Layout

Create one ZIP containing:

- Compose file at ZIP root (`docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, or `compose.yaml`)
- `challenge.yaml`
- verify script (`verify.py` or `verify.sh`)
- write-up (`writeup.md`, `README.md`, or `writeup.txt`)
- challenge source files (Dockerfile, app code, scripts)

## challenge.yaml Template (v2 required)

All submissions must use the v2 format below.

```yaml
name: "Challenge Name"
description: "Short challenge description"
flag: "CTF{example_flag}"
difficulty: "medium" # simple | medium | difficult
verify:
  script: "verify.py"
  language: "python" # python | bash
  timeout: 60
deployment:
  remote_dir: "/home/student/challenge"
services:
  - name: "web"
    protocol: "http" # tcp | udp | http | https
    host: "127.0.0.1"
    port: 8080
    path: "/health"
    expected_status: 200
  - name: "db"
    protocol: "tcp"
    host: "127.0.0.1"
    port: 5432
validation_steps:
  - type: "container_running"
  - type: "service_check"
    service: "web"
  - type: "service_check"
    service: "db"
  - type: "command"
    command: "echo preflight-ok"
    expect_contains: "preflight-ok"
  - type: "verify_script"
```

### Manual review step example (for non-scriptable checks)

Use this when part of the challenge must be verified by a human (for example, a flag shown only in an image/dialog):

```yaml
validation_steps:
  - type: "container_running"
  - type: "service_check"
    service: "web"
  - type: "manual_review"
    instructions: "Open /proof/dialog.png and confirm the visible flag is CTF{example_flag}."
    evidence_hint: "Attach screenshot of the image/dialog and the command used to produce it."
  - type: "verify_script"
```

If `manual_review` is required, your run will be marked `needs_review` until staff approves it.

### Non-web example

```yaml
name: "SSH Recovery"
description: "Challenge that validates an SSH-accessible service."
flag: "CTF{ssh_example}"
difficulty: "difficult"
verify:
  script: "verify.sh"
  language: "bash"
  timeout: 45
services:
  - name: "ssh"
    protocol: "tcp"
    host: "127.0.0.1"
    port: 22
validation_steps:
  - type: "container_running"
  - type: "service_check"
    service: "ssh"
  - type: "verify_script"
```

## Submission Rules

- Challenge must run from your VM using Docker Compose.
- Every declared `services[]` check must pass.
- Verify script must exit with code `0` on success.
- Verify output must include the expected flag value.
- `verify.language` supports `python` and `bash`.
- Use deterministic startup commands; avoid manual runtime setup.
