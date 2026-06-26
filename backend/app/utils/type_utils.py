"""Column type inference helpers for EDA."""

from datetime import datetime

from app.utils.date_utils import looks_like_date_column, parse_date_value

BOOLEAN_TRUE = {"true", "yes", "y", "1"}
BOOLEAN_FALSE = {"false", "no", "n", "0"}


def normalize_cell(value: str | None) -> str:
    """Normalise a CSV cell to stripped text."""
    if value is None:
        return ""
    return value.strip()


def is_missing(value: str) -> bool:
    """Return True for empty or common missing-value tokens."""
    text = normalize_cell(value).lower()
    return text in {"", "na", "n/a", "null", "none", "-"}


def infer_column_type(values: list[str], *, row_count: int) -> str:
    """Infer a column type from observed cell values.

    Args:
        values: Column values including blanks.
        row_count: Total rows in the dataset.

    Returns:
        One of ``integer``, ``float``, ``boolean``, ``datetime``,
        ``categorical``, or ``string``.
    """
    non_missing = [normalize_cell(value) for value in values if not is_missing(value)]
    if not non_missing:
        return "string"

    lowered = {value.lower() for value in non_missing}
    if lowered <= BOOLEAN_TRUE | BOOLEAN_FALSE:
        return "boolean"

    if looks_like_date_column(non_missing):
        return "datetime"

    if all(_is_int(value) for value in non_missing):
        return "integer"

    if all(_is_float(value) for value in non_missing):
        return "float"

    unique_ratio = len(set(non_missing)) / max(row_count, 1)
    if unique_ratio <= 0.2 or len(set(non_missing)) <= 20:
        return "categorical"

    return "string"


def coerce_float(value: str) -> float | None:
    """Parse a numeric string to float when possible."""
    text = normalize_cell(value)
    if is_missing(text):
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def coerce_int(value: str) -> int | None:
    """Parse a numeric string to int when possible."""
    number = coerce_float(value)
    if number is None:
        return None
    if number.is_integer():
        return int(number)
    return None


def parse_datetime_value(value: str) -> datetime | None:
    """Expose date parsing for EDA statistics."""
    text = normalize_cell(value)
    if is_missing(text):
        return None
    return parse_date_value(text)


def _is_int(value: str) -> bool:
    return coerce_int(value) is not None


def _is_float(value: str) -> bool:
    return coerce_float(value) is not None
