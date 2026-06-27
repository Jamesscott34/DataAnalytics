"""XLSX to CSV conversion for course datasets."""

from io import BytesIO
from pathlib import Path

import pandas as pd

from app.utils.file_utils import sanitize_workbook_filename


class XLSXConversionError(ValueError):
    """Raised when an XLSX file cannot be converted to CSV."""


class XLSXConversionService:
    """Convert Excel workbooks to UTF-8 CSV bytes."""

    def convert_bytes(self, content: bytes, *, filename: str) -> tuple[str, bytes]:
        """Convert XLSX bytes to CSV text bytes."""
        safe_name = sanitize_workbook_filename(filename)
        if not safe_name.lower().endswith(".xlsx"):
            raise XLSXConversionError("Only .xlsx workbooks can be converted")
        if not content:
            raise XLSXConversionError("XLSX file is empty")
        try:
            frame = pd.read_excel(BytesIO(content), engine="openpyxl")
        except Exception as exc:  # noqa: BLE001 - surface parser errors to clients.
            raise XLSXConversionError(f"Failed to read XLSX workbook: {exc}") from exc
        if frame.empty:
            raise XLSXConversionError("XLSX workbook contains no rows")
        csv_name = f"{Path(safe_name).stem}.csv"
        csv_bytes = frame.to_csv(index=False).encode("utf-8")
        return csv_name, csv_bytes

    def convert_asset(self, assets_dir: Path, filename: str) -> tuple[str, bytes]:
        """Read a temp asset XLSX file and return CSV filename and bytes."""
        path = assets_dir / filename
        if not path.exists():
            raise XLSXConversionError("XLSX asset not found")
        return self.convert_bytes(path.read_bytes(), filename=filename)


xlsx_conversion_service = XLSXConversionService()
