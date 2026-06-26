"""Date parsing helpers for EDA type inference.

Detects common date/datetime string formats without external dependencies.
"""

from datetime import datetime

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %Y",
    "%b %Y",
)


def parse_date_value(value: str) -> datetime | None:
    """Try to parse a single string value as a date or datetime.

    Args:
        value: Raw cell text.

    Returns:
        Parsed datetime when a supported format matches, else None.
    """
    text = value.strip()
    if not text:
        return None
    for pattern in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, pattern)
        except ValueError:
            continue
        return parsed
    return None


def is_date_like(value: str) -> bool:
    """Return True when the value matches a supported date format."""
    return parse_date_value(value) is not None


def looks_like_date_column(values: list[str]) -> bool:
    """Return True when most non-empty values parse as dates."""
    non_empty = [value.strip() for value in values if value.strip()]
    if not non_empty:
        return False
    parsed = sum(1 for value in non_empty if parse_date_value(value) is not None)
    return parsed / len(non_empty) >= 0.8


def month_name_to_number(month: str) -> int | None:
    """Map a month name to 1-12 when recognised."""
    text = month.strip().lower()
    for index, name in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    ):
        if text == name or text == name[:3]:
            return index
    return None
