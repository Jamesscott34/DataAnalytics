"""Temp assets listing and selection service.

Lists CSV files from the configured temp_assets directory and imports a selected
asset through the same validation, scan, and duplicate workflow as uploads.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import FileSource
from app.schemas.upload import AssetFileInfo, AssetListResponse, UploadResponse
from app.services.csv_service import CSVUploadError, csv_service
from app.utils.file_utils import FileValidationError, resolve_asset_path


class AssetsService:
    """Service for browsing and selecting temp_assets CSV files."""

    def list_assets(self) -> AssetListResponse:
        """Return CSV files available in the temp assets directory."""
        settings = get_settings()
        assets_dir = Path(settings.temp_assets_dir)
        assets_dir.mkdir(parents=True, exist_ok=True)

        files: list[AssetFileInfo] = []
        for path in sorted(assets_dir.glob("*.csv")):
            if not path.is_file():
                continue
            try:
                resolve_asset_path(assets_dir, path.name)
            except FileValidationError:
                continue
            files.append(
                AssetFileInfo(
                    name=path.name,
                    size_bytes=path.stat().st_size,
                    safe=True,
                )
            )
        return AssetListResponse(files=files)

    def select_asset(
        self,
        db: Session,
        *,
        filename: str,
        owner_id: int,
        duplicate_action: str | None = None,
    ) -> UploadResponse:
        """Import a temp asset through the secure upload pipeline."""
        settings = get_settings()
        assets_dir = Path(settings.temp_assets_dir)
        try:
            asset_path = resolve_asset_path(assets_dir, filename)
        except FileValidationError as exc:
            raise CSVUploadError(str(exc)) from exc

        content = asset_path.read_bytes()
        return csv_service.upload_csv(
            db,
            filename=asset_path.name,
            content=content,
            owner_id=owner_id,
            mime_type="text/csv",
            duplicate_action=duplicate_action,
            source=FileSource.TEMP_ASSET,
        )


assets_service = AssetsService()
