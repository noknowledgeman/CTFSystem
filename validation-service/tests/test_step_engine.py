from pathlib import Path

from app.models.challenge_yaml import ChallengeYaml
from app.services.checks.handlers import ValidationStepExecutor


class DummySSH:
    def __init__(self):
        self.commands = []

    def run_command(self, host: str, command: str, timeout=None):
        self.commands.append((host, command, timeout))
        class Result:
            exit_code = 0
            stdout = "hello"
            stderr = ""
        return Result()


class DummyDockerChecker:
    def check_containers_running(self, host: str, remote_dir: str):
        return True, f"containers ok in {remote_dir}"


class DummyServiceChecker:
    def check_service(self, host: str, service, timeout: int = 30):
        return True, f"service {service.name or service.port} ok"


class DummyScriptRunner:
    def run_verify_script(self, host: str, local_root: Path, verify, expected_flag: str):
        return True, f"verified {expected_flag}"


def test_step_executor_orders_and_executes_steps():
    challenge = ChallengeYaml.model_validate(
        {
            "name": "Ordered",
            "description": "Ordered steps",
            "flag": "CTF{ordered}",
            "difficulty": "medium",
            "verify": {"script": "verify.py", "language": "python", "timeout": 30},
            "services": [{"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 8080, "path": "/health"}],
            "validation_steps": [
                {"type": "container_running"},
                {"type": "service_check", "service": "web"},
                {"type": "command", "command": "echo hello", "expect_contains": "hello"},
                {"type": "verify_script"},
            ],
        }
    )
    executor = ValidationStepExecutor(
        ssh=DummySSH(),
        docker_checker=DummyDockerChecker(),
        service_checker=DummyServiceChecker(),
        script_runner=DummyScriptRunner(),
    )
    outcomes = [
        executor.execute("10.0.0.1", challenge, Path("."), step)
        for step in challenge.validation_steps
    ]
    assert [out.step_type for out in outcomes] == [
        "container_running",
        "service_check:web",
        "command",
        "verify_script",
    ]
    assert all(out.ok for out in outcomes)
