"""Python-only security scanner tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.security_scan import SecurityScan
from app.services.security_scan_service import security_scan_service


def _scan(content: bytes, filename: str = "scan.csv"):
    """Scan bytes with default CSV filename."""
    return security_scan_service.scan_bytes(filename=filename, content=content)


def test_xss_payload_detection() -> None:
    """Scanner detects script tags."""
    result = _scan(b"name,comment\nA,<script>alert(1)</script>\n")
    assert result.status == "warning"
    assert any("JavaScript" in issue for issue in result.issues)


def test_javascript_url_detection() -> None:
    """Scanner detects javascript: URLs."""
    result = _scan(b"name,link\nA,javascript:alert(1)\n")
    assert result.status == "warning"
    assert result.risk_score > 0


def test_csv_formula_injection_detection() -> None:
    """Scanner detects formula injection prefixes."""
    result = _scan(b"name,value\nA,=1+1\n")
    assert result.status == "warning"
    assert any("formula injection" in issue.lower() for issue in result.issues)


def test_dangerous_spreadsheet_formula_detection() -> None:
    """Scanner detects dangerous spreadsheet functions."""
    result = _scan(b'name,value\nA,=HYPERLINK("http://evil.test")\n')
    assert result.status == "warning"
    assert any(
        "dangerous spreadsheet formula" in issue.lower() for issue in result.issues
    )


def test_suspicious_command_string_detection() -> None:
    """Scanner detects command execution strings."""
    result = _scan(b"name,cmd\nA,powershell -nop\n")
    assert result.status == "warning"
    assert any("command" in issue.lower() for issue in result.issues)


def test_oversized_row_detection() -> None:
    """Scanner detects unusually long rows."""
    result = _scan(("a\n" + "x" * 100_001 + "\n").encode())
    assert result.status == "warning"
    assert any("long rows" in issue.lower() for issue in result.issues)


def test_base64_payload_detection() -> None:
    """Scanner detects long base64-like payloads."""
    payload = b"A" * 100
    result = _scan(b"name,payload\nA," + payload + b"\n")
    assert result.status == "warning"
    assert any("base64" in issue.lower() for issue in result.issues)


def test_binary_content_blocked() -> None:
    """Scanner blocks binary/null-byte content."""
    result = _scan(b"name,value\nA,\x00\n")
    assert result.status == "blocked"
    assert result.risk_score == 100


def test_scan_persisted_on_upload(client: TestClient, db_session: Session) -> None:
    """Uploading a CSV creates a security scan row."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "scan@example.com",
            "password": "password123",
            "role": "analyst",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "scan@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("scan.csv", b"name,value\nA,1\n", "text/csv")},
    )
    assert response.status_code == 201
    assert response.json()["scan_result"]["status"] == "safe"

    file_id = response.json()["file_id"]
    assert db_session.query(SecurityScan).filter_by(file_id=file_id).count() == 1

    latest = client.get(
        f"/api/v1/scans/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert latest.status_code == 200
    assert latest.json()["status"] == "safe"
