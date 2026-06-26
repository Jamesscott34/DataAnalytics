"""Application configuration from environment variables.

Loads settings via Pydantic BaseSettings. Secrets and environment-specific
values must come from ``.env`` files, never hard-coded in application code.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_env: Literal["development", "production", "test"] = "development"
    env: str = "development"
    log_level: str = "INFO"
    log_json: bool = True
    slow_request_threshold_ms: int = 2000

    database_url: str = Field(
        default="sqlite:///./data/app.db",
        alias="DATABASE_URL",
    )

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    allow_public_registration: bool = Field(
        default=True,
        alias="ALLOW_PUBLIC_REGISTRATION",
    )

    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    temp_assets_dir: str = Field(default="./temp_assets", alias="TEMP_ASSETS_DIR")

    rate_limit_upload_per_minute: int = Field(
        default=10,
        alias="RATE_LIMIT_UPLOAD_PER_MINUTE",
    )
    rate_limit_analysis_per_minute: int = Field(
        default=20,
        alias="RATE_LIMIT_ANALYSIS_PER_MINUTE",
    )

    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_api_base_url: str = Field(default="", alias="LLM_API_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> str:
        """Normalise CORS origins to a comma-separated string for storage."""
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list for middleware configuration."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes derived from megabyte setting."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance.

    Returns:
        Singleton Settings loaded from the environment.
    """
    return Settings()
