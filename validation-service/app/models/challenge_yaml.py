from typing import Literal

from pydantic import BaseModel, Field, field_validator


class VerifyConfig(BaseModel):
    script: str = Field(min_length=1)
    language: Literal["python", "bash"]
    timeout: int = Field(default=30, ge=1, le=300)


class ChallengeYaml(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    flag: str = Field(min_length=1, max_length=512)
    difficulty: Literal["simple", "medium", "difficult"]
    port: int = Field(ge=1, le=65535)
    verify: VerifyConfig

    @field_validator("flag")
    @classmethod
    def ensure_flag_has_format(cls, value: str) -> str:
        if "{" not in value or "}" not in value:
            raise ValueError("flag must use a standard wrapped format (e.g. CTF{...})")
        return value
