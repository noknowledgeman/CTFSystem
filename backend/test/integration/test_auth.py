import pytest
from fastapi.testclient import TestClient

from test.factories import UserFactory


def test_register_creates_user(client: TestClient, db_session):
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@test.ctf.local",
            "password": "secure123",
            "team_id": None,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "newuser@test.ctf.local"
    assert data["user"]["role"] == "player"
    assert "access_token" in data
    assert len(data["access_token"]) > 0
    # Real DB: user should exist
    from ctf.models import User
    user = db_session.query(User).filter(User.username == "newuser").first()
    assert user is not None
    assert user.email == "newuser@test.ctf.local"


def test_register_duplicate_username_returns_400(client: TestClient):
    UserFactory.create(username="alice", email="alice@test.ctf.local")
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "other@test.ctf.local",
            "password": "pass",
            "team_id": None,
        },
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_duplicate_email_returns_400(client: TestClient):
    UserFactory.create(username="bob", email="bob@test.ctf.local")
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "other",
            "email": "bob@test.ctf.local",
            "password": "pass",
            "team_id": None,
        },
    )
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_login_success_returns_token(client: TestClient):
    user = UserFactory.create(username="player1", email="p1@test.ctf.local")
    # password was set by factory as "password123"
    resp = client.post(
        "/api/auth/login",
        json={"username": "player1", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["username"] == "player1"
    assert data["user"]["id"] == user.id
    assert "access_token" in data


def test_login_wrong_password_returns_401(client: TestClient):
    UserFactory.create(username="player1", email="p1@test.ctf.local")
    resp = client.post(
        "/api/auth/login",
        json={"username": "player1", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user_returns_401(client: TestClient):
    resp = client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "any"},
    )
    assert resp.status_code == 401


def test_login_disabled_user_returns_403(client: TestClient):
    UserFactory.create(username="disabled", email="d@test.ctf.local", is_active=False)
    resp = client.post(
        "/api/auth/login",
        json={"username": "disabled", "password": "password123"},
    )
    assert resp.status_code == 403
