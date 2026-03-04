# CTF System – Setup and Links

## Environment

Use a Python 3.11+ virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # or on Windows: venv\Scripts\activate
cd CTFSystem/backend
pip install -r requirements.txt
```

## Competition topology (course environment)

In the Ethical Hacking course, the competition runs in a **virtualised environment** with:

- **One VM per student team**: each group gets its own VM where they deploy their Docker-based challenges.
- An **admin/CTF VM**: runs the CTFSystem backend and frontend, plus the automated validation scripts. This VM can reach all team VMs over the competition subnet.
- During the competition, students use their team VMs to attack other teams’ VMs and solve challenges.

CTFSystem is intended to run on the **admin/CTF VM**. Students access the web UI from within the university network / VPN, log in with their accounts, and see the leaderboard, challenges, and their progress.

## Database setup

1. **Environment**  
   Backend reads from `CTFSystem/backend/.env`. A template is `backend/.env.example`.  
   Defaults:
   - `DATABASE_URL=sqlite:///./ctf.db` → DB file: `CTFSystem/backend/ctf.db`
   - `SECRET_KEY=ctf-dev-secret-change-in-production`
   - `DEFAULT_ADMIN_PASSWORD=admin`

2. **Create database and default admin**  
   From `CTFSystem/backend`:

   ```bash
   PYTHONPATH=. python scripts/init_db.py
   ```

   This creates the SQLite file (if missing), all tables, and a default admin user if none exists.

3. **Database file location**  
   - Path (when running from `backend/`): `CTFSystem/backend/ctf.db`  
   - Absolute (example): `/Users/Artiom/Documents/projects/CTFSystem/backend/ctf.db`

4. **Optional: seed mock data** (challenges, hints, demo players, sample submissions)  
   From `CTFSystem/backend`:
   ```bash
   PYTHONPATH=. python scripts/seed_mock_data.py
   ```
   Demo players: `alice` / `bob` / `charlie` with passwords `player1` / `player2` / `player3`.

## Run the backend

From `CTFSystem/backend`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

When deployed in the course environment, the backend should listen on the admin/CTF VM (e.g. `0.0.0.0:8000`) so the frontend and validation scripts on the same VM can reach it.

## Links (local development)

| What | URL |
|------|-----|
| **API root** | http://localhost:8000 |
| **Swagger UI (OpenAPI docs)** | http://localhost:8000/docs or http://localhost:8000/swagger |
| **ReDoc** | http://localhost:8000/redoc |
| **Health check** | http://localhost:8000/api/health |

## Default admin login

- **Username:** `admin`  
- **Password:** value of `DEFAULT_ADMIN_PASSWORD` in `.env` (default: `admin`)

Use **POST /api/auth/login** with `{"username": "admin", "password": "admin"}` to get a JWT for the admin UI.

## Brightspace challenge submissions → ingestion

In the course workflow, each team submits its self-designed challenge via **Brightspace**. A recommended submission format is:

- A ZIP file containing:
  - `docker/` – Docker context or image build files.
  - `challenge.yaml` – machine-readable metadata (name, category, difficulty, points, expected flag, exposed port, VM identifier, etc.).
  - `writeup.md` – description of the challenge and the steps to solve it.
  - `flag.txt` – the intended flag value.

An offline helper script (or manual process) can convert `challenge.yaml` + `flag.txt` into a `ChallengeSubmissionMetadata` JSON payload. That JSON is then sent from the admin/CTF VM to:

- `POST /api/admin/challenges/ingest`

The ingestion endpoint stores:

- The challenge definition (name, category, difficulty, points, hashed flag).
- The **VM identifier** (which team VM should host the challenge).
- The deployment metadata (exposed port, healthcheck path, etc.) in `upload_metadata`.

## Automated validation service (admin/CTF VM)

The **validation service** runs on the admin/CTF VM and uses the same database as the backend. It can be triggered via:

- `POST /api/admin/challenges/validate`

This endpoint:

- Reads each challenge’s `vm_identifier` and `upload_metadata` (including `exposed_port` and optional `healthcheck_path`).
- Performs simple HTTP healthchecks to the corresponding team VM (e.g. `http://<vm_identifier>:<exposed_port>/<healthcheck_path>`).
- Updates `upload_metadata` with `last_validation_status`, `last_validation_error`, and `last_checked_at`.
- Returns a list of validation results, which the **Admin → VM** page displays in the frontend.

## Frontend → backend link

When you run the React frontend, set the API base URL to the backend, e.g.:

- **Development:** `VITE_API_URL=http://localhost:8000` or `REACT_APP_API_URL=http://localhost:8000` (depending on Vite/CRA) in the frontend `.env`, so the app calls `http://localhost:8000/api/...`.

## Quick reference – API base URL

- **Backend API base (for frontend / Postman):** `http://localhost:8000`  
- **Auth:** `POST http://localhost:8000/api/auth/register` and `POST http://localhost:8000/api/auth/login`  
- **Challenges:** `GET http://localhost:8000/api/challenges`  
- **Leaderboard:** `GET http://localhost:8000/api/leaderboard`  
- **Submit flag:** `POST http://localhost:8000/api/submissions` (requires `Authorization: Bearer <token>`)
