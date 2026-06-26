"""Password hashing utilities using bcrypt.

Uses bcrypt directly rather than passlib to avoid compatibility issues with
newer Python releases. Plaintext passwords are never stored or logged.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for database storage.

    Args:
        plain_password: User-provided password.

    Returns:
        bcrypt hash string safe to persist in ``users.hashed_password``.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: Password supplied at login.
        hashed_password: Value from ``users.hashed_password``.

    Returns:
        True if the password matches the hash.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
