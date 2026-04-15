from datetime import datetime

from pydantic import BaseModel


class SubmissionRead(BaseModel):
    id: int
    group_id: str
    original_filename: str
    status: str
    challenge_name: str | None
    declared_port: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
