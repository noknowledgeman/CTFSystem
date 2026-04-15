from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SubmissionRecord, SubmissionStatus, ValidationRunRecord

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    submissions_total = db.scalar(select(func.count(SubmissionRecord.id))) or 0
    runs_total = db.scalar(select(func.count(ValidationRunRecord.id))) or 0
    valid_total = db.scalar(
        select(func.count(SubmissionRecord.id)).where(SubmissionRecord.status == SubmissionStatus.VALID)
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
        "invalid_total": invalid_total,
        "error_total": error_total,
    }
