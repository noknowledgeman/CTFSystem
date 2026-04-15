# Student Submission Guide

## Required ZIP Layout

Create one ZIP containing:

- `docker-compose.yml`
- `challenge.yaml`
- verify script (`verify.py` or `verify.sh`)
- write-up (`writeup.md`, `README.md`, or `writeup.txt`)
- challenge source files (Dockerfile, app code, scripts)

## challenge.yaml Template

```yaml
name: "Challenge Name"
description: "Short challenge description"
flag: "CTF{example_flag}"
difficulty: "simple" # simple | medium | difficult
port: 8080
verify:
  script: "verify.py"
  language: "python" # python | bash
  timeout: 30
```

## Submission Rules

- Challenge must run from your VM using Docker Compose.
- The declared `port` must be reachable on your VM.
- Verify script must exit with code `0` on success.
- Verify output must include the expected flag value.
- Use deterministic startup commands; avoid manual runtime setup.
