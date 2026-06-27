"""Time series forecasting API tests."""

from fastapi.testclient import TestClient

from app.services.timeseries_service import timeseries_service


def _analyst_token(client: TestClient) -> str:
    email = "timeseries-analyst@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _upload(client: TestClient, token: str, filename: str, content: bytes) -> int:
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["file_id"]


def _sample_series() -> bytes:
    rows = ["date,sales"]
    for month in range(1, 13):
        rows.append(f"2024-{month:02d}-01,{100 + month * 5}")
    return ("\n".join(rows) + "\n").encode()


def test_timeseries_forecast_table_and_metrics(client: TestClient) -> None:
    """Forecast returns metrics, history, and future values."""
    timeseries_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(client, token, "monthly-sales.csv", _sample_series())

    response = client.post(
        f"/api/v1/models/{file_id}/timeseries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "moving_average",
            "date_column": "date",
            "value_column": "sales",
            "forecast_periods": 4,
            "window": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "timeseries"
    assert body["row_count"] == 12
    assert len(body["history"]) == 12
    assert len(body["forecast"]) == 4
    assert body["metrics"]["mae"] >= 0
    assert body["metrics"]["rmse"] >= 0


def test_timeseries_arima_and_autoregressive(client: TestClient) -> None:
    """AR and ARIMA algorithms return forecast output."""
    timeseries_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(client, token, "series.csv", _sample_series())

    for algorithm, payload in (
        ("autoregressive", {"ar_lags": 2}),
        ("arima", {"arima_p": 1, "arima_d": 1, "arima_q": 1}),
    ):
        response = client.post(
            f"/api/v1/models/{file_id}/timeseries",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "algorithm": algorithm,
                "date_column": "date",
                "value_column": "sales",
                "forecast_periods": 3,
                **payload,
            },
        )
        assert response.status_code == 200, algorithm
        assert response.json()["algorithm"] == algorithm
        assert len(response.json()["forecast"]) == 3
