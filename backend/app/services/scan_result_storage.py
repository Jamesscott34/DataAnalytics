"""Persist quick-scan exports to the scan_results directory."""

import re
from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings
from app.schemas.export import SavedScanResult
from app.utils.file_utils import ensure_within_directory

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]+")


class ScanResultStorageError(ValueError):
    """Raised when scan result files cannot be read or written."""


class ScanResultStorage:
    """Save and list analytics reports under scan_results/."""

    def __init__(self) -> None:
        self._root = Path(get_settings().scan_results_dir)

    @property
    def root(self) -> Path:
        return self._root

    def ensure_directory(self) -> Path:
        """Create scan_results directory if missing."""
        self._root.mkdir(parents=True, exist_ok=True)
        return self._root

    def build_filename(self, original_filename: str, extension: str) -> str:
        """Build ``{name}_Analytics_dd-mm-yy.{ext}`` for an export."""
        stem = Path(original_filename).stem
        cleaned = _FILENAME_SAFE_RE.sub("_", stem).strip("_") or "dataset"
        date_str = datetime.now(UTC).strftime("%d-%m-%y")
        return f"{cleaned}_Analytics_{date_str}.{extension.lstrip('.')}"

    def save_bytes(self, *, content: bytes, original_filename: str, extension: str) -> SavedScanResult:
        """Write binary content (PDF) to scan_results."""
        self.ensure_directory()
        filename = self._unique_filename(self.build_filename(original_filename, extension))
        path = self._root / filename
        path.write_bytes(content)
        return self._to_metadata(path, format_label="pdf")

    def save_text(
        self,
        *,
        content: str,
        original_filename: str,
        extension: str = "md",
    ) -> SavedScanResult:
        """Write text content to scan_results."""
        self.ensure_directory()
        filename = self._unique_filename(self.build_filename(original_filename, extension))
        path = self._root / filename
        path.write_text(content, encoding="utf-8")
        return self._to_metadata(path, format_label=self._format_for_suffix(path.suffix))

    def list_results(self) -> list[SavedScanResult]:
        """List saved scan result files newest first."""
        self.ensure_directory()
        files = [
            path
            for path in self._root.iterdir()
            if path.is_file() and path.suffix.lower() in {".md", ".pdf", ".json", ".csv"}
        ]
        files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        return [self._to_metadata(path) for path in files]

    def resolve_path(self, filename: str) -> Path:
        """Resolve a safe path inside scan_results for reading."""
        self.ensure_directory()
        safe_name = Path(filename).name
        if safe_name != filename or ".." in filename:
            raise ScanResultStorageError("Invalid filename")
        path = self._root / safe_name
        ensure_within_directory(self._root, path)
        if not path.is_file():
            raise ScanResultStorageError("Scan result file not found")
        return path

    def read_text(self, filename: str) -> str:
        """Read a saved text report."""
        path = self.resolve_path(filename)
        if path.suffix.lower() not in {".md", ".json", ".csv"}:
            raise ScanResultStorageError("File is not a text report")
        return path.read_text(encoding="utf-8")

    def read_bytes(self, filename: str) -> bytes:
        """Read a saved PDF report."""
        path = self.resolve_path(filename)
        if path.suffix.lower() != ".pdf":
            raise ScanResultStorageError("File is not a PDF report")
        return path.read_bytes()

    def _unique_filename(self, filename: str) -> str:
        path = self._root / filename
        if not path.exists():
            return filename
        stem = path.stem
        suffix = path.suffix
        counter = 2
        while (self._root / f"{stem}-{counter}{suffix}").exists():
            counter += 1
        return f"{stem}-{counter}{suffix}"

    def _to_metadata(self, path: Path, format_label: str | None = None) -> SavedScanResult:
        suffix = path.suffix.lower()
        resolved_format = format_label or self._format_for_suffix(suffix)
        stat = path.stat()
        return SavedScanResult(
            filename=path.name,
            format=resolved_format,  # type: ignore[arg-type]
            size_bytes=stat.st_size,
            saved_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            view_url=f"/api/v1/export/scan-results/{path.name}",
            download_url=f"/api/v1/export/scan-results/{path.name}/download",
        )

    def _format_for_suffix(self, suffix: str) -> str:
        formats = {
            ".csv": "csv",
            ".json": "json",
            ".md": "markdown",
            ".pdf": "pdf",
        }
        return formats.get(suffix.lower(), "markdown")


scan_result_storage = ScanResultStorage()
