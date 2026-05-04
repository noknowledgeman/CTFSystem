"""Verify legacy challenge *types* map to v2 validator + ZipProcessor (no professor-facing docs).

CTF-3/4/9 folders may be incomplete in this workspace; we still prove the *shape* of those
challenges is representable. CTF-8 ships a real compose file under Challenges/ — we use it.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
import yaml

from app.models.challenge_yaml import ChallengeYaml
from app.services.zip_processor import COMPOSE_FILENAMES, ZipProcessor


REPO_ROOT = Path(__file__).resolve().parents[2]
CHALLENGES = REPO_ROOT / "Challenges"
CTF8_COMPOSE = (
    CHALLENGES
    / "508954-138408 - CTF - 8 - Delia Popa - 08 December 2025 633 PM"
    / "EH2025"
    / "docker-compose.yml"
)


def _build_zip_bytes(files: dict[str, str | bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as zf:
        for name, content in files.items():
            if isinstance(content, str):
                zf.writestr(name, content.encode("utf-8"))
            else:
                zf.writestr(name, content)
    return stream.getvalue()


def _minimal_verify_py(flag: str) -> str:
    return f"print('{flag}')\n"


def test_ctf3_style_web_plus_db_maps_to_v2_and_passes_zip_processor(tmp_path):
    """CTF-3 style: HTTP + PostgreSQL (README: ports 80 and 5432)."""
    flag = "CTF{ctf3_compat}"
    compose = """services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
"""
    challenge = {
        "name": "CTF-3 style",
        "description": "Web + DB multi-service",
        "flag": flag,
        "difficulty": "medium",
        "verify": {"script": "verify.py", "language": "python", "timeout": 60},
        "deployment": {"remote_dir": "/home/student/challenge"},
        "services": [
            {"name": "web", "protocol": "http", "host": "127.0.0.1", "port": 80, "path": "/", "expected_status": 200},
            {"name": "db", "protocol": "tcp", "host": "127.0.0.1", "port": 5432},
        ],
        "validation_steps": [
            {"type": "container_running"},
            {"type": "service_check", "service": "web"},
            {"type": "service_check", "service": "db"},
            {"type": "verify_script"},
        ],
    }
    ChallengeYaml.model_validate(challenge)
    payload = _build_zip_bytes(
        {
            "compose.yaml": compose,
            "challenge.yaml": yaml.safe_dump(challenge, sort_keys=False),
            "verify.py": _minimal_verify_py(flag),
            "README.md": "# writeup\n",
        }
    )
    proc = ZipProcessor(str(tmp_path / "up"), str(tmp_path / "ex"))
    out = proc.save_and_extract("ctf3-style.zip", payload)
    assert out.challenge.name == "CTF-3 style"
    assert (out.extract_path / "compose.yaml").is_file()


def test_ctf9_style_multi_tcp_maps_to_v2_and_passes_zip_processor(tmp_path):
    """CTF-9 style: FTP + HTTP + passive sample (README-style multi-port)."""
    flag = "CTF{ctf9_compat}"
    compose = """services:
  ctf:
    image: alpine:3.19
    command: ["sleep", "infinity"]
    ports:
      - "21:21"
      - "8080:8080"
      - "30000:30000"
"""
    challenge = {
        "name": "CTF-9 style",
        "description": "Multi TCP",
        "flag": flag,
        "difficulty": "difficult",
        "verify": {"script": "verify.py", "language": "python", "timeout": 90},
        "services": [
            {"name": "ftp", "protocol": "tcp", "host": "127.0.0.1", "port": 21},
            {"name": "http", "protocol": "tcp", "host": "127.0.0.1", "port": 8080},
            {"name": "pasv", "protocol": "tcp", "host": "127.0.0.1", "port": 30000},
        ],
        "validation_steps": [
            {"type": "container_running"},
            {"type": "service_check", "service": "ftp"},
            {"type": "service_check", "service": "http"},
            {"type": "service_check", "service": "pasv"},
            {"type": "verify_script"},
        ],
    }
    ChallengeYaml.model_validate(challenge)
    payload = _build_zip_bytes(
        {
            "docker-compose.yaml": compose,
            "challenge.yaml": yaml.safe_dump(challenge, sort_keys=False),
            "verify.py": _minimal_verify_py(flag),
            "writeup.md": "# w\n",
        }
    )
    proc = ZipProcessor(str(tmp_path / "up"), str(tmp_path / "ex"))
    out = proc.save_and_extract("ctf9-style.zip", payload)
    assert len(out.challenge.services) == 3


def test_ctf8_on_disk_compose_builds_valid_submission_zip(tmp_path):
    """Use real EH2025/docker-compose.yml from Challenges/ when present."""
    if not CTF8_COMPOSE.is_file():
        pytest.skip("CTF-8 compose not present in workspace")
    compose_text = CTF8_COMPOSE.read_text(encoding="utf-8")
    data = yaml.safe_load(compose_text) or {}
    ports = []
    for _svc_name, svc in (data.get("services") or {}).items():
        for mapping in svc.get("ports") or []:
            if isinstance(mapping, str) and ":" in mapping:
                host_port = mapping.split(":", 1)[0].strip().strip('"')
                if host_port.isdigit():
                    ports.append(int(host_port))
    assert 8000 in ports
    flag = "CTF{ctf8_compat}"
    challenge = {
        "name": "CTF-8 on-disk",
        "description": "From repo compose",
        "flag": flag,
        "difficulty": "medium",
        "verify": {"script": "verify.py", "language": "python", "timeout": 60},
        "services": [
            {
                "name": "web",
                "protocol": "http",
                "host": "127.0.0.1",
                "port": 8000,
                "path": "/",
                "expected_status": 200,
            },
        ],
        "validation_steps": [
            {"type": "container_running"},
            {"type": "service_check", "service": "web"},
            {"type": "verify_script"},
        ],
    }
    ChallengeYaml.model_validate(challenge)
    payload = _build_zip_bytes(
        {
            "docker-compose.yml": compose_text,
            "challenge.yaml": yaml.safe_dump(challenge, sort_keys=False),
            "verify.py": _minimal_verify_py(flag),
            "README.md": "# w\n",
        }
    )
    proc = ZipProcessor(str(tmp_path / "up"), str(tmp_path / "ex"))
    proc.save_and_extract("ctf8.zip", payload)


def test_all_expected_compose_names_are_listed():
    """Guardrail: keep ZipProcessor and tests aligned on accepted filenames."""
    assert "compose.yaml" in COMPOSE_FILENAMES
    assert "docker-compose.yaml" in COMPOSE_FILENAMES
