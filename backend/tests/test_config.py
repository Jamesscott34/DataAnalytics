"""Configuration loading tests."""

import os

from app.config import Settings, get_settings


def test_settings_load_defaults() -> None:
    """Settings instantiate with documented default values."""
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.database_url.startswith("sqlite")
    assert "http://localhost:5173" in settings.cors_origin_list


def test_cors_origin_list_parses_csv() -> None:
    """Comma-separated CORS origins are split into a list."""
    settings = Settings(CORS_ORIGINS="http://a.test,http://b.test")
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]


def test_max_upload_size_bytes() -> None:
    """Upload byte limit is derived from megabyte setting."""
    settings = Settings(MAX_UPLOAD_SIZE_MB=10)
    assert settings.max_upload_size_bytes == 10 * 1024 * 1024


def test_get_settings_cached(monkeypatch) -> None:
    """get_settings returns the same cached instance."""
    get_settings.cache_clear()
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
    os.environ.pop("LOG_LEVEL", None)
