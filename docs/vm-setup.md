# Admin VM Setup

## Objective

Run CTFd and the validation service inside the isolated subnet, with SSH access to each student VM.

## Prerequisites

- Docker and Docker Compose installed on Admin VM
- Reachability from Admin VM to each student VM over SSH
- An SSH keypair for validator access

### Expected VM structure

- **Admin VM**: hosts CTFd + validation service containers.
- **Student VM(s)**: each group has a VM reachable from Admin VM over SSH and capable of running Docker Compose.
- **SSH account**: student VM should contain a `student` user (or value from `VAL_SSH_USERNAME`) with the validator public key in `~student/.ssh/authorized_keys`.

## Steps

1. Clone this repository on the Admin VM.
2. Copy `.env.example` to `.env`.
3. Create `secrets/id_ed25519` with the validator private key.
4. Distribute the corresponding public key to student VMs:
   - append to `~student/.ssh/authorized_keys`
5. Edit `.env`:
   - set `VAL_GROUP_VM_MAP` with group IDs and VM hosts
   - set `VAL_CTFD_API_TOKEN` from CTFd admin settings
6. Start stack:
   - `docker compose up --build -d`
7. Verify health:
   - `curl http://localhost:8080/health`
   - open `http://localhost:8000` (CTFd)

## Access points

- CTFd UI (players/admin): `http://<admin-vm-host>:8000`
- Validation API health: `http://<admin-vm-host>:8080/health`
- Validation API docs (Swagger): `http://<admin-vm-host>:8080/docs`

For production, put CTFd behind HTTPS and restrict port `8080` to staff/VPN only.

## Operational Notes

- Rotate SSH keys each academic period.
- Restrict Admin VM SSH egress to known student VM ranges.
- Keep CTFd admin token confidential and rotate when staff changes.
