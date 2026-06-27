"""Business KPI analytics service."""

import uuid
from collections import Counter, defaultdict
from datetime import datetime
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
from app.services.result_persistence_service import result_persistence_service
from app.utils.csv_parse_utils import parse_csv_rows
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell

MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class BusinessAnalyticsError(ValueError):
    """Raised when business analytics cannot access a dataset."""


class BusinessAnalyticsService:
    """Compute pest-control and general business KPIs from uploaded CSV files."""

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
        headers, rows, _ = self._read_rows(file)
        revenue_column = request.revenue_column or self._infer_column(
            headers,
            ("revenue", "sales", "amount", "price", "total", "invoice"),
        )
        cost_column = request.cost_column or self._infer_column(
            headers,
            ("cost", "expense", "spend", "material_cost", "labor_cost"),
        )
        date_column = request.date_column or self._infer_column(
            headers,
            ("date", "month", "job_date", "service_date"),
        )
        technician_column = request.technician_column or self._infer_column(
            headers,
            ("technician", "tech", "employee", "staff"),
        )
        pest_column = request.pest_column or self._infer_column(
            headers,
            ("pest", "pest_type", "service_type", "category"),
        )
        location_column = request.location_column or self._infer_column(
            headers,
            ("location", "region", "customer_region", "area", "city"),
        )
        customer_column = request.customer_column or self._infer_column(
            headers,
            ("customer", "client", "account", "customer_id"),
        )
        service_column = request.service_column or pest_column

        if revenue_column is None:
            report = self._empty_report(
                file_id=file_id,
                row_count=len(rows),
                note="Business analytics needs a numeric revenue, sales, amount, or price column.",
            )
            return self._store(db, report)

        indexes = {name: index for index, name in enumerate(headers)}
        revenue_index = indexes[revenue_column]
        cost_index = indexes.get(cost_column) if cost_column else None
        date_index = indexes.get(date_column) if date_column else None
        technician_index = indexes.get(technician_column) if technician_column else None
        pest_index = indexes.get(pest_column) if pest_column else None
        location_index = indexes.get(location_column) if location_column else None
        customer_index = indexes.get(customer_column) if customer_column else None
        service_index = indexes.get(service_column) if service_column else None

        revenues: list[float] = []
        costs: list[float] = []
        monthly_revenue: dict[str, float] = defaultdict(float)
        yearly_revenue: dict[str, float] = defaultdict(float)
        named_month_revenue: dict[str, float] = defaultdict(float)
        technician_jobs: Counter[str] = Counter()
        pest_jobs: Counter[str] = Counter()
        location_jobs: Counter[str] = Counter()
        service_revenue: dict[str, float] = defaultdict(float)
        customers: list[str] = []
        january_sales = 0.0

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
                parsed = self._parse_date(normalize_cell(row[date_index]))
                if parsed is not None:
                    month_key = f"{parsed.year}-{parsed.month:02d}"
                    monthly_revenue[month_key] += float(revenue)
                    yearly_revenue[str(parsed.year)] += float(revenue)
                    month_name = MONTH_NAMES[parsed.month - 1]
                    named_month_revenue[month_name] += float(revenue)
                    if parsed.month == 1:
                        january_sales += float(revenue)

            if technician_index is not None:
                tech = normalize_cell(row[technician_index])
                if not is_missing(tech):
                    technician_jobs[tech] += 1
            if pest_index is not None:
                pest = normalize_cell(row[pest_index])
                if not is_missing(pest):
                    pest_jobs[pest] += 1
            if location_index is not None:
                location = normalize_cell(row[location_index])
                if not is_missing(location):
                    location_jobs[location] += 1
            if service_index is not None:
                service = normalize_cell(row[service_index])
                if not is_missing(service):
                    service_revenue[service] += float(revenue)
            if customer_index is not None:
                customer = normalize_cell(row[customer_index])
                if not is_missing(customer):
                    customers.append(customer)

        if not revenues:
            report = self._empty_report(
                file_id=file_id,
                row_count=len(rows),
                revenue_column=revenue_column,
                cost_column=cost_column,
                date_column=date_column,
                note=f"No numeric values found in revenue column: {revenue_column}",
            )
            return self._store(db, report)

        total_revenue = round(sum(revenues), 2)
        total_cost = round(sum(costs), 2)
        gross_margin = round(total_revenue - total_cost, 2)
        margin_pct = (
            round((gross_margin / total_revenue) * 100, 2) if total_revenue else 0
        )
        total_jobs = len(revenues)
        average_job_value = round(total_revenue / total_jobs, 2)
        repeat_customers = self._repeat_customer_count(customers)
        busiest_month = self._busiest_month(monthly_revenue)
        best_service = self._best_service(service_revenue)
        mom_growth = self._month_over_month_growth(monthly_revenue)
        next_forecast = self._next_month_forecast(monthly_revenue)

        sorted_months = sorted(monthly_revenue.items())
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
                KPICard(label="Profit", value=gross_margin, unit="currency"),
                KPICard(label="Margin %", value=margin_pct, unit="percent"),
                KPICard(label="Profit margin %", value=margin_pct, unit="percent"),
                KPICard(
                    label="Average revenue",
                    value=round(total_revenue / len(revenues), 2),
                ),
                KPICard(
                    label="Average job value", value=average_job_value, unit="currency"
                ),
                KPICard(label="Total jobs", value=total_jobs),
                KPICard(
                    label="January sales",
                    value=round(january_sales, 2),
                    unit="currency",
                ),
                KPICard(label="Repeat customers", value=repeat_customers),
                KPICard(label="Busiest month", value=busiest_month or "n/a"),
                KPICard(label="Best performing service", value=best_service or "n/a"),
                KPICard(
                    label="Month-over-month growth",
                    value=round(mom_growth, 2) if mom_growth is not None else "n/a",
                    unit="percent" if mom_growth is not None else None,
                ),
                KPICard(
                    label="Next month forecast",
                    value=(
                        round(next_forecast, 2) if next_forecast is not None else "n/a"
                    ),
                    unit="currency" if next_forecast is not None else None,
                ),
            ],
            revenue_by_month=[
                BusinessChartPoint(label=month, value=round(value, 2))
                for month, value in sorted_months
            ],
            yearly_revenue=[
                BusinessChartPoint(label=year, value=round(value, 2))
                for year, value in sorted(yearly_revenue.items())
            ],
            sales_by_month_named=[
                BusinessChartPoint(
                    label=month, value=round(named_month_revenue[month], 2)
                )
                for month in MONTH_NAMES
                if month in named_month_revenue
            ],
            jobs_by_technician=self._counter_to_points(technician_jobs),
            jobs_by_pest=self._counter_to_points(pest_jobs),
            jobs_by_location=self._counter_to_points(location_jobs),
            suitability_note="Business KPIs calculated successfully.",
        )
        return self._store(db, report)

    def get_latest_for_file(
        self, file_id: int, db: Session | None = None
    ) -> BusinessReport:
        """Return the latest report for a file."""
        result = self._results_by_file.get(file_id)
        if result is not None:
            return result
        if db is not None:
            records = result_persistence_service.list_for_file(
                db,
                file_id=file_id,
                result_type="business",
                limit=1,
            )
            if records:
                restored = BusinessReport.model_validate(records[0].payload)
                self._cache(restored)
                return restored
        raise BusinessAnalyticsError(
            "Business analytics has not been run for this file"
        )

    def get_result(self, result_id: str, db: Session | None = None) -> BusinessReport:
        """Return a stored report by result id."""
        result = result_persistence_service.load_model(
            db,
            self._results,
            result_id,
            BusinessReport,
        )
        if result is None:
            raise BusinessAnalyticsError("Business analytics result not found")
        return result

    def _store(self, db: Session, report: BusinessReport) -> BusinessReport:
        self._cache(report)
        return result_persistence_service.save_model(
            db,
            self._results,
            report,
            result_type="business",
        )

    def _cache(self, report: BusinessReport) -> None:
        self._results[report.result_id] = report
        self._results_by_file[report.file_id] = report

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise BusinessAnalyticsError("File not found")
        return file

    def _read_rows(
        self, file: UploadedFile
    ) -> tuple[list[str], list[list[str]], list[str]]:
        path = Path(get_settings().upload_dir) / file.stored_path
        if not path.exists():
            raise BusinessAnalyticsError("Stored file not found")
        text = decode_csv_bytes(path.read_bytes())
        return parse_csv_rows(text)

    def _infer_column(
        self, headers: list[str], keywords: tuple[str, ...]
    ) -> str | None:
        for header in headers:
            normalized = header.lower().replace("_", " ")
            if any(keyword in normalized for keyword in keywords):
                return header
        return None

    def _parse_date(self, value: str) -> datetime | None:
        if is_missing(value):
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _repeat_customer_count(self, customers: list[str]) -> int:
        counts = Counter(customers)
        return sum(1 for count in counts.values() if count > 1)

    def _busiest_month(self, monthly_revenue: dict[str, float]) -> str | None:
        if not monthly_revenue:
            return None
        month_key, _ = max(monthly_revenue.items(), key=lambda item: item[1])
        try:
            year, month = month_key.split("-")
            return f"{MONTH_NAMES[int(month) - 1]} {year}"
        except (ValueError, IndexError):
            return month_key

    def _best_service(self, service_revenue: dict[str, float]) -> str | None:
        if not service_revenue:
            return None
        service, revenue = max(service_revenue.items(), key=lambda item: item[1])
        return f"{service} ({round(revenue, 2)})"

    def _month_over_month_growth(
        self, monthly_revenue: dict[str, float]
    ) -> float | None:
        if len(monthly_revenue) < 2:
            return None
        sorted_months = sorted(monthly_revenue.items())
        previous = sorted_months[-2][1]
        current = sorted_months[-1][1]
        if previous == 0:
            return None
        return round(((current - previous) / previous) * 100, 2)

    def _next_month_forecast(self, monthly_revenue: dict[str, float]) -> float | None:
        if len(monthly_revenue) < 2:
            return None
        sorted_values = [value for _, value in sorted(monthly_revenue.items())]
        return sorted_values[-1] + (sorted_values[-1] - sorted_values[-2])

    def _counter_to_points(self, counter: Counter[str]) -> list[BusinessChartPoint]:
        return [
            BusinessChartPoint(label=label, value=float(count))
            for label, count in counter.most_common(10)
        ]

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
