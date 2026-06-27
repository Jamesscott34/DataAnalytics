"""Quick scan service — runs all available analyses for a file."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.uploaded_file import UploadedFile
from app.schemas.eda import ColumnSummary, EDASuggestions
from app.schemas.models import ClassificationRequest, RegressionRequest
from app.schemas.quick_scan import (
    QuickScanReport,
    QuickScanStepResult,
    SQLImportSummary,
)
from app.services.classification_service import (
    ClassificationError,
    classification_service,
)
from app.services.eda_service import EDAError, eda_service
from app.services.regression_service import RegressionError, regression_service
from app.services.security_scan_service import security_scan_service
from app.services.sql_analysis_service import SQLAnalysisError, sql_analysis_service


class QuickScanError(ValueError):
    """Raised when a quick scan cannot be performed."""


class QuickScanService:
    """Orchestrates EDA, SQL import, regression, and classification for one file."""

    def __init__(self) -> None:
        self._reports: dict[str, QuickScanReport] = {}
        self._reports_by_file: dict[int, str] = {}

    def clear_reports(self) -> None:
        """Clear stored reports (used in tests)."""
        self._reports.clear()
        self._reports_by_file.clear()

    def run_quick_scan(self, db: Session, *, file_id: int) -> QuickScanReport:
        """Run all available analyses and return a bundled report."""
        file = self._get_file(db, file_id)
        steps: list[QuickScanStepResult] = []
        notes: list[str] = []

        scan = security_scan_service.latest_for_file(db, file_id)
        scan_result = security_scan_service.to_schema(scan) if scan else None
        if scan_result:
            steps.append(
                QuickScanStepResult(
                    step="security_scan",
                    status="success",
                    message=f"Status: {scan_result.status}, risk {scan_result.risk_score}/100",
                ),
            )
        else:
            steps.append(
                QuickScanStepResult(
                    step="security_scan",
                    status="skipped",
                    message="No security scan found for this file.",
                ),
            )

        eda_response = None
        try:
            eda_response = eda_service.run_for_file(db, file_id=file_id)
            steps.append(
                QuickScanStepResult(
                    step="eda",
                    status="success",
                    message=(
                        f"{eda_response.summary.row_count} rows, "
                        f"{eda_response.summary.missing_percent:.1f}% missing"
                    ),
                ),
            )
        except EDAError as exc:
            steps.append(
                QuickScanStepResult(step="eda", status="failed", message=str(exc)),
            )
            notes.append(f"EDA failed: {exc}")

        suggestions = None
        if eda_response is not None:
            try:
                suggestions = eda_service.get_suggestions(db, file_id=file_id)
                steps.append(
                    QuickScanStepResult(
                        step="eda_suggestions",
                        status="success",
                        message=", ".join(suggestions.suggested_analyses)
                        or "No suggestions",
                    ),
                )
            except EDAError as exc:
                steps.append(
                    QuickScanStepResult(
                        step="eda_suggestions",
                        status="failed",
                        message=str(exc),
                    ),
                )

        sql_summary = None
        try:
            sql_response = sql_analysis_service.import_rows(db, file_id=file_id)
            sql_summary = SQLImportSummary(
                table_name=sql_response.table_name,
                columns=sql_response.columns,
                imported_rows=sql_response.imported_rows,
            )
            steps.append(
                QuickScanStepResult(
                    step="sql_import",
                    status="success",
                    message=f"Imported {sql_response.imported_rows} rows",
                ),
            )
        except SQLAnalysisError as exc:
            steps.append(
                QuickScanStepResult(
                    step="sql_import", status="failed", message=str(exc)
                ),
            )

        regression_result = None
        regression_columns = (
            self._pick_regression_columns(eda_response.columns)
            if eda_response
            else None
        )
        if regression_columns is None:
            steps.append(
                QuickScanStepResult(
                    step="regression",
                    status="skipped",
                    message="Need at least two numeric columns for regression.",
                ),
            )
        else:
            target, features = regression_columns
            try:
                regression_result = regression_service.run_regression(
                    db,
                    file_id=file_id,
                    request=RegressionRequest(
                        algorithm="linear",
                        target_column=target,
                        feature_columns=features,
                        test_size=0.2,
                        random_state=42,
                    ),
                )
                steps.append(
                    QuickScanStepResult(
                        step="regression",
                        status="success",
                        message=f"R²={regression_result.metrics.r2}, MAE={regression_result.metrics.mae}",
                    ),
                )
            except (RegressionError, KeyError) as exc:
                steps.append(
                    QuickScanStepResult(
                        step="regression",
                        status="failed",
                        message=str(exc),
                    ),
                )

        classification_result = None
        classification_columns = (
            self._pick_classification_columns(suggestions) if suggestions else None
        )
        if classification_columns is None:
            steps.append(
                QuickScanStepResult(
                    step="classification",
                    status="skipped",
                    message="No suitable categorical target and features found.",
                ),
            )
        else:
            target, features = classification_columns
            try:
                classification_result = classification_service.run_classification(
                    db,
                    file_id=file_id,
                    request=ClassificationRequest(
                        algorithm="logistic",
                        target_column=target,
                        feature_columns=features,
                        test_size=0.2,
                        random_state=42,
                    ),
                )
                steps.append(
                    QuickScanStepResult(
                        step="classification",
                        status="success",
                        message=(
                            f"Accuracy={classification_result.metrics.accuracy}, "
                            f"F1={classification_result.metrics.f1}"
                        ),
                    ),
                )
            except (ClassificationError, KeyError) as exc:
                steps.append(
                    QuickScanStepResult(
                        step="classification",
                        status="failed",
                        message=str(exc),
                    ),
                )

        report = QuickScanReport(
            report_id=str(uuid.uuid4()),
            file_id=file.id,
            filename=file.original_filename,
            file_hash=file.file_hash,
            row_count=file.row_count or 0,
            column_count=file.column_count or 0,
            generated_at=datetime.now(UTC),
            steps=steps,
            security_scan=scan_result,
            eda=eda_response,
            suggestions=suggestions,
            sql_import=sql_summary,
            regression=regression_result,
            classification=classification_result,
            notes=notes,
        )
        self._reports[report.report_id] = report
        self._reports_by_file[file_id] = report.report_id
        return report

    def get_report(self, report_id: str) -> QuickScanReport:
        """Return a stored quick-scan report."""
        report = self._reports.get(report_id)
        if report is None:
            raise QuickScanError("Quick scan report not found")
        return report

    def get_latest_for_file(self, file_id: int) -> QuickScanReport:
        """Return the most recent quick-scan report for a file."""
        report_id = self._reports_by_file.get(file_id)
        if report_id is None:
            raise QuickScanError("No quick scan report for this file")
        return self.get_report(report_id)

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise QuickScanError("File not found")
        return file

    def _pick_regression_columns(
        self,
        columns: list[ColumnSummary],
    ) -> tuple[str, list[str]] | None:
        numeric = [
            column.name
            for column in columns
            if column.inferred_type in {"integer", "float"}
        ]
        if len(numeric) < 2:
            return None
        target = numeric[-1]
        features = [name for name in numeric[:-1]]
        for column in columns:
            if (
                column.inferred_type == "categorical"
                and column.name not in features
                and column.name != target
            ):
                features.append(column.name)
            if len(features) >= 8:
                break
        return target, features

    def _pick_classification_columns(
        self,
        suggestions: EDASuggestions | None,
    ) -> tuple[str, list[str]] | None:
        if not suggestions or not suggestions.target_columns:
            return None
        target = suggestions.target_columns[0]
        features = [name for name in suggestions.feature_columns if name != target][:8]
        if not features:
            return None
        return target, features


quick_scan_service = QuickScanService()
