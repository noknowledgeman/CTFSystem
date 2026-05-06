from pathlib import Path

from app.models.challenge_yaml import ChallengeYaml, ServiceConfig, ValidationStep
from app.services.checks.models import StepOutcome
from app.services.docker_checker import DockerChecker
from app.services.script_runner import ScriptRunner
from app.services.service_checker import ServiceChecker
from app.services.ssh_service import SSHService


class ValidationStepExecutor:
    def __init__(
        self,
        ssh: SSHService,
        docker_checker: DockerChecker,
        service_checker: ServiceChecker,
        script_runner: ScriptRunner,
    ) -> None:
        self.ssh = ssh
        self.docker_checker = docker_checker
        self.service_checker = service_checker
        self.script_runner = script_runner

    def execute(
        self,
        host: str,
        challenge: ChallengeYaml,
        local_root: Path,
        step: ValidationStep,
    ) -> StepOutcome:
        if step.type == "container_running":
            ok, details = self.docker_checker.check_containers_running(host, challenge.deployment.remote_dir)
            return StepOutcome(step_type=step.type, ok=ok, details=details, required=step.required)

        if step.type == "service_check":
            service = self._resolve_service(challenge, step)
            timeout = step.timeout or challenge.verify.timeout
            ok, details = self.service_checker.check_service(host, service, timeout=timeout)
            return StepOutcome(
                step_type=f"{step.type}:{service.name or service.port}",
                ok=ok,
                details=details,
                required=step.required,
            )

        if step.type == "command":
            if not step.command:
                return StepOutcome(step_type=step.type, ok=False, details="Missing command in step", required=step.required)
            result = self.ssh.run_command(host, step.command, timeout=step.timeout)
            output = (result.stdout + "\n" + result.stderr).strip()
            ok = result.exit_code == 0
            if step.expect_contains:
                ok = ok and step.expect_contains in output
            return StepOutcome(step_type=step.type, ok=ok, details=output, required=step.required)

        if step.type == "verify_script":
            ok, details = self.script_runner.run_verify_script(
                host=host,
                local_root=local_root,
                verify=challenge.verify,
                expected_flag=challenge.flag,
            )
            return StepOutcome(step_type=step.type, ok=ok, details=details, required=step.required)

        if step.type == "manual_review":
            details = f"Manual review required: {step.instructions}"
            if step.evidence_hint:
                details = f"{details}\nEvidence hint: {step.evidence_hint}"
            return StepOutcome(step_type=step.type, ok=True, details=details, required=step.required)

        return StepOutcome(step_type=step.type, ok=False, details=f"Unsupported step type: {step.type}", required=step.required)

    def _resolve_service(self, challenge: ChallengeYaml, step: ValidationStep) -> ServiceConfig:
        if step.service:
            for svc in challenge.services:
                if svc.name == step.service or str(svc.port) == step.service:
                    return svc
            raise ValueError(f"Service `{step.service}` not found in challenge services")
        return challenge.services[0]
