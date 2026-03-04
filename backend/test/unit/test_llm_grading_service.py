import json

from ctf.models import Challenge, Submission, User
from ctf.services import llm_grading


class DummyRespChoice:
    def __init__(self, content: str):
        self.message = type("msg", (), {"content": content})


class DummyResp:
    def __init__(self, payload: dict):
        self.choices = [DummyRespChoice(json.dumps(payload))]


def test_grade_submission_with_llm_parses_json(monkeypatch):
    challenge = Challenge(id=1, name="Test", category="web", difficulty="easy", points=100)
    submission = Submission(
        id=1,
        challenge_id=1,
        user_id=1,
        team_id=None,
        submitted_flag="FLAG{test}",
        description="I exploited the XSS and stole the cookie.",
    )
    user = User(id=1, username="alice")

    def fake_client_create(*args, **kwargs):
        payload = {
            "correct": True,
            "score": 90,
            "reasoning_summary": "Looks good.",
            "student_feedback": "Well done.",
            "ta_notes": "Low suspicion.",
            "alignment_checks": {
                "flag_match": "match",
                "steps_align_with_official": "strong",
                "upload_consistency": "consistent",
                "suspicion_of_plagiarism_or_guessing": "low",
            },
            "auto_grade_safe": True,
        }
        return DummyResp(payload)

    class DummyClient:
        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    return fake_client_create()

    monkeypatch.setattr(llm_grading, "_build_client", lambda: DummyClient())

    result = llm_grading.grade_submission_with_llm(
        challenge=challenge,
        submission=submission,
        user=user,
        official_solution_summary="Official solution here.",
        deployment_metadata={},
        flag_match=True,
    )

    assert result["correct"] is True
    assert result["score"] == 90
    assert result["alignment_checks"]["flag_match"] == "match"

