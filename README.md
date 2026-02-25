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
- **Docs (Swagger):** http://localhost:8000/docs  
- **Database:** `backend/ctf.db` (SQLite), created by `python scripts/init_db.py`  
- **Default admin:** username `admin`, password from `backend/.env` (default `admin`)

## Backend

- Python, FastAPI, OpenAPI, SQLite
- Run: `cd backend && uvicorn main:app --reload --port 8000`

## Who can use the platform

**Players (students/participants)** use the same frontend to:
- **Register** and **log in**
- View the **dashboard**: live leaderboard and list of challenges
- Open a **challenge**: read description, **submit flags**, and **unlock hints**
- See their **progress** (points and solved count)

**Admins** (organisers) log in with an admin account and get an extra **Admin** section to manage challenges, grade manual submissions, view stats, and upload VM configs.

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