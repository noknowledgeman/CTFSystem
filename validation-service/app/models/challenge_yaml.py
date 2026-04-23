from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class VerifyConfig(BaseModel):
    script: str = Field(min_length=1)
    language: Literal["python", "bash"]
    timeout: int = Field(default=30, ge=1, le=300)


class DeploymentConfig(BaseModel):
    remote_dir: str = Field(default="/home/student/challenge", min_length=1)


class ServiceConfig(BaseModel):
    name: str = Field(default="")
    protocol: Literal["tcp", "udp", "http", "https"] = Field(default="tcp")
    host: str = Field(default="127.0.0.1", min_length=1)
    port: int = Field(ge=1, le=65535)
    path: str | None = None
    expected_status: int = Field(default=200, ge=100, le=599)


class ValidationStep(BaseModel):
    type: Literal["container_running", "service_check", "command", "verify_script"]
    service: str | None = None
    command: str | None = None
    expect_contains: str | None = None
    timeout: int | None = Field(default=None, ge=1, le=600)
    required: bool = True


class ChallengeYaml(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    flag: str = Field(min_length=1, max_length=512)
    difficulty: Literal["simple", "medium", "difficult"]
    verify: VerifyConfig
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    services: list[ServiceConfig] = Field(min_length=1)
    validation_steps: list[ValidationStep] = Field(min_length=1)

    @field_validator("flag")
    @classmethod
    def ensure_flag_has_format(cls, value: str) -> str:
        if "{" not in value or "}" not in value:
            raise ValueError("flag must use a standard wrapped format (e.g. CTF{...})")
        return value

    @model_validator(mode="after")
    def validate_v2_requirements(self) -> "ChallengeYaml":
        # v2-only: names are required for reliable step references.
        for service in self.services:
            if not service.name.strip():
                raise ValueError("Each service in services[] must have a non-empty name")

        service_names = {service.name for service in self.services}
        for step in self.validation_steps:
            if step.type == "service_check":
                if not step.service:
                    raise ValueError("service_check steps must define `service`")
                if step.service not in service_names:
                    raise ValueError(f"service_check references unknown service `{step.service}`")
        return self
