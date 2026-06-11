from functools import lru_cache
from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="VAL_DATABASE_URL", default="sqlite:///./validation.db")
    upload_dir: str = Field(alias="VAL_UPLOAD_DIR", default="/tmp/validation/uploads")
    extract_dir: str = Field(alias="VAL_EXTRACT_DIR", default="/tmp/validation/extracted")

    ctfd_base_url: str = Field(alias="VAL_CTFD_BASE_URL", default="http://localhost:8000")
    ctfd_api_token: str = Field(alias="VAL_CTFD_API_TOKEN", default="")

    ssh_private_key_path: str = Field(alias="VAL_SSH_PRIVATE_KEY_PATH", default="~/.ssh/id_ed25519")
    ssh_username: str = Field(alias="VAL_SSH_USERNAME", default="student")
    ssh_connect_timeout: int = Field(alias="VAL_SSH_CONNECT_TIMEOUT", default=15)
    ssh_command_timeout: int = Field(alias="VAL_SSH_COMMAND_TIMEOUT", default=60)
    default_verify_timeout: int = Field(alias="VAL_DEFAULT_VERIFY_TIMEOUT", default=30)
    group_vm_map: Dict[str, str] = Field(alias="VAL_GROUP_VM_MAP", default_factory=dict)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
