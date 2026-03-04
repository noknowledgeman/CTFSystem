from __future__ import annotations

import json
from typing import Any, Dict

from ctf.config import settings
from ctf.models import Challenge, Submission, User


def _build_client() -> OpenAI:
    # Local import to avoid requiring openai at module import time (e.g. during tests
    # or deployments that do not use LLM-based grading).
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:  # pragma: no cover - configuration/runtime issue
        raise RuntimeError(
            "openai package is not installed, but LLM-based grading was requested. "
            "Install the 'openai' dependency and configure OPENAI_API_KEY."
        ) from exc

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured for LLM-based grading.")
    return OpenAI(api_key=settings.openai_api_key)


def _build_system_prompt() -> str:
    return (
        "You are an expert Capture-the-Flag (CTF) grader and teaching assistant for a university "
        "Ethical Hacking course. You grade a single challenge submission at a time and respond "
        "ONLY with a single JSON object matching the schema provided in the user message."
    )


def _build_user_prompt(
    challenge: Challenge,
    submission: Submission,
    user: User | None,
    official_solution_summary: str | None,
    deployment_metadata: dict[str, Any] | None,
    flag_match: bool | None,
) -> str:
    metadata_pretty = json.dumps(deployment_metadata or {}, indent=2, sort_keys=True)
    username = getattr(user, "username", None) if user else None

    return f"""
You are grading a single CTF challenge submission.

=== CHALLENGE CONTEXT ===
Challenge ID: {challenge.id}
Name: {challenge.name}
Category: {challenge.category}
Difficulty: {challenge.difficulty}
Max points: {challenge.points}

Expected flag correctness (from backend verification):
- flag_match_boolean: {flag_match}

Official solution summary (may be shortened):
\"\"\"{official_solution_summary or ""}\"\"\"

Key deployment details (from challenge.yaml / upload_metadata):
{metadata_pretty}

=== STUDENT SUBMISSION ===
Submitting user / team:
- User ID: {submission.user_id}
- Team ID: {submission.team_id}
- Username: {username}

Submitted flag (may be empty for description-only grading):
{submission.submitted_flag}

Student's description of how they solved the challenge:
\"\"\"{submission.description or ""}\"\"\"

=== GRADING INSTRUCTIONS (SUMMARY) ===

- Consider both technical correctness and depth of explanation.
- Use the backend-provided flag_match_boolean for whether the flag was correct.
- Check whether the described steps are consistent with the official solution and metadata.
- Provide:
  - correct: boolean
  - score: number between 0 and {challenge.points}
  - reasoning_summary: 2–5 sentences explaining your judgment
  - student_feedback: 1–2 short paragraphs of constructive feedback
  - ta_notes: a short note for teaching staff (suspicion, issues, or suggestions)
  - alignment_checks: {{ flag_match, steps_align_with_official, upload_consistency, suspicion_of_plagiarism_or_guessing }}
  - auto_grade_safe: boolean indicating whether this can be accepted without human review.

Respond ONLY with a JSON object and nothing else.
"""  # noqa: E501


def grade_submission_with_llm(
    challenge: Challenge,
    submission: Submission,
    user: User | None,
    official_solution_summary: str | None = None,
    deployment_metadata: dict[str, Any] | None = None,
    flag_match: bool | None = None,
) -> Dict[str, Any]:
    """
    Call the OpenAI API to obtain a structured grading result for a submission.

    The caller is responsible for persisting the returned grading outcome onto the
    Submission record (assigned_points, feedback, status, etc.).
    """
    client = _build_client()
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        challenge=challenge,
        submission=submission,
        user=user,
        official_solution_summary=official_solution_summary,
        deployment_metadata=deployment_metadata,
        flag_match=flag_match,
    )

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content or ""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"LLM returned non-JSON content: {content!r}") from exc

    return data

