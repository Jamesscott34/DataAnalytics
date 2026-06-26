"""Structured logging helpers for application and audit events.

Provides named loggers and helpers for consistent structured fields.
Never log file contents, raw CSV rows, or plaintext passwords.
"""

import logging
from typing import Any

APP_LOGGER_NAME = "app"
AUDIT_LOGGER_NAME = "app.audit"


def get_logger(name: str = APP_LOGGER_NAME) -> logging.Logger:
    """Return a configured application logger.

    Args:
        name: Logger name; defaults to the application root logger.

    Returns:
        Standard library Logger instance.
    """
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Return the dedicated audit event logger.

    Returns:
        Logger used for security-relevant audit events.
    """
    return logging.getLogger(AUDIT_LOGGER_NAME)


def log_audit_event(
    event_type: str,
    action: str,
    result: str,
    *,
    user_id: int | None = None,
    file_hash: str | None = None,
    filename: str | None = None,
    ip_address: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured audit log entry.

    Args:
        event_type: Category such as upload, scan, or analysis.
        action: Specific action performed.
        result: Outcome such as success, failure, or blocked.
        user_id: Authenticated user identifier when available.
        file_hash: SHA-256 hash of related file when applicable.
        filename: Sanitised filename when applicable.
        ip_address: Client IP when available.
        extra: Additional JSON-serialisable metadata fields.
    """
    payload: dict[str, Any] = {
        "event_type": event_type,
        "action": action,
        "result": result,
        "user_id": user_id,
        "file_hash": file_hash,
        "filename": filename,
        "ip_address": ip_address,
    }
    if extra:
        payload.update(extra)

    get_audit_logger().info("audit_event", extra=payload)
