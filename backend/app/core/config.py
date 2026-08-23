from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default="sqlite:///./parcelpilot.db", alias="DATABASE_URL")
    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_minutes: int = Field(default=15, alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=14, alias="REFRESH_TOKEN_DAYS")
    refresh_cookie_name: str = Field(default="refresh_token", alias="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(default=False, alias="REFRESH_COOKIE_SECURE")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    backend_origin: str = Field(default="http://localhost:8000", alias="BACKEND_ORIGIN")

    voyage_api_key: str | None = Field(default=None, alias="VOYAGE_API_KEY")
    voyage_embedding_model: str = Field(default="voyage-3-large", alias="VOYAGE_EMBEDDING_MODEL")
    qdrant_url: str | None = Field(default=None, alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="parcelpilot_documents", alias="QDRANT_COLLECTION")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    dataset_snapshot_time: str = Field(
        default="2026-08-16 11:00 Asia/Kolkata",
        alias="DATASET_SNAPSHOT_TIME",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_frontend_origins() -> list[str]:
    settings = get_settings()
    origins = [
        origin.strip()
        for origin in settings.frontend_origin.split(",")
        if origin.strip()
    ]
    origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])
    return sorted(set(origins))
