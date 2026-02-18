import pytest
from fastapi.testclient import TestClient

from ctf.auth_utils import hash_password
from ctf.models import Challenge, Hint, HintUnlock, Submission
from test.factories import (
    UserFactory,
    TeamFactory,
    ChallengeFactory,
    HintFactory,
    HintUnlockFactory,
    SubmissionFactory,
)


def test_submit_correct_flag_gets_points(client: TestClient, auth_headers, db_session):
    user = UserFactory.create(username="solver", role="player")
    # Challenge with known flag
    flag = "flag{correct}"
    ch = ChallengeFactory.create(
        name="Easy",
        points=100,
        flag_hash=hash_password(flag),
        grading_mode="auto",
    )
    resp = client.post(
        "/api/submissions",
        json={"challenge_id": ch.id, "flag": flag},
        headers=auth_headers(user),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] is True
    assert data["status"] == "accepted"
    assert data["assigned_points"] == 100
    # Real DB check
    sub = db_session.query(Submission).filter(
        Submission.challenge_id == ch.id,
        Submission.user_id == user.id,
    ).first()
    assert sub is not None
    assert sub.correct is True
    assert sub.assigned_points == 100


def test_submit_wrong_flag_rejected(client: TestClient, auth_headers):
    user = UserFactory.create(username="solver")
    ch = ChallengeFactory.create(points=100, grading_mode="auto")
    resp = client.post(
        "/api/submissions",
        json={"challenge_id": ch.id, "flag": "flag{wrong}"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] is False
    assert data["status"] == "rejected"
    assert data["assigned_points"] == 0


def test_submit_with_hints_deducts_cost(client: TestClient, auth_headers, db_session):
    user = UserFactory.create(username="solver")
    flag = "flag{hinted}"
    ch = ChallengeFactory.create(
        points=100,
        flag_hash=hash_password(flag),
        grading_mode="auto",
    )
    h1 = HintFactory.create(challenge=ch, cost=10)
    h2 = HintFactory.create(challenge=ch, cost=15)
    HintUnlockFactory.create(hint=h1, user_id=user.id, team_id=None)
    HintUnlockFactory.create(hint=h2, user_id=user.id, team_id=None)
    resp = client.post(
        "/api/submissions",
        json={"challenge_id": ch.id, "flag": flag},
        headers=auth_headers(user),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] is True
    # 100 - 10 - 15 = 75
    assert data["assigned_points"] == 75


def test_submit_team_solved_uses_team_hint_cost(client: TestClient, auth_headers, db_session):
    team = TeamFactory.create(name="TeamA")
    user = UserFactory.create(username="member", team_id=team.id)
    flag = "flag{team}"
    ch = ChallengeFactory.create(
        points=100,
        flag_hash=hash_password(flag),
        grading_mode="auto",
    )
    h = HintFactory.create(challenge=ch, cost=20)
    HintUnlockFactory.create(hint=h, user_id=None, team_id=team.id)
    resp = client.post(
        "/api/submissions",
        json={"challenge_id": ch.id, "flag": flag},
        headers=auth_headers(user),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] is True
    assert data["assigned_points"] == 80  # 100 - 20


def test_my_submissions_returns_only_current_user(client: TestClient, auth_headers):
    u1 = UserFactory.create(username="u1")
    u2 = UserFactory.create(username="u2")
    ch = ChallengeFactory.create()
    SubmissionFactory.create(user_id=u1.id, team_id=None, challenge=ch, correct=True)
    SubmissionFactory.create(user_id=u2.id, team_id=None, challenge=ch, correct=False)
    resp = client.get("/api/submissions", headers=auth_headers(u1))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["user_id"] == u1.id


def test_unauthenticated_submit_returns_401(client: TestClient):
    ch = ChallengeFactory.create()
    resp = client.post(
        "/api/submissions",
        json={"challenge_id": ch.id, "flag": "flag{x}"},
    )
    assert resp.status_code == 401
