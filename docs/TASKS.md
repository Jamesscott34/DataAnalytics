# Implementation task list — predictive-security-analytics-lab

> Phase 0 planning document (0.5). Each task maps to a feature branch, conventional commit, files touched, and acceptance tests.

**Branch workflow**: `main` ← merge commit ← `feature/<name>` (or `chore/`, `docs/`, `test/`, `fix/`).

**Pre-commit checks** (all must pass before commit unless `wip:` exception):

- Backend: `ruff check app/`, `black --check app/`, `isort --check-only app/`, `mypy app/`, `bandit -r app/`, `pytest`
- Frontend: `eslint src/`, `prettier --check src/`, `vitest`; `vite build` if build config changed

---

## Task 1 — Initial structure and planning ✅

| Field | Value |
|-------|-------|
| **Branch** | `chore/project-init` |
| **Commit** | `chore(project): initial project structure and planning documents` |
| **Files created** | Root: `README.md`, `LICENSE` (MIT), `.gitignore`, `.env.example`, `docker-compose.yml` (stub). `docs/`: `ARCHITECTURE.md`, `API.md`, `DATABASE_SCHEMA.md`, `COMPONENT_TREE.md`, `TASKS.md`, stub `CHANGELOG.md`, `DATA_WORKFLOW.md`, `MODELS.md`, `SECURITY.md`, `TESTING.md`. `temp_assets/README.md`, `temp_assets/.gitkeep`. Empty dirs: `backend/`, `frontend/`, `docker/`, `.github/workflows/`, `deploy/`. |
| **Tests** | None (docs only). Verify Markdown renders; `git init` succeeds. |
| **Done when** | All Phase 0 docs present; repo initialised; merge to `main`. |

---

## Task 2 — FastAPI backend shell ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/api-health` |
| **Commit** | `feat(api): add FastAPI backend with health check endpoint` |
| **Files** | `backend/app/main.py`, `backend/app/__init__.py`, `backend/requirements.txt`, `backend/pyproject.toml` (tool config stubs), `backend/tests/test_health.py` |
| **Tests** | `GET /api/v1/health` returns 200 `{ "status": "ok" }`. Pytest passes. |
| **Done when** | `uvicorn app.main:app` starts; health test green; merge to `main`. |

---

## Task 3 — React Vite shell ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/frontend-shell` |
| **Commit** | `feat(frontend): add React Vite shell with health check display` |
| **Files** | `frontend/package.json`, `vite.config.js`, `index.html`, `src/main.jsx`, `src/App.jsx`, `src/api/client.js`, `src/api/monitoring.js`, `src/pages/HealthStatusPage.jsx`, `src/components/HealthStatusPanel.jsx`, `frontend/.env.example`, ESLint/Prettier config |
| **Tests** | Vitest: `HealthStatusPanel` renders; fetches health mock. `vite build` succeeds. |
| **Done when** | Dev server shows backend health; merge to `main`. |

---

## Task 4 — Database models and Alembic ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/db-models` |
| **Commit** | `feat(db): add SQLAlchemy models, Alembic config, and initial migration` |
| **Files** | `backend/app/database.py`, `backend/app/models/*.py` (users, sessions, files stubs), `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/001_initial.py`, `backend/tests/test_database.py` |
| **Tests** | Migration up/down; models import; session fixture works. |
| **Done when** | `alembic upgrade head` on SQLite; pytest green. |

---

## Task 5 — Config, logging, errors ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/config-logging` |
| **Commit** | `feat(config): add .env config, logging, and error response standards` |
| **Files** | `backend/app/config.py`, `backend/app/logging_config.py`, `backend/app/schemas/errors.py`, `backend/app/utils/response_utils.py`, `backend/app/utils/logging_utils.py`, `backend/.env.example`, middleware for security headers, `backend/tests/test_config.py`, `backend/tests/test_errors.py` |
| **Tests** | Config loads from env; validation error returns standard shape; JSON logs emitted. |
| **Done when** | All quality tools pass; merge. |

---

## Task 6 — Authentication ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/auth` |
| **Commit** | `feat(auth): add user accounts, JWT authentication, and role-based access` |
| **Files** | `backend/app/auth/*`, `backend/app/schemas/auth.py`, `backend/app/routers/auth.py`, `backend/app/routers/users.py`, migration `002` if needed, `frontend/src/pages/LoginPage.jsx`, `LoginForm`, `useAuth`, `useLogin`, `ProtectedRoute`, `api/auth.js`, `types/auth.ts` |
| **Tests** | Register/login; JWT valid/invalid/expired; Viewer cannot upload; Analyst cannot delete. |
| **Done when** | RBAC dependency injectable; frontend login flow works. |

---

## Task 7 — Secure CSV upload ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/upload` |
| **Commit** | `feat(upload): add secure CSV upload endpoint` |
| **Files** | `backend/app/services/csv_service.py`, `backend/app/utils/file_utils.py`, `hash_utils.py`, `encoding_utils.py`, `schemas/upload.py`, `routers/uploads.py`, `models/uploaded_file.py`, migration `002_files`, `frontend/UploadPage`, `UploadForm`, `api/uploads.js` |
| **Tests** | Safe CSV accepted; non-CSV, double ext, traversal, absolute path, null byte, oversized blocked. |
| **Done when** | Upload stores file + metadata; duplicate hash detected. |

---

## Task 8 — Security scanner ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/security-scanner` |
| **Commit** | `feat(security): add Python-only security scanner` |
| **Files** | `backend/app/services/security_scan_service.py`, `schemas/upload.py` (ScanResult), `routers/scans.py`, `models/security_scan.py`, migration `003`, `ScannerResultPanel`, `ScanStatusBadge` |
| **Tests** | XSS, formula injection, dangerous formulas, command strings, binary, risk score, SHA-256 in output. |
| **Done when** | Scan runs on upload; blocked prevents analysis in UI. |

---

## Task 9 — Temp assets ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/temp-assets` |
| **Commit** | `feat(assets): add temp_assets CSV selector endpoint and UI` |
| **Files** | `routers/assets.py`, path validation in `file_utils.py`, `AssetsPage`, `AssetsFileList`, sample safe CSV in `temp_assets/` (synthetic, no PII), `.gitignore` for `*.csv` except samples |
| **Tests** | Listing; selection; path traversal rejected. |
| **Done when** | UI lists and selects asset without upload. |

---

## Task 10 — Audit logging ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/audit` |
| **Commit** | `feat(audit): add audit logging to uploads, scans, and analysis runs` |
| **Files** | `models/audit_log.py`, `schemas/audit.py`, `services` hooks via logging_utils, `routers/audit.py`, migration `004` |
| **Tests** | Audit entries on upload and scan; Admin list endpoint. |
| **Done when** | Audit persisted + structured log stream. |

---

## Task 11 — Dataset versioning ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/versioning` |
| **Commit** | `feat(versioning): add dataset version detection and history` |
| **Files** | `services/dataset_version_service.py`, `models/file_version.py`, migration `005`, `VersionHistoryPage`, version compare endpoint |
| **Tests** | Duplicate upload records version; history correct; no second disk copy. |
| **Done when** | Re-upload shows version timeline. |

---

## Task 12 — EDA service ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/eda` |
| **Commit** | `feat(eda): add EDA service and EDA API endpoints` |
| **Files** | `services/eda_service.py`, `utils/type_utils.py`, `date_utils.py`, `schemas/eda.py`, `routers/eda.py`, `tests/test_eda_service.py` |
| **Tests** | EDA summary: types, missing, numeric/categorical stats, suggestions. |
| **Done when** | `POST /eda/{file_id}` returns full summary; cache by hash. |

---

## Task 13 — SQL analysis ✅

| Field | Value |
|-------|-------|
| **Branch** | `feature/sql` |
| **Commit** | `feat(sql): add SQL analysis service` |
| **Files** | `services/sql_analysis_service.py`, `models/csv_data.py`, migration `008`, `routers/sql.py`, `SQLAnalysisPage` |
| **Tests** | Import rows; group-by preset; read-only query rejection of destructive SQL. |
| **Done when** | Real SQL against stored rows. |

---

## Task 14 — EDA UI

| Field | Value |
|-------|-------|
| **Branch** | `feature/eda-ui` |
| **Commit** | `feat(eda-ui): add EDA dashboard and chart components to frontend` |
| **Files** | `EDADashboard`, all EDA `charts/*`, `hooks/useEDA.js`, Vitest chart smoke tests |
| **Tests** | Charts render without crash; EDA summary cards show data. |
| **Done when** | Full EDA tab functional. |

---

## Task 15 — Regression

| Field | Value |
|-------|-------|
| **Branch** | `feature/regression` |
| **Commit** | `feat(regression): add regression model service and endpoints` |
| **Files** | `services/regression_service.py`, `schemas/models.py`, `routers/models_regression.py`, register in `plugin_registry.py`, tests for MAE/RMSE/R2 |
| **Tests** | Metrics correct; actual vs predicted payload; RF feature importance. |
| **Done when** | All four algorithms runnable via API. |

---

## Task 16 — Classification

| Field | Value |
|-------|-------|
| **Branch** | `feature/classification` |
| **Commit** | `feat(classification): add classification model service and endpoints` |
| **Files** | `services/classification_service.py`, router, tests for accuracy/F1/confusion matrix/confidence |
| **Tests** | Per required test list in spec. |
| **Done when** | Six algorithms exposed. |

---

## Task 17 — Clustering and PCA

| Field | Value |
|-------|-------|
| **Branch** | `feature/clustering-pca` |
| **Commit** | `feat(clustering): add clustering, PCA service, and endpoints` |
| **Files** | `clustering_service.py`, `pca_service.py`, charts, tests |
| **Tests** | Cluster output shape; elbow data; PCA variance. |
| **Done when** | K-means + hierarchical + PCA API complete. |

---

## Task 18 — Time series

| Field | Value |
|-------|-------|
| **Branch** | `feature/timeseries` |
| **Commit** | `feat(timeseries): add time series forecasting service and endpoints` |
| **Files** | `timeseries_service.py`, `ForecastChart`, tests |
| **Tests** | Forecast table + metrics returned. |
| **Done when** | MA, AR, ARIMA/SARIMAX where practical. |

---

## Task 19 — Similarity / recommendation

| Field | Value |
|-------|-------|
| **Branch** | `feature/similarity` |
| **Commit** | `feat(similarity): add recommendation and similarity analysis` |
| **Files** | `recommendation_service.py`, tests, suitability messaging |
| **Tests** | Cosine similarity; unsuitable dataset message. |
| **Done when** | API + UI section complete. |

---

## Task 20 — Explainability

| Field | Value |
|-------|-------|
| **Branch** | `feature/explainability` |
| **Commit** | `feat(explainability): add feature importance, SHAP values, confidence scores` |
| **Files** | `explainability_service.py`, `FeatureImportanceChart`, `ShapSummaryPanel`, `docs/MODELS.md` SHAP section |
| **Tests** | SHAP where supported; fallback importance; confidence per class. |
| **Done when** | Result pages show explainability panel. |

---

## Task 21 — Business analytics

| Field | Value |
|-------|-------|
| **Branch** | `feature/business` |
| **Commit** | `feat(business): add business analytics service and KPI dashboard` |
| **Files** | `business_analytics_service.py`, `math_utils.py`, `schemas/business.py`, `KPICard`, tests for revenue/margin/January sales |
| **Tests** | KPI values match raw calculations. |
| **Done when** | KPI cards + charts render. |

---

## Task 22 — AI insights

| Field | Value |
|-------|-------|
| **Branch** | `feature/insights` |
| **Commit** | `feat(insights): add AI-generated plain-English analysis summaries` |
| **Files** | `insight_service.py`, `schemas/insights.py`, `models/generated_insight.py`, `InsightsPanel`, migration `009` |
| **Tests** | Fallback when no API key; LLM path mocked. |
| **Done when** | Insights stored and displayed post-analysis. |

---

## Task 23 — Pest control workflow UI

| Field | Value |
|-------|-------|
| **Branch** | `feature/pest-ui` |
| **Commit** | `feat(pest-ui): add pest control analytics workflow and dashboard` |
| **Files** | `BusinessDashboardPage`, column mapper presets for pest schema, sample pest CSV in `temp_assets/`, `DATA_WORKFLOW.md` pest section |
| **Tests** | Business form renders; workflow E2E with sample data. |
| **Done when** | End-to-end pest analytics demo path documented. |

---

## Task 24 — Result charts and export views

| Field | Value |
|-------|-------|
| **Branch** | `feature/charts` |
| **Commit** | `feat(charts): add all result chart components and export views` |
| **Files** | Remaining `charts/*`, `ModelResultsView`, `ExportPage` layout, Vitest for all charts |
| **Tests** | Each chart component smoke test. |
| **Done when** | All model result types have charts. |

---

## Task 25 — Export reports

| Field | Value |
|-------|-------|
| **Branch** | `feature/export` |
| **Commit** | `feat(export): add JSON, CSV, and PDF professional report export` |
| **Files** | `report_service.py`, `schemas/export.py`, `routers/export.py`, reportlab/weasyprint, tests for PDF sections |
| **Tests** | PDF contains all 8 sections; JSON/CSV match UI data. |
| **Done when** | Download works from UI. |

---

## Task 26 — Background jobs

| Field | Value |
|-------|-------|
| **Branch** | `feature/background` |
| **Commit** | `feat(background): add background task processing and job progress reporting` |
| **Files** | `background_service.py`, `schemas/jobs.py`, `routers/jobs.py`, `models/analysis_job.py`, `job_progress.py`, `JobProgressPage`, migration `006` |
| **Tests** | queued→running→complete; cancel; failed stores error. |
| **Done when** | Frontend polls progress; cancel works. |

---

## Task 27 — Plugin registry

| Field | Value |
|-------|-------|
| **Branch** | `feature/plugin` |
| **Commit** | `feat(plugin): add plugin registry for ML model extensibility` |
| **Files** | `plugin_registry.py`, built-in plugins (anomaly, churn, fraud, demand), `routers/plugins.py`, tests |
| **Tests** | register/get/list; new plugin without router changes. |
| **Done when** | Plugins hidden when not applicable. |

---

## Task 28 — Monitoring

| Field | Value |
|-------|-------|
| **Branch** | `feature/monitoring` |
| **Commit** | `feat(monitoring): add health, metrics, and slow query logging endpoints` |
| **Files** | `monitoring_service.py`, `schemas/monitoring.py`, `routers/monitoring.py`, timing middleware, slow query listener |
| **Tests** | Health 200 + DB status; metrics request counts. |
| **Done when** | `/monitoring/*` endpoints live. |

---

## Task 29 — Backend test suite

| Field | Value |
|-------|-------|
| **Branch** | `test/backend-coverage` |
| **Commit** | `test(backend): add backend test suite with 80%+ coverage on services` |
| **Files** | `backend/tests/**`, `pytest.ini`, coverage config in `pyproject.toml`, fill gaps per spec test list |
| **Tests** | `pytest --cov=app/services --cov-fail-under=80` passes. |
| **Done when** | Coverage report ≥80% on services. |

---

## Task 30 — Frontend test suite

| Field | Value |
|-------|-------|
| **Branch** | `test/frontend` |
| **Commit** | `test(frontend): add frontend test suite with Vitest` |
| **Files** | `frontend/src/**/*.test.jsx`, `vitest.config.js`, testing-library setup |
| **Tests** | All items in spec frontend test list pass. |
| **Done when** | `npm run test` green. |

---

## Task 31 — CI

| Field | Value |
|-------|-------|
| **Branch** | `chore/ci` |
| **Commit** | `chore(ci): add GitHub Actions workflow` |
| **Files** | `.github/workflows/ci.yml` |
| **Tests** | Workflow runs lint + pytest + vitest + build on push. |
| **Done when** | CI YAML valid; passes locally equivalent commands. |

---

## Task 32 — Docker

| Field | Value |
|-------|-------|
| **Branch** | `chore/docker` |
| **Commit** | `chore(docker): add Docker and Docker Compose setup` |
| **Files** | `docker/backend.Dockerfile`, `docker/frontend.Dockerfile`, `docker/nginx.conf`, `docker-compose.yml`, volumes, healthchecks |
| **Tests** | `docker-compose up --build` all healthy; backend non-root. |
| **Done when** | Single-command startup from `.env.example`. |

---

## Task 33 — Deployment

| Field | Value |
|-------|-------|
| **Branch** | `feat/deploy` |
| **Commit** | `feat(deploy): add deployment scripts and cloud provider config` |
| **Files** | `deploy/railway.md` or `render.yaml` / Azure notes, README deployment section |
| **Tests** | Manual: deploy checklist documented. |
| **Done when** | Live deployment path documented. |

---

## Task 34 — Full documentation

| Field | Value |
|-------|-------|
| **Branch** | `docs/all` |
| **Commit** | `docs(all): add full documentation suite` |
| **Files** | Complete `README.md`, `docs/SECURITY.md`, `MODELS.md`, `DATA_WORKFLOW.md`, `TESTING.md`, `CHANGELOG.md` |
| **Tests** | All doc files exist; links valid. |
| **Done when** | README badges placeholders; licence present. |

---

## Task 35 — Final validation

| Field | Value |
|-------|-------|
| **Branch** | `chore/final-validation` |
| **Commit** | `chore(final): end-to-end validation and cleanup` |
| **Files** | Any fixes from 25-point validation checklist in spec |
| **Tests** | Full validation list (docker E2E, RBAC, exports, all tools). |
| **Done when** | Git clean; final commit on `main`; report commit hash + count. |

---

## Dependency graph (implementation order)

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11
                              ↓
                    12 → 13 → 14
                              ↓
              15,16,17,18,19 (parallel after 12)
                              ↓
                    20 → 21 → 22 → 23 → 24 → 25
                              ↓
                         26 → 27 → 28
                              ↓
                    29,30 (parallel) → 31 → 32 → 33 → 34 → 35
```

## Project status

### Phase 0 — Planning
Complete. Architecture, API, database schema, component tree, and this task list.

### Phase 1 — Foundation (Tasks 1–5)
Complete.
- Task 1: repo structure, planning docs (`ee25c24`)
- Task 2: FastAPI `/api/v1/health` (`7a935c5`)
- Task 3: React Vite shell, health panel (`0f67925`)
- Task 4: SQLAlchemy models, Alembic `001_initial` (`7654e53`)
- Task 5: `.env` config, logging, error responses (`eb5172b`)

### Phase 2 — Auth and file pipeline (Tasks 6–11)
Complete. Tasks 6–11 delivered auth, secure upload, scanner, temp assets,
integrity manifest, audit logging, and dataset versioning. Task 12 (EDA service)
is complete. Next: Task 14 (EDA UI).

### Phase 3 — Analysis services (Tasks 12–19)
In progress. Tasks 12–13 complete (EDA service, SQL analysis). Next: Task 14 (EDA UI).

### Phase 4 — Insights, UI, and export (Tasks 20–25)
Not started. Explainability, business KPIs, charts, PDF/JSON/CSV export.

### Phase 5 — Jobs, plugins, monitoring (Tasks 26–28)
Not started. Background tasks, plugin registry, health/metrics endpoints.

### Phase 6 — Quality and shipping (Tasks 29–35)
Not started. Test coverage, CI, Docker, deployment, docs, final validation.
