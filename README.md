# TODOS

- Handle https
- Handle env
- Do unit testing
- DO some wider system testing
- Integration Testing with Mohsen
- Write documentation
- Handle CORS

# CTFSystem

Capture the Flag system for the RUG Honours Deepening project: automatic flag submission, hints, and grading (including optional description-based grading).

## Setup and links

**Database setup and all URLs:** **[SETUP_AND_LINKS.md](SETUP_AND_LINKS.md)**

- **API (local):** http://localhost:8000  
- **Swagger UI (API docs):** http://localhost:8000/docs — also at http://localhost:8000/swagger  
- **Database:** `backend/ctf.db` (SQLite), created by `python scripts/init_db.py`  
- **Default admin:** username `admin`, password from `backend/.env` (default `admin`)

In the **course deployment**, the backend and frontend run on an **admin/CTF VM** inside the same virtualised environment as the student team VMs:

- Each student **team VM** hosts one or more Docker-based challenges.
- The **admin/CTF VM** runs CTFSystem (backend + frontend) and the automated validation scripts.
- Students access the web UI from within the university network / VPN to view challenges, submit flags, and see the leaderboard.

## Backend

- Python, FastAPI, OpenAPI, SQLite
- Run: `cd backend && uvicorn main:app --reload --port 8000`

## Who can use the platform

**Players (students/participants)** use the same frontend to:
- **Register** and **log in**
- View the **dashboard**: live leaderboard and list of challenges
- Open a **challenge**: read description, **submit flags**, and **unlock hints**
- See their **progress** (points and solved count)

**Admins** (organisers) log in with an admin account and get an extra **Admin** section to:

- Manage challenges (including VM identifiers and grading mode).
- Grade manual submissions and view stats.
- Upload VM configs and trigger automated **deployment validation** for challenges.

### Brightspace and automated validation

The intended workflow for self-designed challenges is:

1. **Students submit** their challenge in Brightspace as a ZIP containing Docker files, metadata (`challenge.yaml`), a write-up, and the flag.
2. A helper step converts that ZIP into `ChallengeSubmissionMetadata` JSON.
3. The admin/CTF VM calls `POST /api/admin/challenges/ingest` to register the challenge, its VM identifier, and deployment metadata.
4. From the **Admin → VM** page, organisers can call `POST /api/admin/challenges/validate` (via the UI) to run healthchecks against each team VM and see which challenges are correctly deployed and reachable.

## Mock data (see how it looks)

To populate the app with sample challenges, hints, and demo players (so the leaderboard and challenge list look real):

```bash
cd CTFSystem/backend
# Activate your Python virtual environment, then:
PYTHONPATH=. python scripts/seed_mock_data.py
```

This adds:
- **5 challenges** (warmup, web, crypto, forensics) with descriptions and hints
- **3 demo players:** `alice` / `bob` / `charlie` with passwords `player1` / `player2` / `player3`
- **Sample submissions** so the leaderboard shows scores

Then open http://localhost:5173: you’ll see the leaderboard and challenges. Log in as `alice` (password `player1`) to try submitting flags and viewing hints.

## Frontend

- React (Vite + TypeScript) in `frontend/`
- **Run:** `cd frontend && npm install && npm run dev` → http://localhost:5173
- Player: Dashboard (leaderboard, challenges), challenge detail (submit flag, hints), login/register
- Admin: Stats, challenges CRUD, submissions grading, VM config upload (login as `admin` to see Admin link)