from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SubmissionStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[str] = mapped_column(String(100), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    archive_path: Mapped[str] = mapped_column(String(512))
    extracted_path: Mapped[str] = mapped_column(String(512))
    challenge_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    declared_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(SqlEnum(SubmissionStatus), default=SubmissionStatus.UPLOADED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    validation_runs: Mapped[list["ValidationRunRecord"]] = relationship(back_populates="submission")


class ValidationRunRecord(Base):
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    status: Mapped[SubmissionStatus] = mapped_column(SqlEnum(SubmissionStatus), default=SubmissionStatus.VALIDATING)
    vm_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    docker_ok: Mapped[bool | None] = mapped_column(nullable=True)
    port_ok: Mapped[bool | None] = mapped_column(nullable=True)
    verify_ok: Mapped[bool | None] = mapped_column(nullable=True)
    ctfd_synced: Mapped[bool | None] = mapped_column(nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    submission: Mapped[SubmissionRecord] = relationship(back_populates="validation_runs")
