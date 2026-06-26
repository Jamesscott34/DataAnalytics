"""Python-only security scanner service.

Scans uploaded CSV files for defensive indicators such as unsafe filenames,
binary content, CSV formula injection, script injection, command strings, and
suspicious payloads.

This is not antivirus. It does not scan archives, detect novel malware, or
guarantee that a file is safe beyond the documented checks.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.security_scan import ScanStatus, SecurityScan
from app.schemas.upload import ScanResult
from app.utils.encoding_utils import EncodingValidationError, decode_csv_bytes
from app.utils.file_utils import FileValidationError, validate_filename
from app.utils.hash_utils import sha256_bytes

SCRIPT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"<\s*script\b",
        r"javascript\s*:",
        r"\bonerror\s*=",
        r"\bonclick\s*=",
        r"<\s*iframe\b",
        r"<\s*object\b",
        r"<\s*embed\b",
    )
]

DANGEROUS_FORMULA_PATTERN = re.compile(
    r"^\s*=\s*(cmd|hyperlink|webservice|importxml)\b",
    re.IGNORECASE,
)
FORMULA_PREFIX_PATTERN = re.compile(r"^\s*[=+\-@]")
COMMAND_PATTERN = re.compile(
    r"\b(cmd\.exe|powershell|bash\s+-i|nc\s+-e|wget\s+|curl\s+)\b",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\s,]+", re.IGNORECASE)
BASE64_PATTERN = re.compile(r"\b[A-Za-z0-9+/]{80,}={0,2}\b")


@dataclass
class ScanAccumulator:
    """Mutable accumulator for scanner issues and risk score."""

    issues: list[str]
    risk_score: int = 0
    blocked: bool = False

    def add(self, issue: str, score: int, *, blocked: bool = False) -> None:
        """Add a scanner issue with risk contribution."""
        self.issues.append(issue)
        self.risk_score = min(100, self.risk_score + score)
        self.blocked = self.blocked or blocked


class SecurityScanService:
    """Python-only scanner for uploaded CSV files."""

    def scan_bytes(self, *, filename: str, content: bytes) -> ScanResult:
        """Scan uploaded bytes and return a structured result.

        Args:
            filename: Original or sanitised filename.
            content: Raw uploaded file bytes.

        Returns:
            ScanResult with status, issues, risk score, and recommendation.
        """
        accumulator = ScanAccumulator(issues=[])
        self._check_filename(filename, accumulator)
        self._check_binary_content(content, accumulator)

        text = ""
        if not accumulator.blocked:
            text = self._decode_text(content, accumulator)
        if text:
            self._check_long_rows(text, accumulator)
            self._check_script_injection(text, accumulator)
            self._check_formula_injection(text, accumulator)
            self._check_command_strings(text, accumulator)
            self._check_urls(text, accumulator)
            self._check_base64_payloads(text, accumulator)

        status = self._status_for(accumulator)
        return ScanResult(
            status=status.value,
            issues=accumulator.issues,
            risk_score=accumulator.risk_score,
            recommended_action=self._recommendation_for(status),
            scan_timestamp=datetime.now(UTC),
            file_hash=sha256_bytes(content),
        )

    def persist_scan(
        self,
        db: Session,
        *,
        file_id: int,
        result: ScanResult,
    ) -> SecurityScan:
        """Persist a scan result for an uploaded file.

        Args:
            db: Active database session.
            file_id: Uploaded file identifier.
            result: ScanResult to persist.

        Returns:
            Persisted SecurityScan instance.
        """
        scan = SecurityScan(
            file_id=file_id,
            status=ScanStatus(result.status),
            risk_score=result.risk_score,
            issues=result.issues,
            recommended_action=result.recommended_action,
            file_hash=result.file_hash,
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan

    def latest_for_file(self, db: Session, file_id: int) -> SecurityScan | None:
        """Return latest scan for file if one exists."""
        return (
            db.query(SecurityScan)
            .filter(SecurityScan.file_id == file_id)
            .order_by(SecurityScan.scanned_at.desc())
            .first()
        )

    def to_schema(self, scan: SecurityScan) -> ScanResult:
        """Convert a SecurityScan ORM object to a schema."""
        return ScanResult(
            status=scan.status.value,
            issues=scan.issue_list(),
            risk_score=scan.risk_score,
            recommended_action=scan.recommended_action,
            scan_timestamp=scan.scanned_at,
            file_hash=scan.file_hash,
        )

    def _check_filename(self, filename: str, accumulator: ScanAccumulator) -> None:
        """Check filename safety."""
        try:
            validate_filename(filename)
        except FileValidationError as exc:
            accumulator.add(str(exc), 100, blocked=True)

    def _check_binary_content(
        self,
        content: bytes,
        accumulator: ScanAccumulator,
    ) -> None:
        """Check for binary indicators before text scanning."""
        if b"\x00" in content:
            accumulator.add("File contains null bytes", 100, blocked=True)

    def _decode_text(self, content: bytes, accumulator: ScanAccumulator) -> str:
        """Decode text content or block if encoding is unsafe."""
        try:
            return decode_csv_bytes(content)
        except EncodingValidationError as exc:
            accumulator.add(str(exc), 100, blocked=True)
            return ""

    def _check_long_rows(self, text: str, accumulator: ScanAccumulator) -> None:
        """Warn on unusually long CSV rows that may indicate payloads."""
        if any(len(line) > 100_000 for line in text.splitlines()):
            accumulator.add("File contains unusually long rows", 20)

    def _check_script_injection(
        self,
        text: str,
        accumulator: ScanAccumulator,
    ) -> None:
        """Detect HTML and JavaScript injection markers."""
        for pattern in SCRIPT_PATTERNS:
            if pattern.search(text):
                accumulator.add("Potential HTML or JavaScript injection detected", 30)
                return

    def _check_formula_injection(
        self,
        text: str,
        accumulator: ScanAccumulator,
    ) -> None:
        """Detect CSV formula injection cells."""
        for line in text.splitlines():
            for cell in line.split(","):
                stripped = cell.strip().strip('"').strip("'")
                if DANGEROUS_FORMULA_PATTERN.search(stripped):
                    accumulator.add("Dangerous spreadsheet formula detected", 45)
                    return
                if FORMULA_PREFIX_PATTERN.search(stripped):
                    accumulator.add("CSV formula injection pattern detected", 20)
                    return

    def _check_command_strings(
        self,
        text: str,
        accumulator: ScanAccumulator,
    ) -> None:
        """Detect suspicious command execution strings."""
        if COMMAND_PATTERN.search(text):
            accumulator.add("Suspicious command string detected", 40)

    def _check_urls(self, text: str, accumulator: ScanAccumulator) -> None:
        """Detect suspicious embedded URLs."""
        if URL_PATTERN.search(text):
            accumulator.add("Embedded URL detected", 10)

    def _check_base64_payloads(self, text: str, accumulator: ScanAccumulator) -> None:
        """Detect long base64-like payloads."""
        if BASE64_PATTERN.search(text):
            accumulator.add("Embedded base64-looking payload detected", 20)

    def _status_for(self, accumulator: ScanAccumulator) -> ScanStatus:
        """Determine scan status from accumulated risk."""
        if accumulator.blocked or accumulator.risk_score >= 70:
            return ScanStatus.BLOCKED
        if accumulator.issues:
            return ScanStatus.WARNING
        return ScanStatus.SAFE

    def _recommendation_for(self, status: ScanStatus) -> str:
        """Return recommended user action for status."""
        if status == ScanStatus.BLOCKED:
            return "Do not analyse this file. Replace it with a clean CSV."
        if status == ScanStatus.WARNING:
            return "Review issues before analysis and clean suspicious cells."
        return "File passed scanner checks and can be analysed."


security_scan_service = SecurityScanService()
