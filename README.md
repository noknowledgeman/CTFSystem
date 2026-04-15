# CTFd + Automated Validation Service

This repository implements the Honours College proposal: deploy CTFd for the competition platform and run an automated validation service that checks student challenge deployments over SSH.

## Components

- `docker-compose.yml`: orchestration for CTFd, MariaDB, Redis, and validation service.
- `validation-service/`: FastAPI service for ZIP ingestion, remote checks, verify script execution, and CTFd sync.
- `sample-submission/`: reference challenge package for students.
- `docs/`: deployment and usage guides.

## Quick Start

1. Copy environment template:
   - `cp .env.example .env`
2. Create SSH key secret file used by validation service:
   - `mkdir -p secrets`
   - place private key at `secrets/id_ed25519`
3. Start stack:
   - `docker compose up --build -d`
4. Access services:
   - CTFd: `http://localhost:8000`
   - Validation API docs: `http://localhost:8080/docs`

## Validation Workflow

1. Student uploads ZIP package with `docker-compose.yml`, `challenge.yaml`, verify script, and write-up.
2. Service parses and validates metadata.
3. Service SSHes into mapped student VM.
4. Service checks challenge container health and target port.
5. Service runs verify script and confirms expected flag.
6. Service creates/updates challenge metadata in CTFd via REST API.

## Important Configuration

Set these variables in `.env`:

- `VAL_GROUP_VM_MAP`: JSON mapping group IDs to VM IP/host.
- `VAL_CTFD_API_TOKEN`: CTFd admin API token.
- `VAL_SSH_PRIVATE_KEY_FILE`: host path to private key file.
- `VAL_SSH_USERNAME`: account on student VMs.

See `docs/student-guide.md`, `docs/vm-setup.md`, and `docs/port-forwarding.md` for operational details.
