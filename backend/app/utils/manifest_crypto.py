"""Password-protected manifest encryption helpers.

Derives a Fernet key from a user password with PBKDF2 and encrypts JSON
manifest payloads. Does not persist passwords or manage manifest files.
"""

import base64
import json
import os
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
PBKDF2_ITERATIONS = 600_000


class ManifestCryptoError(ValueError):
    """Raised when manifest encryption or decryption fails."""


def encrypt_manifest(password: str, payload: dict[str, Any]) -> bytes:
    """Encrypt a manifest dictionary with a password-derived key."""
    if not password:
        raise ManifestCryptoError("Manifest password is required")
    salt = os.urandom(SALT_SIZE)
    fernet = _derive_fernet(password, salt)
    token = fernet.encrypt(json.dumps(payload).encode("utf-8"))
    return salt + token


def decrypt_manifest(password: str, blob: bytes) -> dict[str, Any]:
    """Decrypt a manifest blob using the provided password."""
    if len(blob) <= SALT_SIZE:
        raise ManifestCryptoError("Manifest file is invalid")
    salt = blob[:SALT_SIZE]
    token = blob[SALT_SIZE:]
    fernet = _derive_fernet(password, salt)
    try:
        decrypted = fernet.decrypt(token)
    except InvalidToken as exc:
        raise ManifestCryptoError("Incorrect manifest password") from exc
    return cast(dict[str, Any], json.loads(decrypted.decode("utf-8")))


def _derive_fernet(password: str, salt: bytes) -> Fernet:
    """Derive a Fernet instance from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return Fernet(key)
