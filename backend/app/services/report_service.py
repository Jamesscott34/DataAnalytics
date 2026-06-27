"""Report generation service for Markdown and PDF exports."""

import csv
import json
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.quick_scan import QuickScanReport
from app.services.report_charts import (
    eda_charts_to_markdown,
    eda_charts_to_pdf_flowables,
)


class ReportService:
    """Builds downloadable analysis reports from quick-scan bundles."""

    def to_json(self, report: QuickScanReport) -> str:
        """Render a quick-scan report as indented JSON."""
        return json.dumps(report.model_dump(mode="json"), indent=2)

    def to_csv(self, report: QuickScanReport) -> str:
        """Render a quick-scan report as key/value CSV rows."""
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "name", "value"])
        writer.writerow(["file", "filename", report.filename])
        writer.writerow(["file", "file_id", report.file_id])
        writer.writerow(["file", "rows", report.row_count])
        writer.writerow(["file", "columns", report.column_count])
        writer.writerow(["file", "sha256", report.file_hash])
        for step in report.steps:
            writer.writerow(["scan_step", step.step, step.status])
        if report.eda:
            summary = report.eda.summary
            writer.writerow(["eda", "missing_cells", summary.missing_cells])
            writer.writerow(["eda", "missing_percent", summary.missing_percent])
            writer.writerow(["eda", "duplicate_rows", summary.duplicate_row_count])
            for column in report.eda.columns:
                writer.writerow(["eda_column", column.name, column.inferred_type])
        if report.regression:
            writer.writerow(["regression", "algorithm", report.regression.algorithm])
            writer.writerow(["regression", "target", report.regression.target_column])
            writer.writerow(["regression", "mae", report.regression.metrics.mae])
            writer.writerow(["regression", "rmse", report.regression.metrics.rmse])
            writer.writerow(["regression", "r2", report.regression.metrics.r2])
        if report.classification:
            writer.writerow(
                ["classification", "algorithm", report.classification.algorithm]
            )
            writer.writerow(
                ["classification", "target", report.classification.target_column]
            )
            writer.writerow(
                ["classification", "accuracy", report.classification.metrics.accuracy]
            )
            writer.writerow(["classification", "f1", report.classification.metrics.f1])
        return buffer.getvalue()

    def to_markdown(self, report: QuickScanReport) -> str:
        """Render a quick-scan report as Markdown."""
        lines = [
            f"# Analysis Report: {report.filename}",
            "",
            f"- **File ID:** {report.file_id}",
            f"- **Generated:** {report.generated_at.isoformat()}",
            f"- **Rows:** {report.row_count}",
            f"- **Columns:** {report.column_count}",
            f"- **SHA-256:** `{report.file_hash}`",
            "",
            "## Scan steps",
            "",
            "| Step | Status | Details |",
            "| --- | --- | --- |",
        ]
        for step in report.steps:
            lines.append(
                f"| {step.step} | {step.status} | {step.message or ''} |",
            )

        if report.security_scan:
            lines.extend(
                [
                    "",
                    "## Security scan",
                    "",
                    f"- **Status:** {report.security_scan.status}",
                    f"- **Risk score:** {report.security_scan.risk_score}/100",
                    f"- **Action:** {report.security_scan.recommended_action}",
                ],
            )
            if report.security_scan.issues:
                lines.append("- **Issues:**")
                lines.extend(f"  - {issue}" for issue in report.security_scan.issues)

        if report.eda:
            summary = report.eda.summary
            lines.extend(
                [
                    "",
                    "## Exploratory data analysis",
                    "",
                    f"- **Rows:** {summary.row_count}",
                    f"- **Columns:** {summary.column_count}",
                    f"- **Missing cells:** {summary.missing_cells} ({summary.missing_percent:.1f}%)",
                    f"- **Duplicate rows:** {summary.duplicate_row_count}",
                    "",
                    "### Columns",
                    "",
                    "| Column | Type | Missing % | Unique |",
                    "| --- | --- | --- | --- |",
                ],
            )
            for column in report.eda.columns:
                lines.append(
                    f"| {column.name} | {column.inferred_type} | "
                    f"{column.missing_percent:.1f} | {column.unique_count} |",
                )
            if report.eda.quality_warnings:
                lines.extend(["", "### Quality warnings", ""])
                lines.extend(f"- {warning}" for warning in report.eda.quality_warnings)
            lines.extend(eda_charts_to_markdown(report.eda.chart_data))

        if report.suggestions:
            lines.extend(
                [
                    "",
                    "## Suggested analyses",
                    "",
                    f"- **Targets:** {', '.join(report.suggestions.target_columns) or '—'}",
                    f"- **Features:** {', '.join(report.suggestions.feature_columns) or '—'}",
                    f"- **Suggested:** {', '.join(report.suggestions.suggested_analyses) or '—'}",
                ],
            )

        if report.sql_import:
            lines.extend(
                [
                    "",
                    "## SQL import",
                    "",
                    f"- **Table:** `{report.sql_import.table_name}`",
                    f"- **Imported rows:** {report.sql_import.imported_rows}",
                    f"- **Columns:** {', '.join(report.sql_import.columns)}",
                ],
            )

        if report.regression:
            regression_metrics = report.regression.metrics
            lines.extend(
                [
                    "",
                    "## Regression",
                    "",
                    f"- **Algorithm:** {report.regression.algorithm}",
                    f"- **Target:** {report.regression.target_column}",
                    f"- **Features:** {', '.join(report.regression.feature_columns)}",
                    f"- **MAE:** {regression_metrics.mae}",
                    f"- **RMSE:** {regression_metrics.rmse}",
                    f"- **R²:** {regression_metrics.r2}",
                    "",
                    "### Actual vs predicted (test set)",
                    "",
                    "| Actual | Predicted |",
                    "| --- | --- |",
                ],
            )
            for row in report.regression.actual_vs_predicted[:20]:
                lines.append(f"| {row.actual} | {row.predicted} |")

        if report.classification:
            classification_metrics = report.classification.metrics
            lines.extend(
                [
                    "",
                    "## Classification",
                    "",
                    f"- **Algorithm:** {report.classification.algorithm}",
                    f"- **Target:** {report.classification.target_column}",
                    f"- **Features:** {', '.join(report.classification.feature_columns)}",
                    f"- **Accuracy:** {classification_metrics.accuracy}",
                    f"- **Precision:** {classification_metrics.precision}",
                    f"- **Recall:** {classification_metrics.recall}",
                    f"- **F1:** {classification_metrics.f1}",
                    "",
                    "### Confusion matrix",
                    "",
                ],
            )
            labels = report.classification.confusion_matrix.labels
            confusion = report.classification.confusion_matrix
            if confusion.included and labels:
                header = "| Actual \\\\ Predicted | " + " | ".join(labels) + " |"
                separator = "| --- | " + " | ".join("---" for _ in labels) + " |"
                lines.extend([header, separator])
                for label, matrix_row in zip(
                    labels,
                    confusion.matrix,
                    strict=True,
                ):
                    lines.append(
                        f"| {label} | "
                        + " | ".join(str(value) for value in matrix_row)
                        + " |",
                    )
            else:
                lines.append(
                    confusion.message
                    or (
                        f"Confusion matrix omitted "
                        f"({confusion.class_count} classes — too many to display)."
                    ),
                )
            if report.classification.classification_report:
                lines.extend(
                    [
                        "",
                        "### Per-class report",
                        "",
                        "| Class | Precision | Recall | F1 | Support |",
                        "| --- | --- | --- | --- | --- |",
                    ],
                )
                for class_row in report.classification.classification_report:
                    lines.append(
                        f"| {class_row.label} | {class_row.precision} | {class_row.recall} | "
                        f"{class_row.f1} | {class_row.support} |",
                    )

        if report.notes:
            lines.extend(["", "## Notes", ""])
            lines.extend(f"- {note}" for note in report.notes)

        lines.append("")
        return "\n".join(lines)

    def to_pdf(self, report: QuickScanReport) -> bytes:
        """Render a quick-scan report as PDF bytes."""
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        from reportlab.platypus import Flowable

        story: list[Flowable] = []

        story.append(Paragraph(f"Analysis Report: {report.filename}", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(
            Paragraph(
                f"Generated {report.generated_at.isoformat()} · "
                f"{report.row_count} rows · {report.column_count} columns",
                styles["Normal"],
            ),
        )
        story.append(Spacer(1, 16))

        story.append(Paragraph("Scan steps", styles["Heading2"]))
        step_rows = [["Step", "Status", "Details"]]
        for step in report.steps:
            step_rows.append([step.step, step.status, step.message or ""])
        step_table = Table(step_rows, repeatRows=1)
        step_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ],
            ),
        )
        story.append(step_table)
        story.append(Spacer(1, 16))

        if report.security_scan:
            story.append(Paragraph("Security scan", styles["Heading2"]))
            story.append(
                Paragraph(
                    f"Status: {report.security_scan.status} · "
                    f"Risk: {report.security_scan.risk_score}/100",
                    styles["Normal"],
                ),
            )
            story.append(Spacer(1, 12))

        if report.eda:
            story.append(Paragraph("Exploratory data analysis", styles["Heading2"]))
            summary = report.eda.summary
            story.append(
                Paragraph(
                    f"Missing: {summary.missing_percent:.1f}% · "
                    f"Duplicates: {summary.duplicate_row_count}",
                    styles["Normal"],
                ),
            )
            column_rows = [["Column", "Type", "Missing %", "Unique"]]
            for column in report.eda.columns[:15]:
                column_rows.append(
                    [
                        column.name,
                        column.inferred_type,
                        f"{column.missing_percent:.1f}",
                        str(column.unique_count),
                    ],
                )
            column_table = Table(column_rows, repeatRows=1)
            column_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ],
                ),
            )
            story.append(column_table)
            story.extend(eda_charts_to_pdf_flowables(report.eda.chart_data))
            story.append(Spacer(1, 16))

        if report.regression:
            regression_metrics = report.regression.metrics
            story.append(Paragraph("Regression", styles["Heading2"]))
            story.append(
                Paragraph(
                    f"{report.regression.algorithm} · target {report.regression.target_column} · "
                    f"MAE {regression_metrics.mae} · RMSE {regression_metrics.rmse} · "
                    f"R² {regression_metrics.r2}",
                    styles["Normal"],
                ),
            )
            story.append(Spacer(1, 12))

        if report.classification:
            classification_metrics = report.classification.metrics
            story.append(Paragraph("Classification", styles["Heading2"]))
            story.append(
                Paragraph(
                    f"{report.classification.algorithm} · target "
                    f"{report.classification.target_column} · "
                    f"Accuracy {classification_metrics.accuracy} · "
                    f"F1 {classification_metrics.f1}",
                    styles["Normal"],
                ),
            )
            story.append(Spacer(1, 12))

        document.build(story)
        return buffer.getvalue()


report_service = ReportService()
