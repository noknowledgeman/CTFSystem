# Validator Manual Playbook

This playbook documents manual validation scenarios for the generalized validator.

## 1. Prerequisites

- Stack running (`ctfd`, `validation-service`, `mariadb`, `redis`)
- Group-to-VM mapping set in `.env` (`VAL_GROUP_VM_MAP`)
- Validator SSH key distributed to student VMs

## 2. API Endpoints Used

- Upload: `POST /submissions/upload`
- Trigger validation: `POST /validate/{submission_id}`
- Run status: `GET /validate/status/{run_id}`
- Dashboard: `GET /admin/dashboard`

## 3. Manual Scenarios

### Scenario A: Simple web sample (from provided CTF-3 style challenge)

Reference material:
- `docs/index.html`
- `docs/508949-138408 - CTF - 3 - Rijk van Putten - 04 December 2025 235 PM/README.md`

Expected:
- Container check passes
- Service check passes for web port
- Verify script passes
- Submission status becomes `valid` (if CTFd token/config are correct)

### Scenario B: Non-web challenge

Use `validation-service/tests/fixtures/non-web/challenge.yaml` as a model.

Expected:
- TCP service check (e.g., SSH) passes
- Optional command step passes
- Verify script step passes

### Scenario C: Multi-step challenge

Use `validation-service/tests/fixtures/multi-step/challenge.yaml` as a model.

Expected:
- Ordered step execution in run details
- Early required-step failures produce `invalid` with clear failure location
- Optional steps do not fail whole run when marked `required: false`

## 4. Failure Analysis Guidance

Inspect `details` in validation run response:

- Each step is logged as:
  - step index
  - step type
  - required flag
  - pass/fail
  - step output/error details

Common causes:
- SSH timeout or key mismatch
- Wrong remote deployment directory
- Incorrect service protocol/port/path
- Verify script missing dependencies or wrong expected flag
