from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# SQLite needs check_same_thread=False for FastAPI
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401 - register models with Base
    Base.metadata.create_all(bind=engine)
    # Add is_active to users if missing (existing DBs)
    with engine.connect() as conn:
        try:
            r = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            cols = [row[1] for row in r]
            if "is_active" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
        except Exception:
            pass
    # Create default admin if no admin exists
    from .models import User
    from .auth_utils import hash_password
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").first() is None:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password(settings.default_admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
