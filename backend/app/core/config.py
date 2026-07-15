from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EduMate"
    app_env: str = "development"
    api_prefix: str = "/api"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/edumate"
    database_echo: bool = False
    qdrant_url: str = "http://localhost:6333"
    openai_api_key: str = "sk-change-me"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    backend_cors_origins: str = Field(default="http://localhost:5173")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

