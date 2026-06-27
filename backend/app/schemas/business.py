"""Business analytics schemas."""

from pydantic import BaseModel


class BusinessAnalyticsRequest(BaseModel):
    """Column mapping for business KPI analysis."""

    date_column: str | None = None
    revenue_column: str | None = None
    cost_column: str | None = None


class KPICard(BaseModel):
    """Single KPI card payload."""

    label: str
    value: float | int | str
    unit: str | None = None
    direction: str = "neutral"


class BusinessChartPoint(BaseModel):
    """Simple chart/table data point."""

    label: str
    value: float


class BusinessReport(BaseModel):
    """Business analytics report."""

    result_id: str
    file_id: int
    row_count: int
    revenue_column: str | None
    cost_column: str | None
    date_column: str | None
    kpis: list[KPICard]
    revenue_by_month: list[BusinessChartPoint]
    suitability_note: str
