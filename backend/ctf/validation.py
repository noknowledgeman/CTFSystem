from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from sqlalchemy.orm import Session

from .models import Challenge


def _build_healthcheck_url(challenge: Challenge, metadata: Dict[str, Any]) -> str | None:
    """
    Build a simple HTTP healthcheck URL from challenge + metadata.

    Conventions for metadata:
    - vm_identifier: host or IP of the target VM (from Challenge.vm_identifier)
    - exposed_port: integer port where the challenge listens
    - healthcheck_path: optional path (default '/')
    """
    host = metadata.get("vm_address") or challenge.vm_identifier
    port = metadata.get("exposed_port")
    if not host or not port:
        return None
    path = metadata.get("healthcheck_path") or "/"
    if not path.startswith("/"):
        path = "/" + path
    return f"http://{host}:{port}{path}"


def validate_challenges(db: Session, timeout_s: float = 3.0) -> List[Dict[str, Any]]:
    """
    Validate that Docker-based challenges appear reachable on their designated VMs.

    For each challenge with a vm_identifier and upload_metadata containing
    at least an `exposed_port`, this function:
    - builds a healthcheck URL
    - performs a simple HTTP GET
    - records status (ok/failed/skipped) back into upload_metadata
    """
    results: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    challenges = db.query(Challenge).all()
    for c in challenges:
        status = "skipped"
        error: str | None = None

        try:
            metadata: Dict[str, Any] = {}
            if c.upload_metadata:
                try:
                    metadata = json.loads(c.upload_metadata)
                except json.JSONDecodeError:
                    # keep metadata empty but record decode issue
                    metadata = {}
                    error = "invalid_upload_metadata_json"

            url = _build_healthcheck_url(c, metadata)
            if not url:
                status = "skipped"
                if error is None:
                    error = "missing_vm_or_port"
            else:
                try:
                    resp = httpx.get(url, timeout=timeout_s)
                    if resp.status_code < 400:
                        status = "ok"
                    else:
                        status = "failed"
                        error = f"http_{resp.status_code}"
                except Exception as exc:  # pragma: no cover - network errors
                    status = "failed"
                    error = str(exc)

            # Update metadata with validation outcome
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["last_validation_status"] = status
            metadata["last_validation_error"] = error
            metadata["last_checked_at"] = now
            c.upload_metadata = json.dumps(metadata)
        finally:
            results.append(
                {
                    "challenge_id": c.id,
                    "name": c.name,
                    "vm_identifier": c.vm_identifier,
                    "status": status,
                    "error": error,
                    "checked_at": now,
                }
            )

    db.commit()
    return results

