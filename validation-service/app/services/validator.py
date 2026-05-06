from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import SubmissionRecord, SubmissionStatus, ValidationRunRecord
from app.services.ctfd_client import CTFdClient
from app.services.checks.handlers import ValidationStepExecutor
from app.services.checks.models import StepOutcome
from app.services.docker_checker import DockerChecker
from app.services.script_runner import ScriptRunner
from app.services.service_checker import ServiceChecker
from app.services.ssh_service import SSHService


class ValidationOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        ssh = SSHService(
            username=settings.ssh_username,
            private_key_path=settings.ssh_private_key_path,
            connect_timeout=settings.ssh_connect_timeout,
            command_timeout=settings.ssh_command_timeout,
        )
        self.ssh = ssh
        self.docker_checker = DockerChecker(ssh=ssh)
        self.service_checker = ServiceChecker(ssh=ssh)
        self.script_runner = ScriptRunner(ssh=ssh, default_timeout=settings.default_verify_timeout)
        self.ctfd_client = CTFdClient(base_url=settings.ctfd_base_url, api_token=settings.ctfd_api_token)
        self.step_executor = ValidationStepExecutor(
            ssh=self.ssh,
            docker_checker=self.docker_checker,
            service_checker=self.service_checker,
            script_runner=self.script_runner,
        )

    def validate_submission(self, db: Session, submission: SubmissionRecord) -> ValidationRunRecord:
        host = self._resolve_group_host(submission.group_id)
        run = ValidationRunRecord(
            submission_id=submission.id,
            status=SubmissionStatus.VALIDATING,
            vm_host=host,
            details="Validation started",
        )
        submission.status = SubmissionStatus.VALIDATING
        db.add(run)
        db.commit()
        db.refresh(run)
        db.refresh(submission)

        try:
            challenge = self.load_challenge_from_disk(submission.extracted_path)
            outcomes: list[StepOutcome] = []
            for step in challenge.validation_steps:
                outcome = self.step_executor.execute(
                    host=host,
                    challenge=challenge,
                    local_root=Path(submission.extracted_path),
                    step=step,
                )
                outcomes.append(outcome)

            run.docker_ok = all(
                outcome.ok for outcome in outcomes if outcome.step_type.startswith("container_running")
            ) if any(outcome.step_type.startswith("container_running") for outcome in outcomes) else None
            run.port_ok = all(
                outcome.ok for outcome in outcomes if outcome.step_type.startswith("service_check")
            ) if any(outcome.step_type.startswith("service_check") for outcome in outcomes) else None
            run.verify_ok = all(
                outcome.ok for outcome in outcomes if outcome.step_type == "verify_script"
            ) if any(outcome.step_type == "verify_script" for outcome in outcomes) else None

            synced = False
            required_ok = all(outcome.ok for outcome in outcomes if outcome.required)
            needs_manual_review = any(
                outcome.required and outcome.step_type == "manual_review"
                for outcome in outcomes
            )
            if required_ok and not needs_manual_review:
                self.ctfd_client.ensure_challenge(challenge)
                synced = True
            run.ctfd_synced = synced

            if required_ok and needs_manual_review:
                run.status = SubmissionStatus.NEEDS_REVIEW
            else:
                all_ok = required_ok and synced
                run.status = SubmissionStatus.VALID if all_ok else SubmissionStatus.INVALID
            submission.status = run.status
            run.details = "\n\n".join(
                [
                    f"[{idx}] {outcome.step_type} | required={outcome.required} | ok={outcome.ok}\n{outcome.details}"
                    for idx, outcome in enumerate(outcomes, start=1)
                ]
            )
            if required_ok and needs_manual_review:
                run.details += "\n\nPending staff approval: required manual review step(s) present."
        except Exception as exc:  # noqa: BLE001
            run.status = SubmissionStatus.ERROR
            submission.status = SubmissionStatus.ERROR
            run.details = f"Validation failed with error: {exc}"
        finally:
            run.completed_at = datetime.utcnow()
            db.add(run)
            db.add(submission)
            db.commit()
            db.refresh(run)

        return run

    def _resolve_group_host(self, group_id: str) -> str:
        if group_id not in self.settings.group_vm_map:
            raise ValueError(f"No VM mapping found for group_id: {group_id}")
        return self.settings.group_vm_map[group_id]

    def load_challenge_from_disk(self, extracted_path: str):
        import yaml
        from app.models.challenge_yaml import ChallengeYaml

        challenge_file = Path(extracted_path) / "challenge.yaml"
        data = yaml.safe_load(challenge_file.read_text(encoding="utf-8")) or {}
        return ChallengeYaml.model_validate(data)
