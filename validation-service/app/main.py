from pathlib import Path

from fastapi import FastAPI

from app.config import get_settings
from app.db.database import Base, engine
from app.db import models as db_models  # noqa: F401
from app.routers import admin, submissions, validation


def create_app() -> FastAPI:
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.extract_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="CTF Validation Service", version="1.0.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(submissions.router)
    app.include_router(validation.router)
    app.include_router(admin.router)
    return app


app = create_app()
