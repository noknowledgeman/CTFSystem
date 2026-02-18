import pytest
from fastapi.testclient import TestClient

from ctf.models import HintUnlock
from test.factories import UserFactory, ChallengeFactory, HintFactory


def test_unlock_hint_creates_hint_unlock(client: TestClient, auth_headers, db_session):
    user = UserFactory.create(username="player")
    ch = ChallengeFactory.create()
    HintFactory.create(challenge=ch, order=0, cost=10)
    resp = client.post(
        f"/api/hints/challenge/{ch.id}/unlock",
        headers=auth_headers(user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["challenge_id"] == ch.id
    assert data["cost"] == 10
    # Real DB
    unlock = db_session.query(HintUnlock).filter(
        HintUnlock.user_id == user.id,
    ).first()
    assert unlock is not None


def test_unlock_next_hint_returns_second_then_400(client: TestClient, auth_headers):
    user = UserFactory.create(username="player")
    ch = ChallengeFactory.create()
    HintFactory.create(challenge=ch, order=0, cost=5)
    HintFactory.create(challenge=ch, order=1, cost=10)
    resp1 = client.post(
        f"/api/hints/challenge/{ch.id}/unlock",
        headers=auth_headers(user),
    )
    assert resp1.status_code == 200
    assert resp1.json()["cost"] == 5
    resp2 = client.post(
        f"/api/hints/challenge/{ch.id}/unlock",
        headers=auth_headers(user),
    )
    assert resp2.status_code == 200
    assert resp2.json()["cost"] == 10
    resp3 = client.post(
        f"/api/hints/challenge/{ch.id}/unlock",
        headers=auth_headers(user),
    )
    assert resp3.status_code == 400  # No more hints
