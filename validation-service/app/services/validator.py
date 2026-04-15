from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import SubmissionRecord, SubmissionStatus, ValidationRunRecord
from app.services.ctfd_client import CTFdClient
from app.services.docker_checker import DockerChecker
from app.services.script_runner import ScriptRunner
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
        self.docker_checker = DockerChecker(ssh=ssh)
        self.script_runner = ScriptRunner(ssh=ssh, default_timeout=settings.default_verify_timeout)
        self.ctfd_client = CTFdClient(base_url=settings.ctfd_base_url, api_token=settings.ctfd_api_token)

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
            docker_ok, docker_details = self.docker_checker.check_containers_running(host, "/home/student/challenge")
            run.docker_ok = docker_ok

            port_ok, port_details = self.docker_checker.check_port_listening(host, submission.declared_port or 0)
            run.port_ok = port_ok

            challenge = self._load_challenge_from_disk(submission.extracted_path)
            verify_ok, verify_details = self.script_runner.run_verify_script(
                host=host,
                local_root=Path(submission.extracted_path),
                verify=challenge.verify,
                expected_flag=challenge.flag,
            )
            run.verify_ok = verify_ok

            synced = False
            if docker_ok and port_ok and verify_ok:
                self.ctfd_client.ensure_challenge(challenge)
                synced = True
            run.ctfd_synced = synced

            all_ok = docker_ok and port_ok and verify_ok and synced
            run.status = SubmissionStatus.VALID if all_ok else SubmissionStatus.INVALID
            submission.status = run.status
            run.details = "\n\n".join(
                [
                    "Docker check:\n" + docker_details,
                    "Port check:\n" + port_details,
                    "Verify output:\n" + verify_details,
                ]
            )
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

    def _load_challenge_from_disk(self, extracted_path: str):
        import yaml
        from app.models.challenge_yaml import ChallengeYaml

        challenge_file = Path(extracted_path) / "challenge.yaml"
        data = yaml.safe_load(challenge_file.read_text(encoding="utf-8")) or {}
        return ChallengeYaml.model_validate(data)
