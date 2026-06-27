"""Time series forecasting service."""

import csv
import math
import uuid
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    TimeseriesMetrics,
    TimeseriesPoint,
    TimeseriesRequest,
    TimeseriesResult,
)
from app.services.plugin_registry import (
    TimeseriesAlgorithmSpec,
    get_timeseries_algorithm,
    register_timeseries_algorithm,
)
from app.services.result_persistence_service import result_persistence_service
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import (
    coerce_float,
    is_missing,
    normalize_cell,
    parse_datetime_value,
)


class TimeseriesError(ValueError):
    """Raised when time series forecasting cannot run."""


MIN_SERIES_LENGTH = 12


@dataclass(frozen=True)
class _SeriesPoint:
    label: str
    value: float


class TimeseriesService:
    """Moving average, AR, ARIMA, and SARIMAX forecasts on uploaded CSV files."""

    def __init__(self) -> None:
        self._results: dict[str, TimeseriesResult] = {}
        self._register_builtin_algorithms()

    def clear_results(self) -> None:
        """Clear stored time series results (used in tests)."""
        self._results.clear()

    def run_forecast(
        self,
        db: Session,
        *,
        file_id: int,
        request: TimeseriesRequest,
    ) -> TimeseriesResult:
        """Fit a forecast model and return metrics plus future values."""
        get_timeseries_algorithm(request.algorithm)
        file = self._get_file(db, file_id)
        series = self._load_series(file, request.date_column, request.value_column)
        if len(series) < MIN_SERIES_LENGTH:
            raise TimeseriesError(
                f"Need at least {MIN_SERIES_LENGTH} dated rows for time series forecasting",
            )

        train_size = max(
            MIN_SERIES_LENGTH // 2,
            int(len(series) * request.train_ratio),
        )
        if train_size >= len(series) - 2:
            raise TimeseriesError("Not enough rows after train/test split")

        train = series[:train_size]
        test = series[train_size:]
        train_values = np.asarray([point.value for point in train], dtype=float)
        test_values = np.asarray([point.value for point in test], dtype=float)

        test_forecast = self._forecast_algorithm(
            request,
            train_values=train_values,
            steps=len(test_values),
        )
        metrics = self._metrics(test_values, test_forecast)

        full_values = np.asarray([point.value for point in series], dtype=float)
        future_values = self._forecast_algorithm(
            request,
            train_values=full_values,
            steps=request.forecast_periods,
        )

        history = [
            TimeseriesPoint(label=point.label, actual=point.value) for point in series
        ]
        for index, (point, predicted) in enumerate(
            zip(test, test_forecast, strict=True)
        ):
            history[train_size + index] = TimeseriesPoint(
                label=point.label,
                actual=point.value,
                forecast=round(float(predicted), 4),
            )

        forecast_points = [
            TimeseriesPoint(
                label=f"F+{index + 1}",
                forecast=round(float(value), 4),
            )
            for index, value in enumerate(future_values)
        ]

        result = TimeseriesResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            algorithm=request.algorithm,
            date_column=request.date_column,
            value_column=request.value_column,
            row_count=len(series),
            train_rows=len(train),
            test_rows=len(test),
            metrics=metrics,
            history=history,
            forecast=forecast_points,
        )
        return result_persistence_service.save_model(
            db,
            self._results,
            result,
            result_type="timeseries",
            algorithm=request.algorithm,
        )

    def get_result(self, result_id: str, db: Session | None = None) -> TimeseriesResult:
        """Return a stored time series result."""
        result = result_persistence_service.load_model(
            db,
            self._results,
            result_id,
            TimeseriesResult,
        )
        if result is None:
            raise TimeseriesError("Time series result not found")
        return result

    def _forecast_algorithm(
        self,
        request: TimeseriesRequest,
        *,
        train_values: np.ndarray,
        steps: int,
    ) -> np.ndarray:
        if request.algorithm == "moving_average":
            return self._moving_average_forecast(
                train_values,
                window=request.window,
                steps=steps,
            )
        if request.algorithm == "autoregressive":
            return self._autoregressive_forecast(
                train_values,
                lags=request.ar_lags,
                steps=steps,
            )
        if request.algorithm == "arima":
            return self._arima_forecast(
                train_values,
                order=(request.arima_p, request.arima_d, request.arima_q),
                steps=steps,
            )
        if request.algorithm == "sarimax":
            if request.seasonal_period is None:
                raise TimeseriesError("seasonal_period is required for SARIMAX")
            return self._sarimax_forecast(
                train_values,
                order=(request.arima_p, request.arima_d, request.arima_q),
                seasonal_period=request.seasonal_period,
                steps=steps,
            )
        raise TimeseriesError(f"Unsupported algorithm: {request.algorithm}")

    def _moving_average_forecast(
        self,
        values: np.ndarray,
        *,
        window: int,
        steps: int,
    ) -> np.ndarray:
        history = values.tolist()
        predictions: list[float] = []
        for _ in range(steps):
            window_values = history[-window:]
            prediction = float(np.mean(window_values))
            predictions.append(prediction)
            history.append(prediction)
        return np.asarray(predictions, dtype=float)

    def _autoregressive_forecast(
        self,
        values: np.ndarray,
        *,
        lags: int,
        steps: int,
    ) -> np.ndarray:
        effective_lags = min(lags, max(1, len(values) - 2))
        model = AutoReg(values, lags=effective_lags, old_names=False).fit()
        return np.asarray(model.forecast(steps), dtype=float)

    def _arima_forecast(
        self,
        values: np.ndarray,
        *,
        order: tuple[int, int, int],
        steps: int,
    ) -> np.ndarray:
        model = ARIMA(values, order=order).fit()
        return np.asarray(model.forecast(steps), dtype=float)

    def _sarimax_forecast(
        self,
        values: np.ndarray,
        *,
        order: tuple[int, int, int],
        seasonal_period: int,
        steps: int,
    ) -> np.ndarray:
        if len(values) < seasonal_period * 2:
            raise TimeseriesError(
                f"Need at least {seasonal_period * 2} rows for SARIMAX "
                f"with seasonal period {seasonal_period}",
            )
        model = SARIMAX(
            values,
            order=order,
            seasonal_order=(1, 0, 0, seasonal_period),
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False)
        return np.asarray(model.forecast(steps), dtype=float)

    def _metrics(self, actual: np.ndarray, predicted: np.ndarray) -> TimeseriesMetrics:
        errors = actual - predicted
        mae = round(float(np.mean(np.abs(errors))), 4)
        rmse = round(float(math.sqrt(np.mean(errors**2))), 4)
        nonzero = actual != 0
        mape = None
        if np.any(nonzero):
            mape = round(
                float(np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100),
                4,
            )
        return TimeseriesMetrics(mae=mae, rmse=rmse, mape=mape)

    def _register_builtin_algorithms(self) -> None:
        register_timeseries_algorithm(
            TimeseriesAlgorithmSpec(
                id="moving_average",
                label="Moving average",
                description="Rolling mean forecast over recent observations.",
            ),
        )
        register_timeseries_algorithm(
            TimeseriesAlgorithmSpec(
                id="autoregressive",
                label="Autoregressive (AR)",
                description="Linear autoregression on recent lags.",
            ),
        )
        register_timeseries_algorithm(
            TimeseriesAlgorithmSpec(
                id="arima",
                label="ARIMA",
                description="AutoRegressive Integrated Moving Average model.",
            ),
        )
        register_timeseries_algorithm(
            TimeseriesAlgorithmSpec(
                id="sarimax",
                label="SARIMAX",
                description="Seasonal ARIMA when a seasonal period is supplied.",
            ),
        )

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise TimeseriesError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise TimeseriesError("Stored file not found")
        return path.read_bytes()

    def _load_series(
        self,
        file: UploadedFile,
        date_column: str,
        value_column: str,
    ) -> list[_SeriesPoint]:
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        reader = csv.reader(StringIO(text, newline=""))
        rows = list(reader)
        if not rows or not rows[0]:
            raise TimeseriesError("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        if date_column not in headers:
            raise TimeseriesError(f"Date column not found: {date_column}")
        if value_column not in headers:
            raise TimeseriesError(f"Value column not found: {value_column}")

        date_index = headers.index(date_column)
        value_index = headers.index(value_column)
        points: list[_SeriesPoint] = []

        for _row_number, row in enumerate(rows[1:], start=1):
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            date_text = normalize_cell(row[date_index])
            value_text = normalize_cell(row[value_index])
            if is_missing(date_text) or is_missing(value_text):
                continue
            parsed_date = parse_datetime_value(date_text)
            value = coerce_float(value_text)
            if value is None:
                continue
            label = parsed_date.date().isoformat() if parsed_date else date_text
            points.append(_SeriesPoint(label=label, value=value))

        if not points:
            raise TimeseriesError("No valid dated numeric rows found")

        points.sort(key=lambda point: point.label)
        return points


timeseries_service = TimeseriesService()
