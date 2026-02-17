from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ctf.db"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    default_admin_password: str = "admin"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
