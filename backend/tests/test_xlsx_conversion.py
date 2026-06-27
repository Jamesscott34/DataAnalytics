"""XLSX conversion tests."""

from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from app.services.xlsx_conversion_service import xlsx_conversion_service


def test_convert_bytes_produces_csv() -> None:
    """XLSX bytes are converted to CSV with headers preserved."""
    buffer = BytesIO()
    pd.DataFrame({"sku": ["A1", "B2"], "qty": [1, 3]}).to_excel(
        buffer,
        index=False,
        engine="openpyxl",
    )
    csv_name, csv_bytes = xlsx_conversion_service.convert_bytes(
        buffer.getvalue(),
        filename="retail.xlsx",
    )
    assert csv_name == "retail.csv"
    assert b"sku,qty" in csv_bytes
    assert b"A1" in csv_bytes


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
    buffer = BytesIO()
    pd.DataFrame({"region": ["North"], "sales": [100]}).to_excel(
        buffer,
        index=False,
        engine="openpyxl",
    )
    response = client.post(
        "/api/v1/uploads/xlsx",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "course.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "course.csv"
    assert response.json()["column_count"] >= 2
