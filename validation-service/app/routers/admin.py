from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.models import SubmissionRecord, SubmissionStatus, ValidationRunRecord
from app.services.validator import ValidationOrchestrator

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    submissions_total = db.scalar(select(func.count(SubmissionRecord.id))) or 0
    runs_total = db.scalar(select(func.count(ValidationRunRecord.id))) or 0
    valid_total = db.scalar(
        select(func.count(SubmissionRecord.id)).where(SubmissionRecord.status == SubmissionStatus.VALID)
    ) or 0
    needs_review_total = db.scalar(
        select(func.count(SubmissionRecord.id)).where(SubmissionRecord.status == SubmissionStatus.NEEDS_REVIEW)
    ) or 0
    invalid_total = db.scalar(
        select(func.count(SubmissionRecord.id)).where(SubmissionRecord.status == SubmissionStatus.INVALID)
    ) or 0
    error_total = db.scalar(
        select(func.count(SubmissionRecord.id)).where(SubmissionRecord.status == SubmissionStatus.ERROR)
    ) or 0
    return {
        "submissions_total": submissions_total,
        "validation_runs_total": runs_total,
        "valid_total": valid_total,
        "needs_review_total": needs_review_total,
        "invalid_total": invalid_total,
        "error_total": error_total,
    }


class ReviewDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    notes: str = Field(default="")


@router.post("/review/{submission_id}")
def review_submission(submission_id: int, payload: ReviewDecisionRequest, db: Session = Depends(get_db)):
    submission = db.scalar(select(SubmissionRecord).where(SubmissionRecord.id == submission_id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status != SubmissionStatus.NEEDS_REVIEW:
        raise HTTPException(status_code=409, detail="Submission is not awaiting manual review")

    run = db.scalar(
        select(ValidationRunRecord)
        .where(ValidationRunRecord.submission_id == submission_id)
        .order_by(ValidationRunRecord.created_at.desc())
    )
    if not run:
        raise HTTPException(status_code=404, detail="Validation run not found")

    notes_suffix = f"\nReviewer notes: {payload.notes.strip()}" if payload.notes.strip() else ""

    if payload.decision == "approve":
        orchestrator = ValidationOrchestrator(get_settings())
        challenge = orchestrator.load_challenge_from_disk(submission.extracted_path)
        orchestrator.ctfd_client.ensure_challenge(challenge)
        submission.status = SubmissionStatus.VALID
        run.status = SubmissionStatus.VALID
        run.ctfd_synced = True
        run.details = f"{run.details}\n\nManual review approved.{notes_suffix}"
    else:
        submission.status = SubmissionStatus.INVALID
        run.status = SubmissionStatus.INVALID
        run.details = f"{run.details}\n\nManual review rejected.{notes_suffix}"

    run.completed_at = datetime.utcnow()
    db.add(submission)
    db.add(run)
    db.commit()
    db.refresh(submission)
    db.refresh(run)
    return {
        "submission_id": submission.id,
        "status": submission.status.value,
        "run_id": run.id,
    }
