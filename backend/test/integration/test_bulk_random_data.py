from random import choice, randint

from fastapi.testclient import TestClient

from ctf.models import Submission
from test.factories import ChallengeFactory, TeamFactory, UserFactory


def test_bulk_random_challenges_and_submissions(client: TestClient, auth_headers, db_session):
  """Smoke-test: many challenges, users, and submissions across grading modes.

  This exercises the full submissions/leaderboard path with ~30–40 challenges
  and randomised data to ensure the system remains robust.
  """
  # Create a few teams and users (some with teams, some solo)
  teams = [TeamFactory.create() for _ in range(3)]
  team_ids = [t.id for t in teams]
  users = [
    UserFactory.create(team_id=choice([None] + team_ids))
    for _ in range(12)
  ]

  # Create 35 challenges with mixed grading modes
  modes = ["auto", "manual", "llm"]
  challenges = [
    ChallengeFactory.create(points=randint(50, 500), grading_mode=choice(modes))
    for _ in range(35)
  ]

  # Have users submit flags/solutions to random challenges
  for user in users:
    for ch in challenges:
      # Roughly 1 in 4 chance that a user submits to a given challenge
      if randint(0, 3) == 0:
        payload = {
          "challenge_id": ch.id,
          "flag": "flag{test}",  # matches default factory flag_hash for auto-graded
          "description": "Automated test submission exercising grading.",
        }
        resp = client.post("/api/submissions", json=payload, headers=auth_headers(user))
        # Even if a specific grading_mode path changes later, the endpoint should not 500
        assert resp.status_code == 201

  # Ensure challenge listing and leaderboard endpoints still behave as expected
  resp_ch = client.get("/api/challenges")
  assert resp_ch.status_code == 200
  assert isinstance(resp_ch.json(), list)

  resp_lb_user = client.get("/api/leaderboard?by=user")
  assert resp_lb_user.status_code == 200

  resp_lb_team = client.get("/api/leaderboard?by=team")
  assert resp_lb_team.status_code == 200

  # Check we actually stored a substantial number of submissions
  assert db_session.query(Submission).count() >= 30

