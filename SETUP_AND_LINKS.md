# CTF System – Setup and Links

## Environment

Use a Python 3.11+ virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # or on Windows: venv\Scripts\activate
cd CTFSystem/backend
pip install -r requirements.txt
```

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

## Links (local development)

| What | URL |
|------|-----|
| **API root** | http://localhost:8000 |
| **OpenAPI (Swagger) docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health check** | http://localhost:8000/api/health |

## Default admin login

- **Username:** `admin`  
- **Password:** value of `DEFAULT_ADMIN_PASSWORD` in `.env` (default: `admin`)

Use **POST /api/auth/login** with `{"username": "admin", "password": "admin"}` to get a JWT for the admin UI.

## Frontend → backend link

When you run the React frontend, set the API base URL to the backend, e.g.:

- **Development:** `VITE_API_URL=http://localhost:8000` or `REACT_APP_API_URL=http://localhost:8000` (depending on Vite/CRA) in the frontend `.env`, so the app calls `http://localhost:8000/api/...`.

## Quick reference – API base URL

- **Backend API base (for frontend / Postman):** `http://localhost:8000`  
- **Auth:** `POST http://localhost:8000/api/auth/register` and `POST http://localhost:8000/api/auth/login`  
- **Challenges:** `GET http://localhost:8000/api/challenges`  
- **Leaderboard:** `GET http://localhost:8000/api/leaderboard`  
- **Submit flag:** `POST http://localhost:8000/api/submissions` (requires `Authorization: Bearer <token>`)
