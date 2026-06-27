"""Built-in analytics plugins: anomaly, churn, fraud, demand."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.plugins import PluginInfo, PluginRunResponse
from app.utils.encoding_utils import decode_csv_bytes


class PluginError(ValueError):
    """Raised when a plugin cannot run."""


@dataclass(frozen=True)
class AnalyticsPluginSpec:
    """Metadata and runner for an analytics plugin."""

    name: str
    display_name: str
    description: str
    min_numeric_columns: int = 1
    requires_label: bool = False
    requires_date: bool = False
    runner: Callable[[Session, int, dict[str, Any]], PluginRunResponse] | None = None


ANALYTICS_PLUGINS: dict[str, AnalyticsPluginSpec] = {}
_PLUGIN_RESULTS: dict[str, PluginRunResponse] = {}


def register_analytics_plugin(spec: AnalyticsPluginSpec) -> None:
    """Register a built-in analytics plugin."""
    ANALYTICS_PLUGINS[spec.name] = spec


def list_plugin_specs() -> list[PluginInfo]:
    """Return plugin metadata without file applicability checks."""
    return [
        PluginInfo(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            applicable=True,
        )
        for spec in ANALYTICS_PLUGINS.values()
    ]


def list_plugins(db: Session, *, file_id: int | None = None) -> list[PluginInfo]:
    """Return plugins with applicability when file_id is provided."""
    profile = _column_profile(db, file_id) if file_id is not None else None
    return [
        _plugin_info(spec, profile)
        for spec in ANALYTICS_PLUGINS.values()
    ]


def get_plugin(name: str) -> AnalyticsPluginSpec:
    """Look up a plugin by name."""
    spec = ANALYTICS_PLUGINS.get(name)
    if spec is None:
        raise PluginError(f"Unknown plugin: {name}")
    return spec


def run_plugin(
    db: Session,
    *,
    plugin_name: str,
    file_id: int,
    params: dict[str, Any],
) -> PluginRunResponse:
    """Execute a plugin and store the result."""
    spec = get_plugin(plugin_name)
    if spec.runner is None:
        raise PluginError(f"Plugin {plugin_name} has no runner")
    info = _plugin_info(spec, _column_profile(db, file_id))
    if not info.applicable:
        raise PluginError(info.reason or f"Plugin {plugin_name} is not applicable")
    result = spec.runner(db, file_id, params)
    _PLUGIN_RESULTS[result.result_id] = result
    return result


def get_plugin_result(result_id: str) -> PluginRunResponse:
    """Return a stored plugin result."""
    result = _PLUGIN_RESULTS.get(result_id)
    if result is None:
        raise PluginError("Plugin result not found")
    return result


def clear_plugin_results() -> None:
    """Clear stored plugin results (tests)."""
    _PLUGIN_RESULTS.clear()


def _plugin_info(
    spec: AnalyticsPluginSpec,
    profile: tuple[list[str], list[str], list[str]] | None,
) -> PluginInfo:
    if profile is None:
        return PluginInfo(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            applicable=True,
        )
    numeric, labels, dates = profile
    if len(numeric) < spec.min_numeric_columns:
        return PluginInfo(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            applicable=False,
            reason=f"Needs at least {spec.min_numeric_columns} numeric column(s).",
        )
    if spec.requires_label and not labels:
        return PluginInfo(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            applicable=False,
            reason="Needs a categorical label column.",
        )
    if spec.requires_date and not dates:
        return PluginInfo(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            applicable=False,
            reason="Needs a date or time column.",
        )
    return PluginInfo(
        name=spec.name,
        display_name=spec.display_name,
        description=spec.description,
        applicable=True,
    )


def _load_frame(db: Session, file_id: int) -> pd.DataFrame:
    file = db.get(UploadedFile, file_id)
    if file is None:
        raise PluginError("File not found")
    path = Path(get_settings().upload_dir) / file.stored_path
    text = decode_csv_bytes(path.read_bytes())
    return pd.read_csv(StringIO(text))


def _load_columns(db: Session, file_id: int) -> list[str]:
    return list(_load_frame(db, file_id).columns)


def _column_profile(db: Session, file_id: int) -> tuple[list[str], list[str], list[str]]:
    frame = _load_frame(db, file_id)
    numeric = list(frame.select_dtypes(include="number").columns)
    labels = [
        column
        for column in frame.columns
        if column not in numeric
        and (any(hint in column.lower() for hint in _LABEL_HINTS) or frame[column].nunique() <= 12)
    ]
    dates = [
        column
        for column in frame.columns
        if any(hint in column.lower() for hint in _DATE_HINTS)
    ]
    return numeric, labels, dates


_DATE_HINTS = {"date", "time", "month", "year", "period", "day"}
_LABEL_HINTS = {"label", "churn", "fraud", "class", "target", "status", "category"}


def _run_anomaly(db: Session, file_id: int, params: dict[str, Any]) -> PluginRunResponse:
    frame = _load_frame(db, file_id)
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        raise PluginError("No numeric columns for anomaly detection")
    model = IsolationForest(random_state=42, contamination=0.1)
    scores = model.fit_predict(numeric.fillna(0))
    anomaly_count = int((scores == -1).sum())
    return PluginRunResponse(
        plugin_name="anomaly_detection",
        file_id=file_id,
        result_id=str(uuid.uuid4()),
        summary=f"Detected {anomaly_count} anomalous rows of {len(frame)}.",
        metrics={"anomaly_count": anomaly_count, "row_count": len(frame)},
    )


def _run_churn(db: Session, file_id: int, params: dict[str, Any]) -> PluginRunResponse:
    frame = _load_frame(db, file_id)
    label_col = params.get("label_column") or _pick_label(frame)
    if label_col is None:
        raise PluginError("No label column found for churn analysis")
    features = frame.select_dtypes(include="number").drop(columns=[label_col], errors="ignore")
    if features.shape[1] == 0:
        raise PluginError("No numeric feature columns for churn model")
    y = frame[label_col].astype(str)
    if y.nunique() < 2:
        raise PluginError("Label column must have at least two classes")
    model = LogisticRegression(max_iter=500)
    model.fit(features.fillna(0), y)
    accuracy = float(model.score(features.fillna(0), y))
    return PluginRunResponse(
        plugin_name="customer_churn",
        file_id=file_id,
        result_id=str(uuid.uuid4()),
        summary=f"Churn classifier trained on {label_col} with accuracy {accuracy:.3f}.",
        metrics={"accuracy": round(accuracy, 4), "label_column": label_col},
    )


def _run_fraud(db: Session, file_id: int, params: dict[str, Any]) -> PluginRunResponse:
    frame = _load_frame(db, file_id)
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        raise PluginError("No numeric columns for fraud scoring")
    z_scores = np.abs((numeric - numeric.mean()) / numeric.std(ddof=0).replace(0, 1))
    flagged = int((z_scores.max(axis=1) > 3).sum())
    return PluginRunResponse(
        plugin_name="fraud_detection",
        file_id=file_id,
        result_id=str(uuid.uuid4()),
        summary=f"Flagged {flagged} high-risk rows using z-score thresholds.",
        metrics={"flagged_rows": flagged, "row_count": len(frame)},
    )


def _run_demand(db: Session, file_id: int, params: dict[str, Any]) -> PluginRunResponse:
    frame = _load_frame(db, file_id)
    date_col = params.get("date_column") or next(
        (column for column in frame.columns if any(h in column.lower() for h in _DATE_HINTS)),
        None,
    )
    value_col = params.get("value_column") or next(
        (column for column in frame.select_dtypes(include="number").columns),
        None,
    )
    if date_col is None or value_col is None:
        raise PluginError("Need date and numeric value columns for demand forecast")
    series = pd.to_numeric(frame[value_col], errors="coerce").dropna()
    if len(series) < 3:
        raise PluginError("Need at least 3 observations for demand forecast")
    forecast = float(series.tail(3).mean())
    return PluginRunResponse(
        plugin_name="demand_forecast",
        file_id=file_id,
        result_id=str(uuid.uuid4()),
        summary=f"3-period moving average forecast for {value_col}: {forecast:.2f}.",
        metrics={
            "date_column": date_col,
            "value_column": value_col,
            "forecast": round(forecast, 4),
        },
    )


def _pick_label(frame: pd.DataFrame) -> str | None:
    for column in frame.columns:
        if any(hint in column.lower() for hint in _LABEL_HINTS):
            return column
    for column in frame.columns:
        if frame[column].dtype == object and frame[column].nunique() <= 12:
            return column
    return None


def _register_builtins() -> None:
    register_analytics_plugin(
        AnalyticsPluginSpec(
            name="anomaly_detection",
            display_name="Anomaly detection",
            description="Isolation forest over numeric columns.",
            min_numeric_columns=1,
            runner=_run_anomaly,
        ),
    )
    register_analytics_plugin(
        AnalyticsPluginSpec(
            name="customer_churn",
            display_name="Customer churn",
            description="Logistic regression on a categorical churn label.",
            min_numeric_columns=1,
            requires_label=True,
            runner=_run_churn,
        ),
    )
    register_analytics_plugin(
        AnalyticsPluginSpec(
            name="fraud_detection",
            display_name="Fraud detection",
            description="Z-score outlier scoring on numeric transaction fields.",
            min_numeric_columns=1,
            runner=_run_fraud,
        ),
    )
    register_analytics_plugin(
        AnalyticsPluginSpec(
            name="demand_forecast",
            display_name="Demand forecast",
            description="Simple moving-average demand forecast.",
            min_numeric_columns=1,
            requires_date=True,
            runner=_run_demand,
        ),
    )


_register_builtins()
