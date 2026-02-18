import pytest
from fastapi.testclient import TestClient

from test.factories import UserFactory, TeamFactory


def test_list_teams_returns_created_teams(client: TestClient):
    TeamFactory.create(name="Alpha")
    TeamFactory.create(name="Beta")
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    data = resp.json()
    names = [x["name"] for x in data]
    assert "Alpha" in names
    assert "Beta" in names


def test_join_team_updates_user(client: TestClient, auth_headers, db_session):
    user = UserFactory.create(username="joiner", team_id=None)
    team = TeamFactory.create(name="JoinMe")
    resp = client.post(
        f"/api/teams/{team.id}/join",
        headers=auth_headers(user),
    )
    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.team_id == team.id


def test_leave_team_clears_team_id(client: TestClient, auth_headers, db_session):
    team = TeamFactory.create(name="Leavable")
    user = UserFactory.create(username="leaver", team_id=team.id)
    resp = client.post("/api/teams/leave", headers=auth_headers(user))
    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.team_id is None
