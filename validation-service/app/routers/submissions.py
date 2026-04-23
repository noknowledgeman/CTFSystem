from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.models import SubmissionRecord, SubmissionStatus
from app.models.submission import SubmissionRead
from app.services.zip_processor import ZipProcessor

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/upload", response_model=SubmissionRead)
async def upload_submission(
    group_id: str = Form(...),
    archive: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not archive.filename or not archive.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP uploads are supported")

    settings = get_settings()
    payload = await archive.read()
    processor = ZipProcessor(settings.upload_dir, settings.extract_dir)
    try:
        processed = processor.save_and_extract(archive.filename, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    submission = SubmissionRecord(
        group_id=group_id,
        original_filename=archive.filename,
        archive_path=str(processed.archive_path),
        extracted_path=str(Path(processed.extract_path)),
        challenge_name=processed.challenge.name,
        declared_port=processed.challenge.services[0].port,
        status=SubmissionStatus.UPLOADED,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("", response_model=list[SubmissionRead])
def list_submissions(db: Session = Depends(get_db)):
    rows = db.scalars(select(SubmissionRecord).order_by(SubmissionRecord.created_at.desc())).all()
    return list(rows)
