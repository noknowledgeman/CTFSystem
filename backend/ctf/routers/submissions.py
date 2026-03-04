from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Submission, User
from ctf.schemas import SubmissionCreate, SubmissionRead, SubmissionGradeUpdate
from ctf.dependencies import get_current_user, require_admin
from ctf.services.submissions import (
    apply_manual_grade,
    create_submission_for_player,
    grade_submission_llm,
)

router = APIRouter()


@router.post("", response_model=SubmissionRead, status_code=201)
def submit_flag(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    try:
        return create_submission_for_player(db=db, current_user=current_user, data=data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
    apply_manual_grade(
        sub,
        status=data.status,
        assigned_points=data.assigned_points,
        feedback=data.feedback,
    )
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/{submission_id}/grade-llm", response_model=SubmissionRead)
def grade_submission_with_llm_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    """
    Trigger LLM-based grading for a pending submission.

    This endpoint is intended for use from the admin/CTF VM only.
    """
    try:
        sub = grade_submission_llm(db=db, submission_id=submission_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        # Typically misconfiguration of OPENAI_API_KEY / model.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return sub
