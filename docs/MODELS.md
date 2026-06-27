# Models reference

This project exposes regression, classification, clustering, PCA, time series,
similarity, and plugin model families.

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
