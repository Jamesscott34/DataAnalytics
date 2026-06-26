"""Database and migration integration tests."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import Session

from app.models import UploadedFile, User, UserSession
from app.models.user import UserRole


def test_models_import() -> None:
    """ORM model classes are importable."""
    assert User.__tablename__ == "users"
    assert UserSession.__tablename__ == "user_sessions"
    assert UploadedFile.__tablename__ == "uploaded_files"


def test_alembic_upgrade_head(tmp_path: Path) -> None:
    """Alembic upgrade creates expected tables."""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(alembic_cfg, "head")

    inspector = inspect(engine_from_url(f"sqlite:///{db_path}"))
    tables = set(inspector.get_table_names())
    assert "users" in tables
    assert "user_sessions" in tables
    assert "uploaded_files" in tables


def engine_from_url(url: str) -> Engine:
    """Create an engine for the given URL (test helper)."""
    return create_engine(url)


def test_session_fixture_can_query(db_session: Session) -> None:
    """Session fixture queries users from the isolated test database."""
    count = db_session.query(User).count()
    assert count >= 0


def test_user_role_enum_values() -> None:
    """UserRole enum contains expected RBAC values."""
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.ANALYST.value == "analyst"
    assert UserRole.VIEWER.value == "viewer"
