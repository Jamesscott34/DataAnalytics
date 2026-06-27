"""Shared CSV parsing helpers for upload and EDA services."""

import csv
from io import StringIO


class CSVParseError(ValueError):
    """Raised when CSV text cannot be parsed."""


def parse_csv_rows(text: str) -> tuple[list[str], list[list[str]], list[str]]:
    """Parse CSV text into headers, normalized data rows, and warnings.

    Ragged rows (market-basket style) are padded to a consistent width instead
    of being rejected.
    """
    reader = csv.reader(StringIO(text, newline=""))
    try:
        rows = list(reader)
    except csv.Error as exc:
        raise CSVParseError(f"Invalid CSV format: {exc}") from exc

    if not rows or not rows[0]:
        raise CSVParseError("CSV must contain a header row")

    headers = [
        header.strip() or f"column_{index + 1}" for index, header in enumerate(rows[0])
    ]
    data_rows = [row for row in rows[1:] if any(cell.strip() for cell in row)]
    warnings: list[str] = []

    max_width = max(
        [len(headers), *[len(row) for row in data_rows]], default=len(headers)
    )
    if max_width > len(headers):
        warnings.append(
            "Ragged CSV rows detected; extra columns were padded for analysis"
        )
        original_width = len(headers)
        for index in range(original_width, max_width):
            headers.append(f"item_{index - original_width + 1}")

    normalized_rows: list[list[str]] = []
    for row in data_rows:
        if len(row) < max_width:
            row = row + [""] * (max_width - len(row))
        elif len(row) > max_width:
            row = row[:max_width]
        normalized_rows.append(row)

    return headers, normalized_rows, warnings
