"""Asset integrity manifest API schemas."""

from pydantic import BaseModel, Field


class IntegrityFileInfo(BaseModel):
    """Tracked or discovered file metadata."""

    path: str
    sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int


class ModifiedIntegrityFile(BaseModel):
    """File whose SHA-256 no longer matches the manifest."""

    path: str
    stored_sha256: str = Field(min_length=64, max_length=64)
    current_sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int


class IntegrityStatusResponse(BaseModel):
    """Current integrity scan and manifest state."""

    manifest_exists: bool
    unlocked: bool
    watched_folders: list[str]
    discovered_file_count: int
    setup_required: bool
    new_files: list[IntegrityFileInfo] = []
    modified_files: list[ModifiedIntegrityFile] = []
    removed_files: list[str] = []
    unchanged_count: int = 0


class InitializeManifestRequest(BaseModel):
    """Create a new password-protected manifest."""

    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class UnlockManifestRequest(BaseModel):
    """Unlock an existing password-protected manifest."""

    password: str = Field(min_length=1, max_length=128)


class ApplyIntegrityChangesRequest(BaseModel):
    """Apply user-approved manifest updates."""

    add_or_update: list[str] = []
    remove: list[str] = []


class IntegrityActionResponse(BaseModel):
    """Simple integrity action result."""

    message: str
    unlocked: bool = False
    setup_required: bool = False
