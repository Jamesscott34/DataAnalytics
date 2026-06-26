"""Encoding validation helpers.

Provides conservative text decoding for uploaded CSV files. Does not perform
CSV dialect detection or semantic data validation.
"""


class EncodingValidationError(ValueError):
    """Raised when uploaded bytes cannot be safely decoded as text."""


def decode_csv_bytes(content: bytes) -> str:
    """Decode CSV bytes using UTF-8 variants.

    Args:
        content: Raw uploaded file bytes.

    Returns:
        Decoded text.

    Raises:
        EncodingValidationError: If content is binary or not UTF-8 compatible.
    """
    if b"\x00" in content:
        raise EncodingValidationError("File contains null bytes")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise EncodingValidationError("CSV must be valid UTF-8 text") from exc

    if _non_printable_ratio(text) > 0.05:
        raise EncodingValidationError("File contains too many control characters")
    return text


def _non_printable_ratio(text: str) -> float:
    """Return ratio of non-printable control characters in text."""
    if not text:
        return 0.0
    allowed = {"\n", "\r", "\t"}
    non_printable = sum(
        1 for char in text if not char.isprintable() and char not in allowed
    )
    return non_printable / len(text)
