"""Business KPI analytics service."""

import csv
import uuid
from collections import defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.business import (
    BusinessAnalyticsRequest,
    BusinessChartPoint,
    BusinessReport,
    KPICard,
)
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class BusinessAnalyticsError(ValueError):
    """Raised when business analytics cannot access a dataset."""


class BusinessAnalyticsService:
    """Compute simple business KPIs from uploaded CSV files."""

    def __init__(self) -> None:
        self._results_by_file: dict[int, BusinessReport] = {}
        self._results: dict[str, BusinessReport] = {}

    def clear_results(self) -> None:
        """Clear stored results (used in tests)."""
        self._results_by_file.clear()
        self._results.clear()

    def analyze(
        self,
        db: Session,
        *,
        file_id: int,
        request: BusinessAnalyticsRequest,
    ) -> BusinessReport:
        """Analyze revenue/cost/date columns and return KPI cards."""
        file = self._get_file(db, file_id)
        headers, rows = self._read_rows(file)
        revenue_column = request.revenue_column or self._infer_column(
            headers,
            ("revenue", "sales", "amount", "price", "total"),
        )
        cost_column = request.cost_column or self._infer_column(
            headers,
            ("cost", "expense", "spend"),
        )
        date_column = request.date_column or self._infer_column(headers, ("date", "month"))

        if revenue_column is None:
            report = self._empty_report(
                file_id=file_id,
                row_count=len(rows),
                note="Business analytics needs a numeric revenue, sales, amount, or price column.",
            )
            self._store(report)
            return report

        indexes = {name: index for index, name in enumerate(headers)}
        revenue_index = indexes[revenue_column]
        cost_index = indexes.get(cost_column) if cost_column else None
        date_index = indexes.get(date_column) if date_column else None

        revenues: list[float] = []
        costs: list[float] = []
        monthly_revenue: dict[str, float] = defaultdict(float)
        for row in rows:
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            revenue = coerce_float(normalize_cell(row[revenue_index]))
            if revenue is None:
                continue
            revenues.append(float(revenue))
            cost = 0.0
            if cost_index is not None:
                maybe_cost = coerce_float(normalize_cell(row[cost_index]))
                cost = float(maybe_cost) if maybe_cost is not None else 0.0
            costs.append(cost)
            if date_index is not None:
                month = self._month_label(normalize_cell(row[date_index]))
                if month:
                    monthly_revenue[month] += float(revenue)

        if not revenues:
            report = self._empty_report(
                file_id=file_id,
                row_count=len(rows),
                revenue_column=revenue_column,
                cost_column=cost_column,
                date_column=date_column,
                note=f"No numeric values found in revenue column: {revenue_column}",
            )
            self._store(report)
            return report

        total_revenue = round(sum(revenues), 2)
        total_cost = round(sum(costs), 2)
        gross_margin = round(total_revenue - total_cost, 2)
        margin_pct = round((gross_margin / total_revenue) * 100, 2) if total_revenue else 0
        report = BusinessReport(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            row_count=len(rows),
            revenue_column=revenue_column,
            cost_column=cost_column,
            date_column=date_column,
            kpis=[
                KPICard(label="Total revenue", value=total_revenue, unit="currency"),
                KPICard(label="Total cost", value=total_cost, unit="currency"),
                KPICard(label="Gross margin", value=gross_margin, unit="currency"),
                KPICard(label="Margin %", value=margin_pct, unit="percent"),
                KPICard(label="Average revenue", value=round(total_revenue / len(revenues), 2)),
            ],
            revenue_by_month=[
                BusinessChartPoint(label=month, value=round(value, 2))
                for month, value in sorted(monthly_revenue.items())
            ],
            suitability_note="Business KPIs calculated successfully.",
        )
        self._store(report)
        return report

    def get_latest_for_file(self, file_id: int) -> BusinessReport:
        """Return the latest report for a file."""
        result = self._results_by_file.get(file_id)
        if result is None:
            raise BusinessAnalyticsError("Business analytics has not been run for this file")
        return result

    def get_result(self, result_id: str) -> BusinessReport:
        """Return a stored report by result id."""
        result = self._results.get(result_id)
        if result is None:
            raise BusinessAnalyticsError("Business analytics result not found")
        return result

    def _store(self, report: BusinessReport) -> None:
        self._results[report.result_id] = report
        self._results_by_file[report.file_id] = report

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise BusinessAnalyticsError("File not found")
        return file

    def _read_rows(self, file: UploadedFile) -> tuple[list[str], list[list[str]]]:
        path = Path(get_settings().upload_dir) / file.stored_path
        if not path.exists():
            raise BusinessAnalyticsError("Stored file not found")
        text = decode_csv_bytes(path.read_bytes())
        rows = list(csv.reader(StringIO(text, newline="")))
        if not rows or not rows[0]:
            raise BusinessAnalyticsError("CSV must contain a header row")
        return [header.strip() for header in rows[0]], rows[1:]

    def _infer_column(self, headers: list[str], keywords: tuple[str, ...]) -> str | None:
        for header in headers:
            normalized = header.lower().replace("_", " ")
            if any(keyword in normalized for keyword in keywords):
                return header
        return None

    def _month_label(self, value: str) -> str | None:
        if is_missing(value):
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(value, fmt)
                return f"{parsed.year}-{parsed.month:02d}"
            except ValueError:
                continue
        return value[:7] if len(value) >= 7 else value

    def _empty_report(
        self,
        *,
        file_id: int,
        row_count: int,
        note: str,
        revenue_column: str | None = None,
        cost_column: str | None = None,
        date_column: str | None = None,
    ) -> BusinessReport:
        return BusinessReport(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            row_count=row_count,
            revenue_column=revenue_column,
            cost_column=cost_column,
            date_column=date_column,
            kpis=[],
            revenue_by_month=[],
            suitability_note=note,
        )


business_analytics_service = BusinessAnalyticsService()
