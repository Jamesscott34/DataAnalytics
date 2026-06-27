"""XLSX conversion tests."""

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.services.xlsx_conversion_service import (
    XLSXConversionError,
    xlsx_conversion_service,
)
from app.utils.file_utils import FileValidationError


def _make_simple_xlsx_bytes() -> bytes:
    """Helper to create a small in-memory XLSX file."""
    buffer = BytesIO()
    pd.DataFrame({"sku": ["A1", "B2"], "qty": [1, 3]}).to_excel(
        buffer,
        index=False,
        engine="openpyxl",
    )
    return buffer.getvalue()


def test_convert_bytes_produces_csv() -> None:
    """XLSX bytes are converted to CSV with headers preserved."""
    csv_name, csv_bytes = xlsx_conversion_service.convert_bytes(
        _make_simple_xlsx_bytes(),
        filename="retail.xlsx",
    )
    assert csv_name == "retail.csv"
    assert b"sku,qty" in csv_bytes
    assert b"A1" in csv_bytes


def test_convert_bytes_empty_content_raises() -> None:
    """Empty XLSX content is rejected with an XLSXConversionError."""
    with pytest.raises(XLSXConversionError, match="empty"):
        xlsx_conversion_service.convert_bytes(b"", filename="empty.xlsx")


def test_convert_bytes_non_xlsx_content_raises() -> None:
    """Non-XLSX bytes are rejected with an XLSXConversionError."""
    with pytest.raises(XLSXConversionError, match="Failed to read"):
        xlsx_conversion_service.convert_bytes(
            b"this is not a real xlsx file",
            filename="not-really.xlsx",
        )


def test_convert_bytes_empty_workbook_raises() -> None:
    """XLSX files without any usable worksheet data are rejected."""
    from openpyxl import Workbook

    buffer = BytesIO()
    Workbook().save(buffer)

    with pytest.raises(XLSXConversionError, match="no rows"):
        xlsx_conversion_service.convert_bytes(
            buffer.getvalue(),
            filename="empty-workbook.xlsx",
        )


def test_convert_bytes_invalid_filename_raises() -> None:
    """Unsafe or invalid filenames are rejected by the conversion service."""
    with pytest.raises(FileValidationError, match="path"):
        xlsx_conversion_service.convert_bytes(
            _make_simple_xlsx_bytes(),
            filename="../../etc/passwd.xlsx",
        )


def test_convert_bytes_legacy_xls_extension_rejected() -> None:
    """Legacy .xls filenames are rejected before parsing."""
    with pytest.raises(FileValidationError, match="Only .xlsx"):
        xlsx_conversion_service.convert_bytes(
            _make_simple_xlsx_bytes(),
            filename="legacy.xls",
        )


def test_convert_asset_missing_file_raises(tmp_path) -> None:
    """convert_asset fails when the asset file is missing."""
    with pytest.raises(XLSXConversionError, match="not found"):
        xlsx_conversion_service.convert_asset(tmp_path, "nonexistent-asset.xlsx")


def test_upload_xlsx_endpoint_stores_csv(client: TestClient) -> None:
    """POST /uploads/xlsx converts workbook and stores CSV metadata."""
    email = "xlsx-uploader@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/uploads/xlsx",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "course.xlsx",
                _make_simple_xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "course.csv"
    assert response.json()["column_count"] >= 2


def test_convert_xlsx_endpoint_missing_asset_returns_400(client: TestClient) -> None:
    """Asset-based conversion returns HTTP 400 when the asset file is missing."""
    email = "xlsx-asset@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/assets/convert-xlsx",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "nonexistent-asset.xlsx"},
    )

    assert response.status_code == 400
    assert "not found" in response.json()["message"].lower()


def test_upload_xlsx_endpoint_rejects_invalid_bytes(client: TestClient) -> None:
    """POST /uploads/xlsx returns 400 for invalid workbook bytes."""
    email = "xlsx-invalid@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/uploads/xlsx",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "broken.xlsx",
                b"not-a-workbook",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 400
    assert "xlsx" in response.json()["message"].lower()
