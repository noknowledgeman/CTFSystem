from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from ctf.database import init_db
from ctf.routers import auth, challenges, hints, submissions, leaderboard, admin, health, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CTF System API",
    description="Capture the Flag submission and grading system",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# I can fix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
app.include_router(hints.router, prefix="/api/hints", tags=["hints"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(health.router, prefix="/api/health", tags=["health"])


@app.get("/")
def root():
    return {"message": "CTF System API", "docs": "/docs", "swagger": "/docs"}


@app.get("/swagger", include_in_schema=False)
def swagger_redirect():
    """Redirect /swagger to Swagger UI at /docs."""
    return RedirectResponse(url="/docs")
