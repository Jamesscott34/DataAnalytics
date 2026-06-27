# Models reference

This project exposes regression, classification, clustering, PCA, time series,
similarity, and plugin model families.

## Analytics plugins

Built-in plugins are registered in `app/services/analytics_plugins.py` and exposed at:

- `GET /api/v1/plugins?file_id=` — list plugins with applicability for a dataset
- `POST /api/v1/plugins/{name}/run` — run anomaly, churn, fraud, or demand plugins

| Plugin | Purpose |
| --- | --- |
| `anomaly_detection` | Isolation forest on numeric columns |
| `customer_churn` | Logistic regression on a categorical label |
| `fraud_detection` | Z-score outlier scoring |
| `demand_forecast` | Moving-average forecast from date + value columns |

Plugins with unmet column requirements return `applicable: false` in list responses.

## Explainability

Explainability is intentionally lightweight in the local build:

| Model family | Explanation shown | SHAP support |
| --- | --- | --- |
| Regression: linear | Absolute coefficients as feature importance | Fallback only |
| Regression: decision tree/random forest | Tree impurity feature importance | Fallback only |
| Regression: polynomial | Expanded linear coefficients where available | Fallback only |
| Classification | Prediction confidence summaries when probabilities are available | Fallback only |
| Clustering/PCA/time series/similarity | Method-specific diagnostics in result views | Not applicable |

`GET /api/v1/explainability/{result_id}` returns feature importance,
confidence summaries, and plain-English fallback notes for supported stored
results. `POST /api/v1/explainability/{result_id}/shap` returns a structured
fallback response when SHAP values are not available.
