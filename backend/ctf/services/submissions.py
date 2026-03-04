from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ctf.auth_utils import verify_password
from ctf.models import Challenge, Hint, HintUnlock, Submission, User
from ctf.services.llm_grading import grade_submission_with_llm


def _hint_cost_for_challenge(
    db: Session,
    user_id: int | None,
    team_id: int | None,
    challenge_id: int,
) -> int:
    q = (
        db.query(HintUnlock.hint_id)
        .join(Hint, HintUnlock.hint_id == Hint.id)
        .filter(Hint.challenge_id == challenge_id)
    )
    if team_id:
        q = q.filter(HintUnlock.team_id == team_id)
    else:
        q = q.filter(HintUnlock.user_id == user_id)
    unlocked_ids = [r[0] for r in q.distinct().all()]
    if not unlocked_ids:
        return 0
    total = db.query(func.coalesce(func.sum(Hint.cost), 0)).filter(Hint.id.in_(unlocked_ids)).scalar()
    return int(total or 0)


def create_submission_for_player(
    db: Session,
    current_user: User,
    data,
) -> Submission:
    """
    Handle a new submission from a player, respecting the challenge grading_mode:
    - auto: immediate flag verification and scoring
    - manual: store pending for human grading
    - llm: store pending, with optional pre-computed flag_match for later LLM grading
    """
    challenge = db.query(Challenge).filter(Challenge.id == data.challenge_id).first()
    if not challenge:
        raise ValueError("Challenge not found")

    # Check already solved (user or team)
    if current_user.team_id:
        already = (
            db.query(Submission)
            .filter(
                Submission.challenge_id == data.challenge_id,
                Submission.team_id == current_user.team_id,
                Submission.correct == True,  # noqa: E712
            )
            .first()
        )
    else:
        already = (
            db.query(Submission)
            .filter(
                Submission.challenge_id == data.challenge_id,
                Submission.user_id == current_user.id,
                Submission.correct == True,  # noqa: E712
            )
            .first()
        )
    if already:
        return already

    if challenge.grading_mode == "auto":
        correct = verify_password(data.flag, challenge.flag_hash)
        hint_deduction = _hint_cost_for_challenge(
            db,
            current_user.id if not current_user.team_id else None,
            current_user.team_id,
            data.challenge_id,
        )
        points = max(0, challenge.points - hint_deduction) if correct else 0
        sub = Submission(
            user_id=current_user.id if not current_user.team_id else None,
            team_id=current_user.team_id,
            challenge_id=data.challenge_id,
            submitted_flag=data.flag,
            description=data.description,
            correct=correct,
            status="accepted" if correct else "rejected",
            assigned_points=points,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    # Manual or LLM-based grading: store as pending for later review / LLM call
    correct_initial = False
    if challenge.grading_mode == "llm":
        # Pre-compute whether the flag matches; this is passed as context to the LLM later.
        correct_initial = verify_password(data.flag, challenge.flag_hash)

    sub = Submission(
        user_id=current_user.id if not current_user.team_id else None,
        team_id=current_user.team_id,
        challenge_id=data.challenge_id,
        submitted_flag=data.flag,
        description=data.description,
        correct=correct_initial,
        status="pending",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def apply_manual_grade(sub: Submission, status: str, assigned_points: int | None, feedback: str | None) -> None:
    sub.status = status
    if assigned_points is not None:
        sub.assigned_points = assigned_points
    if feedback is not None:
        sub.feedback = feedback
    sub.correct = status == "accepted"


def grade_submission_llm(
    db: Session,
    submission_id: int,
) -> Submission:
    """
    Run LLM-based grading for a pending submission.

    This:
    - fetches the submission and its challenge
    - builds metadata from upload_metadata
    - calls the OpenAI-based grading service
    - writes back assigned_points, feedback, status, and correct flag
    """
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise ValueError("Submission not found")
    challenge = db.query(Challenge).filter(Challenge.id == sub.challenge_id).first()
    if not challenge:
        raise ValueError("Challenge not found")

    # LLM grading is only meaningful for challenges explicitly configured for it.
    if challenge.grading_mode not in {"llm", "manual"}:
        # Allow calling it for manual challenges as an assistant tool, but reject auto.
        if challenge.grading_mode == "auto":
            raise ValueError("LLM grading is not enabled for auto-graded challenges")

    user = db.query(User).filter(User.id == sub.user_id).first() if sub.user_id else None

    metadata: dict[str, Any] = {}
    if challenge.upload_metadata:
        try:
            parsed = json.loads(challenge.upload_metadata)
            if isinstance(parsed, dict):
                metadata = parsed
        except json.JSONDecodeError:
            metadata = {}

    flag_match = sub.correct if sub.status == "pending" else None

    llm_result = grade_submission_with_llm(
        challenge=challenge,
        submission=sub,
        user=user,
        official_solution_summary=metadata.get("official_solution_summary"),
        deployment_metadata=metadata,
        flag_match=flag_match,
    )

    score = int(llm_result.get("score", 0) or 0)
    score = max(0, min(score, challenge.points))
    correct = bool(llm_result.get("correct", False))
    student_feedback = llm_result.get("student_feedback") or ""
    ta_notes = llm_result.get("ta_notes") or ""

    sub.assigned_points = score
    sub.correct = correct
    sub.status = "accepted" if correct else "rejected"

    # Combine feedback and TA notes into the existing feedback field for now.
    combined_feedback_parts = []
    if student_feedback:
        combined_feedback_parts.append(student_feedback)
    if ta_notes:
        combined_feedback_parts.append(f"\n\n[Notes for TA]\n{ta_notes}")
    if combined_feedback_parts:
        sub.feedback = "".join(combined_feedback_parts)

    db.commit()
    db.refresh(sub)
    return sub

