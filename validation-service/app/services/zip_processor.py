from __future__ import annotations

import shutil
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.models.challenge_yaml import ChallengeYaml


CHALLENGE_YAML = "challenge.yaml"
COMPOSE_FILENAMES = (
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yaml",
    "compose.yml",
)
OPTIONAL_WRITEUPS = ("writeup.md", "README.md", "writeup.txt")


@dataclass
class ProcessedSubmission:
    archive_path: Path
    extract_path: Path
    challenge: ChallengeYaml


class ZipProcessor:
    def __init__(self, upload_dir: str, extract_dir: str) -> None:
        self.upload_root = Path(upload_dir)
        self.extract_root = Path(extract_dir)
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.extract_root.mkdir(parents=True, exist_ok=True)

    def save_and_extract(self, file_name: str, payload: bytes) -> ProcessedSubmission:
        token = uuid.uuid4().hex
        archive_dir = self.upload_root / token
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / file_name
        archive_path.write_bytes(payload)

        extract_path = self.extract_root / token
        extract_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(extract_path)

        normalized_root = self._normalize_extract_root(extract_path)
        challenge = self._read_challenge(normalized_root / "challenge.yaml")
        self._validate_structure(normalized_root, challenge)
        return ProcessedSubmission(archive_path=archive_path, extract_path=normalized_root, challenge=challenge)

    def cleanup(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def _normalize_extract_root(self, extract_path: Path) -> Path:
        children = [item for item in extract_path.iterdir() if item.name != "__MACOSX"]
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        return extract_path

    def _read_challenge(self, challenge_file: Path) -> ChallengeYaml:
        if not challenge_file.exists():
            raise ValueError("challenge.yaml is missing from the submission archive")
        try:
            data = yaml.safe_load(challenge_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"challenge.yaml is invalid YAML: {exc}") from exc
        return ChallengeYaml.model_validate(data)

    def _compose_file_at_root(self, root: Path) -> Path | None:
        for name in COMPOSE_FILENAMES:
            candidate = root / name
            if candidate.is_file():
                return candidate
        return None

    def _validate_structure(self, root: Path, challenge: ChallengeYaml) -> None:
        if not (root / CHALLENGE_YAML).is_file():
            raise ValueError(f"Missing required file: {CHALLENGE_YAML}")
        if self._compose_file_at_root(root) is None:
            raise ValueError(
                "Missing Docker Compose file at archive root. "
                f"Expected one of: {', '.join(COMPOSE_FILENAMES)}"
            )

        verify_path = root / challenge.verify.script
        if not verify_path.exists():
            raise ValueError(f"Verify script not found: {challenge.verify.script}")

        if not any((root / candidate).exists() for candidate in OPTIONAL_WRITEUPS):
            raise ValueError("A write-up file is required (writeup.md, README.md, or writeup.txt)")
