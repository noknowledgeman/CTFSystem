from datetime import datetime

from pydantic import BaseModel


class ValidationResult(BaseModel):
    run_id: int
    submission_id: int
    status: str
    vm_host: str | None
    docker_ok: bool | None
    port_ok: bool | None
    verify_ok: bool | None
    ctfd_synced: bool | None
    details: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
