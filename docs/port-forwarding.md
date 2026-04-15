# Port Forwarding Workflow

Students usually access challenge services through SSH forwarding when direct routing is unavailable.

## Local to Student VM Forwarding

Example: expose a service on student VM port `8080` as local `18080`.

```bash
ssh -L 18080:127.0.0.1:8080 student@<student_vm_ip>
```

Then browse:

- `http://127.0.0.1:18080`

## Multi-hop Forwarding via Admin VM

If student VMs are only reachable from Admin VM:

```bash
ssh -L 18080:<student_vm_ip>:8080 admin@<admin_vm_ip>
```

## Validation Service Connectivity Checks

The validator checks:

- SSH connectivity to mapped VM host
- Docker containers are running
- Declared challenge port is listening
- verify script result includes expected flag

If any check fails, the submission is marked invalid/error and can be re-run after fixes.
