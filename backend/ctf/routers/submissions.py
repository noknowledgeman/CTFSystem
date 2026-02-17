from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Challenge, Submission, User, HintUnlock, Hint
from ctf.schemas import SubmissionCreate, SubmissionRead, SubmissionGradeUpdate
from ctf.auth_utils import verify_password
from ctf.dependencies import get_current_user, require_admin
from sqlalchemy import func

router = APIRouter()


def _hint_cost_for_challenge(db, user_id: int | None, team_id: int | None, challenge_id: int) -> int:
    q = db.query(HintUnlock.hint_id).join(Hint, HintUnlock.hint_id == Hint.id).filter(Hint.challenge_id == challenge_id)
    if team_id:
        q = q.filter(HintUnlock.team_id == team_id)
    else:
        q = q.filter(HintUnlock.user_id == user_id)
    unlocked_ids = [r[0] for r in q.distinct().all()]
    if not unlocked_ids:
        return 0
    total = db.query(func.coalesce(func.sum(Hint.cost), 0)).filter(Hint.id.in_(unlocked_ids)).scalar()
    return int(total or 0)


@router.post("", response_model=SubmissionRead, status_code=201)
def submit_flag(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    challenge = db.query(Challenge).filter(Challenge.id == data.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Check already solved (user or team)
    if current_user.team_id:
        already = (
            db.query(Submission)
            .filter(
                Submission.challenge_id == data.challenge_id,
                Submission.team_id == current_user.team_id,
                Submission.correct == True,
            )
            .first()
        )
    else:
        already = (
            db.query(Submission)
            .filter(
                Submission.challenge_id == data.challenge_id,
                Submission.user_id == current_user.id,
                Submission.correct == True,
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
    else:
        # Manual grading: store and leave pending
        sub = Submission(
            user_id=current_user.id if not current_user.team_id else None,
            team_id=current_user.team_id,
            challenge_id=data.challenge_id,
            submitted_flag=data.flag,
            description=data.description,
            correct=False,
            status="pending",
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub


@router.get("", response_model=List[SubmissionRead])
def my_submissions(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    if current_user.team_id:
        subs = (
            db.query(Submission)
            .filter(Submission.team_id == current_user.team_id)
            .order_by(Submission.created_at.desc())
            .all()
        )
    else:
        subs = (
            db.query(Submission)
            .filter(Submission.user_id == current_user.id)
            .order_by(Submission.created_at.desc())
            .all()
        )
    return subs


# ----- Admin -----
@router.get("/all", response_model=List[SubmissionRead])
def list_all_submissions(
    challenge_id: int | None = Query(None),
    user_id: int | None = Query(None),
    team_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    q = db.query(Submission)
    if challenge_id is not None:
        q = q.filter(Submission.challenge_id == challenge_id)
    if user_id is not None:
        q = q.filter(Submission.user_id == user_id)
    if team_id is not None:
        q = q.filter(Submission.team_id == team_id)
    subs = q.order_by(Submission.created_at.desc()).all()
    return subs


@router.patch("/{submission_id}", response_model=SubmissionRead)
def grade_submission(
    submission_id: int,
    data: SubmissionGradeUpdate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.status = data.status
    if data.assigned_points is not None:
        sub.assigned_points = data.assigned_points
    if data.feedback is not None:
        sub.feedback = data.feedback
    sub.correct = data.status == "accepted"
    db.commit()
    db.refresh(sub)
    return sub
