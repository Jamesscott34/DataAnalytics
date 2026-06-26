"""Hashing helpers.

Provides cryptographic hashes used for file deduplication and integrity
checks. Does not store secrets or handle password hashing; see auth utilities.
"""

import hashlib


def sha256_bytes(content: bytes) -> str:
    """Return SHA-256 hash for bytes as lowercase hex.

    Args:
        content: Raw bytes to hash.

    Returns:
        SHA-256 digest as a 64-character hexadecimal string.
    """
    # SHA-256 is used instead of MD5 because this hash is a deduplication key.
    return hashlib.sha256(content).hexdigest()
