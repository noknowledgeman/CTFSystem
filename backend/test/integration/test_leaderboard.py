import pytest
from fastapi.testclient import TestClient

from test.factories import (
    UserFactory,
    TeamFactory,
    ChallengeFactory,
    SubmissionFactory,
)


def test_leaderboard_users_reflects_real_submissions(client: TestClient):
    u1 = UserFactory.create(username="alice")
    u2 = UserFactory.create(username="bob")
    ch = ChallengeFactory.create(points=100)
    SubmissionFactory.create(
        user_id=u1.id, team_id=None, challenge=ch,
        correct=True, assigned_points=100,
    )
    SubmissionFactory.create(
        user_id=u2.id, team_id=None, challenge=ch,
        correct=True, assigned_points=50,
    )
    resp = client.get("/api/leaderboard?by=user")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    by_name = {x["username_or_team"]: x["total_points"] for x in data}
    assert by_name.get("alice") == 100
    assert by_name.get("bob") == 50


def test_leaderboard_teams_reflects_team_submissions(client: TestClient):
    team = TeamFactory.create(name="Winners")
    UserFactory.create(username="m1", team_id=team.id)
    ch = ChallengeFactory.create(points=200)
    SubmissionFactory.create(
        user_id=None, team_id=team.id, challenge=ch,
        correct=True, assigned_points=200,
    )
    resp = client.get("/api/leaderboard?by=team")
    assert resp.status_code == 200
    data = resp.json()
    names = [x["username_or_team"] for x in data]
    assert "Winners" in names


def test_leaderboard_me_detailed_requires_auth(client: TestClient):
    resp = client.get("/api/leaderboard/me/detailed")
    assert resp.status_code == 401
