from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillFlow MVP"
    database_url: str = "sqlite:///./skillflow.db"
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    app_base_url: str = "http://localhost:8000"
    telegram_bot_token: str = ""
    api_base_url: str = "http://localhost:8000"
    telegram_link_code_ttl_seconds: int = Field(default=600, ge=60, le=86400)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
