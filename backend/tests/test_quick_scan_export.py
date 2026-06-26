"""Quick scan and export tests."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services.quick_scan_service import quick_scan_service
from app.services.scan_result_storage import scan_result_storage


@pytest.fixture
def scan_results_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use an isolated scan_results directory for export tests."""
    results_dir = tmp_path / "scan_results"
    results_dir.mkdir()
    settings = get_settings()
    monkeypatch.setattr(settings, "scan_results_dir", str(results_dir))
    scan_result_storage._root = results_dir  # noqa: SLF001
    return results_dir


def _analyst_token(client: TestClient) -> str:
    email = "quickscan-analyst@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _upload(client: TestClient, token: str, filename: str, content: bytes) -> int:
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["file_id"]


def test_quick_scan_runs_analyses_and_exports(
    client: TestClient,
    scan_results_dir: Path,
) -> None:
    """Quick scan bundles EDA, SQL, regression, and classification when possible."""
    quick_scan_service.clear_reports()
    token = _analyst_token(client)
    content = (
        b"region,units,revenue,label\n"
        b"North,10,100,A\n"
        b"North,12,120,A\n"
        b"South,8,70,B\n"
        b"South,9,80,B\n"
        b"East,15,150,A\n"
        b"East,14,140,A\n"
        b"West,11,110,B\n"
        b"West,13,130,B\n"
    )
    file_id = _upload(client, token, "scan-data.csv", content)

    response = client.post(
        f"/api/v1/files/{file_id}/quick-scan",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["file_id"] == file_id
    assert body["eda"] is not None
    assert body["sql_import"] is not None
    step_names = {step["step"] for step in body["steps"]}
    assert "eda" in step_names
    assert "sql_import" in step_names

    report_id = body["report_id"]
    md_response = client.post(
        "/api/v1/export/markdown",
        headers={"Authorization": f"Bearer {token}"},
        json={"report_id": report_id},
    )
    assert md_response.status_code == 200
    md_body = md_response.json()
    assert re.match(r"scan-data_Analytics_\d{2}-\d{2}-\d{2}\.md", md_body["saved"]["filename"])
    saved_md = scan_results_dir / md_body["saved"]["filename"]
    assert saved_md.is_file()
    assert "Analysis Report" in saved_md.read_text(encoding="utf-8")
    assert "## Exploratory data analysis" in saved_md.read_text(encoding="utf-8")

    pdf_response = client.post(
        "/api/v1/export/pdf",
        headers={"Authorization": f"Bearer {token}"},
        json={"report_id": report_id},
    )
    assert pdf_response.status_code == 200
    pdf_body = pdf_response.json()
    assert re.match(r"scan-data_Analytics_\d{2}-\d{2}-\d{2}\.pdf", pdf_body["saved"]["filename"])
    saved_pdf = scan_results_dir / pdf_body["saved"]["filename"]
    assert saved_pdf.is_file()
    assert saved_pdf.read_bytes().startswith(b"%PDF")

    list_response = client.get(
        "/api/v1/export/scan-results",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 2
    filenames = {item["filename"] for item in listed["items"]}
    assert md_body["saved"]["filename"] in filenames
    assert pdf_body["saved"]["filename"] in filenames

    view_md = client.get(
        f"/api/v1/export/scan-results/{md_body['saved']['filename']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert view_md.status_code == 200
    assert "Analysis Report" in view_md.text

    view_pdf = client.get(
        f"/api/v1/export/scan-results/{pdf_body['saved']['filename']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert view_pdf.status_code == 200
    assert view_pdf.content.startswith(b"%PDF")
