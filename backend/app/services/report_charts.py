"""Render EDA chart_data for Markdown and PDF report exports."""

from __future__ import annotations

from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Flowable, Paragraph, Spacer


class DrawingFlowable(Flowable):
    """Embed a reportlab Drawing in a Platypus story."""

    def __init__(self, drawing: Drawing, width: float, height: float) -> None:
        self.drawing = drawing
        self.width = width
        self.height = height

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        self.drawing.drawOn(self.canv, 0, 0)


def eda_charts_to_markdown(chart_data: dict[str, Any]) -> list[str]:
    """Convert EDA chart_data into Markdown sections with tables and bar visuals."""
    if not chart_data:
        return []

    lines = ["", "### EDA charts", ""]
    for column_name, chart in chart_data.items():
        chart_type = chart.get("type")
        if chart_type == "histogram":
            lines.extend(_histogram_markdown(column_name, chart.get("bins", [])))
        elif chart_type == "bar":
            lines.extend(_bar_markdown(column_name, chart.get("values", [])))
    return lines


def eda_charts_to_pdf_flowables(chart_data: dict[str, Any]) -> list[Flowable]:
    """Convert EDA chart_data into PDF flowables."""
    if not chart_data:
        return []

    styles = getSampleStyleSheet()
    flowables: list[Flowable] = [
        Paragraph("EDA charts", styles["Heading3"]),
        Spacer(1, 8),
    ]

    for column_name, chart in chart_data.items():
        chart_type = chart.get("type")
        if chart_type == "histogram":
            labels, counts = _histogram_labels_counts(chart.get("bins", []))
            title = f"{column_name} (histogram)"
        elif chart_type == "bar":
            labels, counts = _bar_labels_counts(chart.get("values", []))
            title = f"{column_name} (bar chart)"
        else:
            continue

        if not labels:
            continue

        flowables.append(Paragraph(title, styles["Heading4"]))
        flowables.append(Spacer(1, 6))
        flowables.append(
            DrawingFlowable(
                _build_bar_chart_drawing(labels, counts),
                width=460,
                height=180,
            ),
        )
        flowables.append(Spacer(1, 12))

    return flowables


def _histogram_labels_counts(bins: list[dict[str, Any]]) -> tuple[list[str], list[int]]:
    labels: list[str] = []
    counts: list[int] = []
    for item in bins:
        start = item.get("start")
        end = item.get("end")
        count = int(item.get("count", 0))
        labels.append(f"{start}-{end}")
        counts.append(count)
    return labels, counts


def _bar_labels_counts(values: list[dict[str, Any]]) -> tuple[list[str], list[int]]:
    labels: list[str] = []
    counts: list[int] = []
    for item in values:
        labels.append(str(item.get("value", "")))
        counts.append(int(item.get("count", 0)))
    return labels, counts


def _histogram_markdown(column_name: str, bins: list[dict[str, Any]]) -> list[str]:
    if not bins:
        return []

    labels, counts = _histogram_labels_counts(bins)
    return _chart_table_markdown(f"{column_name} (histogram)", labels, counts)


def _bar_markdown(column_name: str, values: list[dict[str, Any]]) -> list[str]:
    if not values:
        return []

    labels, counts = _bar_labels_counts(values)
    return _chart_table_markdown(f"{column_name} (bar chart)", labels, counts)


def _chart_table_markdown(title: str, labels: list[str], counts: list[int]) -> list[str]:
    max_count = max(counts) if counts else 1
    lines = [
        f"#### {title}",
        "",
        "| Label | Count | Chart |",
        "| --- | ---: | --- |",
    ]
    for label, count in zip(labels, counts, strict=True):
        lines.append(f"| {label} | {count} | {_ascii_bar(count, max_count)} |")
    lines.append("")
    return lines


def _ascii_bar(count: int, max_count: int, width: int = 20) -> str:
    if max_count <= 0 or count <= 0:
        return ""
    filled = max(1, round((count / max_count) * width))
    return "█" * filled


def _truncate_label(label: str, max_length: int = 12) -> str:
    if len(label) <= max_length:
        return label
    return label[: max_length - 1] + "…"


def _build_bar_chart_drawing(labels: list[str], counts: list[int]) -> Drawing:
    width = 460.0
    height = 180.0
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.height = height - 60
    chart.width = width - 80
    chart.data = [counts]
    chart.categoryAxis.categoryNames = [_truncate_label(label) for label in labels]
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor("#3b82f6")
    chart.bars[0].strokeColor = colors.HexColor("#2563eb")
    chart.bars[0].strokeWidth = 0.5
    drawing.add(chart)
    return drawing
