import pytest
from fastapi.testclient import TestClient

from test.factories import UserFactory, ChallengeFactory, HintFactory


def test_list_challenges_returns_created_challenges(client: TestClient):
    c1 = ChallengeFactory.create(name="Web 1", category="web", points=100)
    c2 = ChallengeFactory.create(name="Crypto 1", category="crypto", points=200)
    resp = client.get("/api/challenges")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    names = [x["name"] for x in data]
    assert "Web 1" in names
    assert "Crypto 1" in names


def test_get_challenge_by_id(client: TestClient):
    ch = ChallengeFactory.create(name="Single", description="Desc", points=50)
    resp = client.get(f"/api/challenges/{ch.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Single"
    assert data["description"] == "Desc"
    assert data["points"] == 50


def test_get_challenge_not_found(client: TestClient):
    resp = client.get("/api/challenges/99999")
    assert resp.status_code == 404


def test_challenge_includes_hints_when_present(client: TestClient):
    ch = ChallengeFactory.create()
    HintFactory.create(challenge=ch, order=0, content="First hint", cost=5)
    HintFactory.create(challenge=ch, order=1, content="Second hint", cost=10)
    resp = client.get(f"/api/challenges/{ch.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "hints" in data
    assert len(data["hints"]) == 2
    assert data["hints"][0]["content"] == "First hint"
    assert data["hints"][0]["cost"] == 5
