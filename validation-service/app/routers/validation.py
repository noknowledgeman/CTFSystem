from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.models import SubmissionRecord, ValidationRunRecord
from app.models.validation_result import ValidationResult
from app.services.validator import ValidationOrchestrator

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("/{submission_id}", response_model=ValidationResult)
def validate_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.scalar(select(SubmissionRecord).where(SubmissionRecord.id == submission_id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    orchestrator = ValidationOrchestrator(get_settings())
    run = orchestrator.validate_submission(db, submission)
    return ValidationResult(
        run_id=run.id,
        submission_id=run.submission_id,
        status=run.status.value,
        vm_host=run.vm_host,
        docker_ok=run.docker_ok,
        port_ok=run.port_ok,
        verify_ok=run.verify_ok,
        ctfd_synced=run.ctfd_synced,
        details=run.details,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


@router.get("/status/{run_id}", response_model=ValidationResult)
def validation_status(run_id: int, db: Session = Depends(get_db)):
    run = db.scalar(select(ValidationRunRecord).where(ValidationRunRecord.id == run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return ValidationResult(
        run_id=run.id,
        submission_id=run.submission_id,
        status=run.status.value,
        vm_host=run.vm_host,
        docker_ok=run.docker_ok,
        port_ok=run.port_ok,
        verify_ok=run.verify_ok,
        ctfd_synced=run.ctfd_synced,
        details=run.details,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )
