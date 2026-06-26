"""File validation and path safety helpers.

Provides filename sanitisation, extension checks, and upload path validation.
Does not read file contents or perform CSV parsing.
"""

import re
from pathlib import Path

BLOCKED_EXTENSIONS = {
    ".bat",
    ".bin",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".js",
    ".msi",
    ".ps1",
    ".scr",
    ".sh",
    ".vbs",
}

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class FileValidationError(ValueError):
    """Raised when an upload filename or path fails validation."""


def sanitize_filename(filename: str) -> str:
    """Return a storage-safe filename.

    Args:
        filename: Client-provided filename.

    Returns:
        Sanitised basename with unsafe characters replaced by underscores.

    Raises:
        FileValidationError: If the filename is empty or unsafe.
    """
    validate_filename(filename)
    basename = Path(filename).name
    sanitized = _SAFE_FILENAME_RE.sub("_", basename).strip("._")
    if not sanitized:
        raise FileValidationError("Filename is empty after sanitisation")
    return sanitized


def validate_filename(filename: str) -> None:
    """Validate an uploaded filename before storage.

    Args:
        filename: Client-provided filename.

    Raises:
        FileValidationError: If the filename is unsafe or not a CSV file.
    """
    if not filename:
        raise FileValidationError("Filename is required")
    if "\x00" in filename:
        raise FileValidationError("Filename contains a null byte")
    if filename != Path(filename).name:
        raise FileValidationError("Filename must not contain path separators")
    if Path(filename).is_absolute():
        raise FileValidationError("Absolute paths are not allowed")
    if ".." in Path(filename).parts or ".." in filename:
        raise FileValidationError("Path traversal is not allowed")

    suffixes = [suffix.lower() for suffix in Path(filename).suffixes]
    if not suffixes or suffixes[-1] != ".csv":
        raise FileValidationError("Only .csv files are allowed")
    if any(suffix in BLOCKED_EXTENSIONS for suffix in suffixes):
        raise FileValidationError("Executable or script extensions are blocked")


def ensure_within_directory(base_dir: Path, candidate: Path) -> Path:
    """Resolve a path and ensure it remains inside a base directory.

    Args:
        base_dir: Trusted parent directory.
        candidate: Candidate child path.

    Returns:
        Resolved candidate path.

    Raises:
        FileValidationError: If candidate escapes base_dir.
    """
    resolved_base = base_dir.resolve()
    resolved_candidate = candidate.resolve()
    is_inside = resolved_base in resolved_candidate.parents
    if not is_inside and resolved_candidate != resolved_base:
        raise FileValidationError("Resolved path escapes upload directory")
    return resolved_candidate
