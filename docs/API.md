# API design — predictive-security-analytics-lab

> Phase 0 planning document (0.2). All routes prefixed with `/api/v1/`.

## Conventions

- **Auth**: `Authorization: Bearer <access_token>` unless marked Public.
- **Errors**: `{ "error": "<type>", "message": "<detail>", "status_code": <int> }`
- **Pagination**: `?page=1&page_size=50` (default 50, max 200) on list/tabular endpoints.
- **Rate limits** (slowapi): upload 10/min; analysis start 20/min; auth login 5/min per IP.
- **Roles**: Admin, Analyst, Viewer — see RBAC column.

---

## Authentication

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/auth/register` | `{ "email", "password", "full_name?" }` | `UserRead` | Public; Admin-only when `ALLOW_PUBLIC_REGISTRATION=false` |
| POST | `/auth/login` | `{ "email", "password" }` | `TokenResponse` `{ access_token, refresh_token, token_type, expires_in }` | Public; 5/min |
| POST | `/auth/refresh` | `{ "refresh_token" }` | `TokenResponse` | Public; validates refresh in `user_sessions` |
| POST | `/auth/logout` | `{ "refresh_token?" }` | `{ "message": "logged out" }` | Authenticated; revokes session |
| GET | `/auth/me` | — | `UserRead` | Authenticated |

---

## Monitoring (Public)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/monitoring/health` | — | `HealthResponse` `{ status, version, database, disk_free_mb, timestamp }` | Public |
| GET | `/monitoring/metrics` | — | `MetricsResponse` `{ request_count, avg_response_ms, error_rate, active_jobs, uptime_seconds }` | Public |
| GET | `/monitoring/db/stats` | — | `{ tables: [{ name, row_count }], slow_queries: [...] }` | Public (dev); Admin in prod optional |

---

## Users (Admin)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/users` | `?page&page_size&role?` | `{ items: UserRead[], total }` | Admin |
| GET | `/users/{user_id}` | — | `UserRead` | Admin |
| PATCH | `/users/{user_id}` | `{ role?, is_active?, full_name? }` | `UserRead` | Admin |
| DELETE | `/users/{user_id}` | — | `{ "message" }` | Admin |

---

## Upload & files

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/uploads` | `multipart: file` | `UploadResponse` `{ file_id, filename, file_hash, size_bytes, is_duplicate, version_number, scan_id }` | Analyst+; 10/min |
| GET | `/uploads` | `?page&page_size` | `{ items: UploadMetadata[], total }` | Authenticated; scoped to user unless Admin |
| GET | `/uploads/{file_id}` | — | `UploadMetadata` | Authenticated; owner or Admin |
| DELETE | `/uploads/{file_id}` | — | `{ "message" }` | Admin |
| GET | `/uploads/{file_id}/preview` | `?page&page_size` | `{ columns, rows[], total_rows }` | Authenticated |
| GET | `/uploads/{file_id}/versions` | — | `{ versions: FileVersion[] }` | Authenticated |
| GET | `/uploads/{file_id}/versions/compare` | `?version_a&version_b` | `VersionCompareResponse` | Authenticated |

---

## Temp assets

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/assets` | — | `{ files: [{ name, size_bytes, safe }] }` | Authenticated |
| POST | `/assets/select` | `{ "filename" }` | `UploadResponse` (same shape as upload) | Analyst+ |

---

## Security scan

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/scans/{file_id}` | — | `ScanResult` `{ status, issues[], risk_score, recommended_action, scan_timestamp, file_hash }` | Analyst+ |
| GET | `/scans/{file_id}` | — | `ScanResult` (latest) | Authenticated |
| GET | `/scans/{file_id}/history` | — | `{ scans: ScanResult[] }` | Authenticated |

---

## EDA

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/eda/{file_id}` | `EDARequest` `{ force_refresh?: bool }` | `EDAResponse` `{ summary, columns[], quality_warnings[], chart_data, job_id? }` | Analyst+; may queue if large |
| GET | `/eda/{file_id}` | — | `EDAResponse` (cached) | Authenticated |
| GET | `/eda/{file_id}/columns/{column_name}` | — | `ColumnSummary` | Authenticated |
| GET | `/eda/{file_id}/suggestions` | — | `{ target_columns[], feature_columns[], date_columns[], suggested_analyses[] }` | Authenticated |

---

## SQL analysis

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/sql/{file_id}/import` | `{ max_rows?: int }` | `{ imported_rows, table_name }` | Analyst+ |
| POST | `/sql/{file_id}/query` | `{ "query": str, "params"?: {} }` | `{ columns, rows[], row_count }` | Analyst+; read-only validated SQL |
| GET | `/sql/{file_id}/presets` | — | `{ presets: [{ id, name, description, sql }] }` | Authenticated |
| POST | `/sql/{file_id}/presets/{preset_id}/run` | — | `{ columns, rows[], row_count }` | Analyst+ |

Preset examples: group-by aggregations, top-N, filtered counts, join across imported tables.

---

## Analysis jobs (background)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/jobs` | `?status&page` | `{ items: JobStatus[], total }` | Authenticated |
| GET | `/jobs/{job_id}` | — | `JobStatus` `{ id, type, status, progress, error?, created_at, completed_at }` | Authenticated |
| GET | `/jobs/{job_id}/progress` | — | `JobProgress` `{ progress, stage, message }` | Authenticated |
| POST | `/jobs/{job_id}/cancel` | — | `JobStatus` | Analyst+; owner or Admin |
| GET | `/jobs/{job_id}/result` | — | `JobResult` (typed by job type) | Authenticated |

---

## Predictive models (via plugin registry)

Base path: `/models/{file_id}/...` — all Analyst+ unless noted.

### Regression

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/models/{file_id}/regression` | `RegressionRequest` `{ algorithm, target_column, feature_columns[], test_size?, random_state? }` | `ModelJobResponse` `{ job_id }` or sync `RegressionResult` | Analyst+; 20/min |
| GET | `/models/results/{result_id}` | — | `RegressionResult` `{ metrics: { mae, rmse, r2 }, actual_vs_predicted[], residuals[], feature_importance[], explainability }` | Authenticated |

Algorithms: `linear`, `polynomial`, `decision_tree`, `random_forest`.

### Classification

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/models/{file_id}/classification` | `ClassificationRequest` `{ algorithm, target_column, feature_columns[], test_size? }` | `ModelJobResponse` | Analyst+ |
| GET | `/models/results/{result_id}` | — | `ClassificationResult` `{ accuracy, precision, recall, f1, confusion_matrix, classification_report, predictions[], confidence_scores[] }` | Authenticated |

Algorithms: `logistic`, `decision_tree`, `random_forest`, `knn`, `svm`, `naive_bayes`.

### Clustering & PCA

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/models/{file_id}/clustering` | `ClusteringRequest` `{ algorithm, feature_columns[], n_clusters?, method_elbow? }` | `ModelJobResponse` | Analyst+ |
| POST | `/models/{file_id}/pca` | `PCARequest` `{ feature_columns[], n_components? }` | `ModelJobResponse` | Analyst+ |
| GET | `/models/results/{result_id}` | — | `ClusteringResult` or `PCAResult` | Authenticated |

### Time series

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/models/{file_id}/timeseries` | `TimeSeriesRequest` `{ date_column, value_column, algorithm, forecast_periods? }` | `ModelJobResponse` | Analyst+ |
| GET | `/models/results/{result_id}` | — | `TimeSeriesResult` `{ forecast[], metrics, chart_data }` | Authenticated |

Algorithms: `moving_average`, `autoregressive`, `arima`, `sarimax`.

### Similarity / recommendation

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/models/{file_id}/similarity` | `SimilarityRequest` `{ mode: row|item, id_column?, feature_columns[] }` | `ModelJobResponse` or `SimilarityResult` | Analyst+ |
| GET | `/models/results/{result_id}` | — | `SimilarityResult` `{ similarity_matrix_preview, top_pairs[], suitability_note }` | Authenticated |

### Task detection

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/models/{file_id}/detect-tasks` | — | `{ suggestions: [{ type, reason, recommended_columns }] }` | Authenticated |

### Plugins

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/plugins` | `?file_id?` | `{ plugins: [{ name, display_name, description, applicable }] }` | Authenticated |
| POST | `/plugins/{plugin_name}/run` | `{ file_id, params: {} }` | `ModelJobResponse` | Analyst+ |

Built-in plugins: `anomaly_detection`, `customer_churn`, `fraud_detection`, `demand_forecast`.

---

## Explainability

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/explainability/{result_id}` | — | `{ feature_importance[], shap_values?, confidence_scores?, prediction_intervals?, summary_text }` | Authenticated |
| POST | `/explainability/{result_id}/shap` | `{ max_samples?: int }` | `{ shap_summary, shap_values_sample[] }` | Analyst+; tree/linear models |

---

## Business analytics

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/business/{file_id}/analyze` | `BusinessAnalyticsRequest` `{ column_mapping?: {}, date_column?, revenue_column?, cost_column?, ... }` | `BusinessReport` or `{ job_id }` | Analyst+ |
| GET | `/business/{file_id}/kpis` | — | `{ cards: KPICard[] }` | Authenticated |
| GET | `/business/results/{result_id}` | — | `BusinessReport` `{ kpis, charts, tables, forecast }` | Authenticated |

---

## Insights (AI summaries)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/insights/generate` | `InsightRequest` `{ job_id or result_id, analysis_type }` | `InsightResponse` `{ summary, source: llm|fallback, generated_at }` | Analyst+ |
| GET | `/insights/{insight_id}` | — | `InsightResponse` | Authenticated |
| GET | `/insights/by-job/{job_id}` | — | `InsightResponse` | Authenticated |

---

## Export

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| POST | `/export/json` | `ExportRequest` `{ result_ids[], include_eda?, include_scan? }` | `application/json` stream or `{ download_url }` | Viewer+ |
| POST | `/export/csv` | `ExportRequest` | `text/csv` stream | Viewer+ |
| POST | `/export/pdf` | `ExportRequest` | `application/pdf` stream | Viewer+ |

PDF sections: executive summary, dataset overview, EDA charts, model performance, business KPIs, security scan, recommendations, appendix.

---

## Audit

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/audit` | `?event_type&user_id&from&to&page` | `{ items: AuditLogEntry[], total }` | Admin |
| GET | `/audit/{file_id}` | — | `{ items: AuditLogEntry[] }` | Admin or file owner |

---

## Version comparison (results)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/versions/results/compare` | `?result_id_a&result_id_b` | `{ metrics_diff, summary }` | Authenticated |

---

## Health check (legacy alias)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| GET | `/health` | — | `{ "status": "ok" }` | Public; minimal ping (commit 2); superseded by monitoring |

---

## WebSocket (optional stretch)

| Method | Path | Request | Response | Auth / limits |
|--------|------|---------|----------|---------------|
| WS | `/ws/jobs/{job_id}` | token query param | progress events | Authenticated; fallback to polling |

Phase 1 implementation uses polling only; WS noted for future.

---

## OpenAPI

FastAPI auto-generates OpenAPI 3.1 at `/api/v1/openapi.json` and Swagger UI at `/api/v1/docs` (disabled or Admin-only in production via config).
