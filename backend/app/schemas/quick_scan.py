"""Quick scan and analysis report schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.eda import EDAResponse, EDASuggestions
from app.schemas.models import ClassificationResult, RegressionResult
from app.schemas.upload import ScanResult

StepStatus = Literal["success", "skipped", "failed"]


class QuickScanStepResult(BaseModel):
    """Outcome of a single analysis step in a quick scan."""

    step: str
    status: StepStatus
    message: str | None = None


class SQLImportSummary(BaseModel):
    """Summary of SQL table import during quick scan."""

    table_name: str
    columns: list[str]
    imported_rows: int


class QuickScanReport(BaseModel):
    """Bundled analysis results for one uploaded file."""

    report_id: str
    file_id: int
    filename: str
    file_hash: str
    row_count: int
    column_count: int
    generated_at: datetime
    steps: list[QuickScanStepResult] = Field(default_factory=list)
    security_scan: ScanResult | None = None
    eda: EDAResponse | None = None
    suggestions: EDASuggestions | None = None
    sql_import: SQLImportSummary | None = None
    regression: RegressionResult | None = None
    classification: ClassificationResult | None = None
    notes: list[str] = Field(default_factory=list)
