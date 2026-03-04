import os

# Force in-memory DB for tests *before* any app/database import.
# Otherwise with pytest-xdist (e.g. -n 12) multiple workers all run init_db()
# against the same ctf.db file and hang on SQLite locks.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from ctf.database import Base, get_db
from main import app


def _clear_tables(session):
    """Delete all rows so each test starts with a clean DB."""
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


@pytest.fixture(scope="function")
def test_engine():
    """Fresh in-memory engine per test for isolation."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """DB session for the test. Tables are cleared at start so each test has a clean DB."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    _clear_tables(session)
    yield session
    session.rollback()
    session.close()


def _get_db_override(session):
    """Yield the test session so API and factories share the same DB state."""
    try:
        yield session
    finally:
        pass  # don't close; fixture handles it


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client. get_db is overridden to use the same session as factories."""

    def override_get_db():
        # FastAPI expects a dependency that YIELDS the session, not a plain generator
        # object. This wrapper ensures `db_session` itself is yielded correctly.
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function", autouse=True)
def set_factory_session(db_session):
    """Inject the test DB session into all factories so they use real models."""
    from test.factories import (  # noqa: F401
        UserFactory,
        TeamFactory,
        ChallengeFactory,
        HintFactory,
        HintUnlockFactory,
        SubmissionFactory,
    )
    for factory in (
        UserFactory,
        TeamFactory,
        ChallengeFactory,
        HintFactory,
        HintUnlockFactory,
        SubmissionFactory,
    ):
        factory._meta.sqlalchemy_session = db_session
    yield
    for factory in (
        UserFactory,
        TeamFactory,
        ChallengeFactory,
        HintFactory,
        HintUnlockFactory,
        SubmissionFactory,
    ):
        factory._meta.sqlalchemy_session = None


@pytest.fixture
def auth_headers(db_session):
    """Return a callable that gives Bearer token headers for a User model."""
    from ctf.auth_utils import create_access_token

    def _headers(user):
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}
    return _headers
