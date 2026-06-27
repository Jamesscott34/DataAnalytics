"""Tests for EDA chart rendering in exported reports."""

from datetime import UTC, datetime

from app.schemas.eda import ColumnSummary, EDAResponse, EDASummary, NumericStats
from app.schemas.quick_scan import QuickScanReport
from app.services.report_charts import (
    eda_charts_to_markdown,
    eda_charts_to_pdf_flowables,
)
from app.services.report_service import report_service


def test_eda_charts_to_markdown_includes_histogram_and_bar() -> None:
    """Markdown export includes chart tables with ASCII bars."""
    chart_data = {
        "units": {
            "type": "histogram",
            "bins": [
                {"start": 8, "end": 10, "count": 2},
                {"start": 10, "end": 12, "count": 4},
            ],
        },
        "region": {
            "type": "bar",
            "values": [
                {"value": "North", "count": 2},
                {"value": "South", "count": 2},
            ],
        },
    }

    markdown = "\n".join(eda_charts_to_markdown(chart_data))
    assert "### EDA charts" in markdown
    assert "units (histogram)" in markdown
    assert "region (bar chart)" in markdown
    assert "█" in markdown
    assert "| North | 2 |" in markdown


def test_eda_charts_to_pdf_flowables_builds_without_error() -> None:
    """PDF chart flowables can be constructed for histogram and bar data."""
    chart_data = {
        "revenue": {
            "type": "histogram",
            "bins": [{"start": 70, "end": 100, "count": 4}],
        },
    }
    flowables = eda_charts_to_pdf_flowables(chart_data)
    assert len(flowables) >= 2


def test_report_markdown_and_pdf_include_eda_charts() -> None:
    """Full report export includes EDA chart sections."""
    eda = EDAResponse(
        summary=EDASummary(
            row_count=8,
            column_count=2,
            duplicate_row_count=0,
            missing_cells=0,
            missing_percent=0.0,
            file_hash="a" * 64,
        ),
        columns=[
            ColumnSummary(
                name="units",
                inferred_type="integer",
                missing_count=0,
                missing_percent=0.0,
                unique_count=5,
                sample_values=["10"],
                numeric_stats=NumericStats(min=8, max=15),
            ),
        ],
        quality_warnings=[],
        chart_data={
            "units": {
                "type": "histogram",
                "bins": [{"start": 8, "end": 12, "count": 8}],
            },
        },
        analyzed_at=datetime.now(UTC),
    )
    report = QuickScanReport(
        report_id="test-report",
        file_id=1,
        filename="sample.csv",
        row_count=8,
        column_count=2,
        file_hash="a" * 64,
        generated_at=datetime.now(UTC),
        steps=[],
        eda=eda,
    )

    markdown = report_service.to_markdown(report)
    assert "### EDA charts" in markdown
    assert "units (histogram)" in markdown

    pdf_bytes = report_service.to_pdf(report)
    assert pdf_bytes.startswith(b"%PDF")
