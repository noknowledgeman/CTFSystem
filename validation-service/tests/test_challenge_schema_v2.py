from pathlib import Path

import yaml
import pytest

from app.models.challenge_yaml import ChallengeYaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_v2_requires_services_and_steps():
    data = {
        "name": "V2",
        "description": "V2 format",
        "flag": "CTF{v2}",
        "difficulty": "simple",
        "verify": {"script": "verify.py", "language": "python", "timeout": 30},
        "services": [{"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 8080, "path": "/"}],
        "validation_steps": [
            {"type": "container_running"},
            {"type": "service_check", "service": "web"},
            {"type": "verify_script"},
        ],
    }
    model = ChallengeYaml.model_validate(data)
    assert len(model.services) == 1
    assert model.services[0].port == 8080
    assert [step.type for step in model.validation_steps] == ["container_running", "service_check", "verify_script"]


def test_non_web_fixture_schema_parses():
    fixture = Path(__file__).parent / "fixtures" / "non-web" / "challenge.yaml"
    model = ChallengeYaml.model_validate(_load_yaml(fixture))
    assert model.services[0].protocol == "tcp"
    assert any(step.type == "command" for step in model.validation_steps)


def test_multi_step_fixture_schema_parses():
    fixture = Path(__file__).parent / "fixtures" / "multi-step" / "challenge.yaml"
    model = ChallengeYaml.model_validate(_load_yaml(fixture))
    assert len(model.services) == 2
    assert [step.type for step in model.validation_steps] == [
        "container_running",
        "service_check",
        "service_check",
        "command",
        "verify_script",
    ]


def test_manual_review_step_requires_instructions():
    data = {
        "name": "Manual",
        "description": "Needs visual verification",
        "flag": "CTF{manual}",
        "difficulty": "medium",
        "verify": {"script": "verify.sh", "language": "bash", "timeout": 30},
        "services": [{"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 8080}],
        "validation_steps": [
            {"type": "container_running"},
            {"type": "manual_review"},
        ],
    }
    with pytest.raises(ValueError, match="manual_review steps must define non-empty `instructions`"):
        ChallengeYaml.model_validate(data)


def test_manual_review_step_with_instructions_and_bash_verify_parses():
    data = {
        "name": "Manual",
        "description": "Needs visual verification",
        "flag": "CTF{manual}",
        "difficulty": "medium",
        "verify": {"script": "verify.sh", "language": "bash", "timeout": 30},
        "services": [{"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 8080}],
        "validation_steps": [
            {"type": "container_running"},
            {
                "type": "manual_review",
                "instructions": "Confirm the dialog shown in the screenshot contains the flag.",
                "evidence_hint": "Attach screenshot from /tmp/challenge/dialog.png",
            },
            {"type": "verify_script"},
        ],
    }
    model = ChallengeYaml.model_validate(data)
    assert model.verify.language == "bash"
    assert model.validation_steps[1].type == "manual_review"
    assert model.validation_steps[1].instructions is not None
