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
    qdrant_collection_name: str = "knowledge_chunks"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    openai_api_key: str = "sk-change-me"
    openai_base_url: str = ""
    openai_model: str = ""
    upload_dir: str = "uploads"
    max_upload_bytes: int = 50 * 1024 * 1024
    formula_ocr_enabled: bool = False
    formula_ocr_engine: str = "pix2tex"
    formula_ocr_min_confidence: float = 0.7
    log_level: str = "INFO"

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
