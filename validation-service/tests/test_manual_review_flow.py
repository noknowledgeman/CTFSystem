from pathlib import Path

from app.config import get_settings
from app.db.database import SessionLocal
from app.db.models import SubmissionRecord, SubmissionStatus, ValidationRunRecord
from app.models.challenge_yaml import ChallengeYaml
from app.services.checks.models import StepOutcome
from app.services.validator import ValidationOrchestrator


class _AlwaysPassExecutor:
    def execute(self, host: str, challenge: ChallengeYaml, local_root: Path, step):
        if step.type == "manual_review":
            return StepOutcome(
                step_type="manual_review",
                ok=True,
                details=f"Manual review required: {step.instructions}",
                required=step.required,
            )
        return StepOutcome(step_type=step.type, ok=True, details="ok", required=step.required)


class _TrackingCTFdClient:
    def __init__(self):
        self.calls = 0

    def ensure_challenge(self, challenge: ChallengeYaml) -> None:
        self.calls += 1


def _manual_challenge() -> ChallengeYaml:
    return ChallengeYaml.model_validate(
        {
            "name": "Manual Flow",
            "description": "Manual review flow",
            "flag": "CTF{manual_flow}",
            "difficulty": "medium",
            "verify": {"script": "verify.sh", "language": "bash", "timeout": 30},
            "services": [{"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 8080}],
            "validation_steps": [
                {"type": "container_running"},
                {"type": "manual_review", "instructions": "Visually verify image dialog contains the flag"},
                {"type": "verify_script"},
            ],
        }
    )


def test_orchestrator_sets_needs_review_and_skips_ctfd_sync():
    db = SessionLocal()
    submission = SubmissionRecord(
        group_id="group-1",
        original_filename="manual.zip",
        archive_path="/tmp/manual.zip",
        extracted_path="/tmp/manual",
        challenge_name="Manual Flow",
        declared_port=8080,
        status=SubmissionStatus.UPLOADED,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    orchestrator = ValidationOrchestrator(get_settings())
    tracker = _TrackingCTFdClient()
    orchestrator.step_executor = _AlwaysPassExecutor()
    orchestrator.ctfd_client = tracker
    orchestrator.load_challenge_from_disk = lambda _: _manual_challenge()

    run = orchestrator.validate_submission(db, submission)
    assert run.status == SubmissionStatus.NEEDS_REVIEW
    assert run.ctfd_synced is False
    assert "Pending staff approval" in run.details
    assert tracker.calls == 0
    db.close()


def test_admin_review_approve_then_reject_paths(monkeypatch):
    class DummyOrchestrator:
        synced = 0

        def __init__(self, _settings):
            self.ctfd_client = self

        def load_challenge_from_disk(self, _extracted_path: str):
            return _manual_challenge()

        def ensure_challenge(self, _challenge):
            DummyOrchestrator.synced += 1

    from app.routers import admin as admin_router

    monkeypatch.setattr(admin_router, "ValidationOrchestrator", DummyOrchestrator)

    db = SessionLocal()
    approve_submission = SubmissionRecord(
        group_id="group-1",
        original_filename="approve.zip",
        archive_path="/tmp/approve.zip",
        extracted_path="/tmp/approve",
        challenge_name="Manual Flow",
        declared_port=8080,
        status=SubmissionStatus.NEEDS_REVIEW,
    )
    reject_submission = SubmissionRecord(
        group_id="group-1",
        original_filename="reject.zip",
        archive_path="/tmp/reject.zip",
        extracted_path="/tmp/reject",
        challenge_name="Manual Flow",
        declared_port=8080,
        status=SubmissionStatus.NEEDS_REVIEW,
    )
    db.add(approve_submission)
    db.add(reject_submission)
    db.commit()
    db.refresh(approve_submission)
    db.refresh(reject_submission)
    approve_submission_id = approve_submission.id
    reject_submission_id = reject_submission.id

    db.add(
        ValidationRunRecord(
            submission_id=approve_submission_id,
            status=SubmissionStatus.NEEDS_REVIEW,
            vm_host="127.0.0.1",
            details="manual review pending",
        )
    )
    db.add(
        ValidationRunRecord(
            submission_id=reject_submission_id,
            status=SubmissionStatus.NEEDS_REVIEW,
            vm_host="127.0.0.1",
            details="manual review pending",
        )
    )
    db.commit()
    db.close()

    approve_response = admin_router.review_submission(
        approve_submission_id,
        admin_router.ReviewDecisionRequest(decision="approve", notes="Looks correct"),
        SessionLocal(),
    )
    assert approve_response["status"] == SubmissionStatus.VALID.value
    assert DummyOrchestrator.synced == 1

    reject_response = admin_router.review_submission(
        reject_submission_id,
        admin_router.ReviewDecisionRequest(
            decision="reject",
            notes="Dialog text does not show expected flag",
        ),
        SessionLocal(),
    )
    assert reject_response["status"] == SubmissionStatus.INVALID.value
