# Predictive Data Analytics Platform

[![CI](https://github.com/Jamesscott34/DataAnalytics/actions/workflows/ci.yml/badge.svg)](https://github.com/Jamesscott34/DataAnalytics/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A production-style, full-stack data analytics application built with **FastAPI** and **React**. It takes you from raw CSV or Excel files through security validation, exploratory analysis, machine learning, SQL querying, business intelligence, and professional report export — all behind authenticated, role-based access control.

The platform is designed for portfolio demonstration, coursework submission, and as a reference architecture for separating API routes, domain services, persistence, and a modern single-page frontend.

---

## Table of contents

- [What this application does](#what-this-application-does)
- [Feature reference](#feature-reference)
- [User roles](#user-roles)
- [Architecture](#architecture)
- [End-to-end workflow](#end-to-end-workflow)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Quality assurance](#quality-assurance)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)

---

## What this application does

At a high level, the platform answers one question: **“What can we learn from this dataset, safely and repeatably?”**

1. **Ingest** tabular data (upload, Excel conversion, or bundled sample files).
2. **Validate** every file with a defensive Python security scanner before analysis.
3. **Profile** columns, missing values, distributions, and data-quality issues.
4. **Analyse** using statistical, ML, SQL, or business-KPI engines.
5. **Visualise** results in interactive React dashboards with Recharts.
6. **Persist** outputs in SQL so results survive server restarts.
7. **Export** findings as JSON, CSV, or PDF for sharing or archival.

Every significant action — upload, scan, analysis run, export — is logged to an audit trail. Large files are sampled or processed in background jobs with live progress polling in the UI.

---

## Feature reference

### Authentication and user management

- **JWT access and refresh tokens** with bcrypt password hashing.
- **Three roles**: Admin, Analyst, and Viewer — enforced on every protected endpoint.
- **Session management**: login, refresh, logout, and `/auth/me` profile lookup.
- **Admin user API**: list, update roles, and deactivate accounts.
- Optional `ALLOW_PUBLIC_REGISTRATION` flag to restrict sign-up in production.

### Data ingestion and file management

| Capability | Description |
|------------|-------------|
| **CSV upload** | Multipart upload with filename sanitisation, size limits (configurable, default 250 MB), and MIME validation. |
| **XLSX import** | Excel workbooks (`.xlsx`) converted to UTF-8 CSV via `openpyxl` before entering the normal upload pipeline. |
| **Temp assets** | Read-only sample datasets in `temp_assets/` can be listed and imported without a browser file picker. |
| **SHA-256 deduplication** | Identical file content is detected per user; clients can reuse or replace existing uploads. |
| **Ragged CSV support** | Market-basket style rows with variable column counts are padded instead of rejected, with warnings surfaced in EDA. |
| **Large-file handling** | Files above 50 MB trigger client-side hash verification; EDA on very large files uses row sampling or background jobs. |
| **Version history** | Upload versions are tracked; users can compare schema and row counts across versions. |
| **File preview** | Paginated preview of uploaded CSV content from the API. |
| **Admin delete** | Only administrators can permanently remove uploaded files. |

### Security scanning

Before any analysis runs, every upload passes through a **Python-only defensive scanner** (not antivirus). It checks for:

- Unsafe filenames and path traversal
- Non-CSV extensions and binary content
- Script injection markers (`<script>`, `javascript:`, event handlers)
- CSV formula injection (`=CMD`, `=HYPERLINK`, cells starting with `=`, `+`, `-`, `@`)
- Suspicious command strings and embedded URLs
- Overly long rows and base64-like payloads

Scan results are stored with a **risk score** and recommended action: `safe`, `warning`, or `blocked`. Blocked files cannot proceed to analysis.

### Asset integrity manifest

For course and demo datasets in `temp_assets/` and `assets/`, the platform maintains an optional **password-protected SHA-256 manifest**:

- Detects new, modified, or removed files since the last manifest was saved.
- Prompts analysts once per session to create, unlock, or review changes.
- Helps ensure bundled datasets have not been tampered with between runs.

### Exploratory data analysis (EDA)

EDA produces a rich profile of every uploaded dataset:

- **Summary statistics**: row count, column count, duplicate rows, missing cells and percentages.
- **Column inference**: automatic detection of integer, float, date, boolean, and text types.
- **Per-column stats**: min, max, mean, median, standard deviation, unique counts, and sample values.
- **Quality warnings**: high cardinality, constant columns, type mismatches, ragged rows, and sampling notices.
- **Charts** (`dataset_charts`):
  - Histograms and bar charts per column
  - Scatter plots between numeric pairs
  - Line charts for date + numeric series
  - Correlation heatmaps when two or more numeric columns exist
- **Caching**: results keyed by file hash; `force_refresh` bypasses cache.
- **Background EDA**: files ≥ 50 MB (or `force_background`) queue a job; the frontend polls `/jobs/{id}` for progress.
- **Suggestions endpoint**: recommends target columns, features, and analysis types for downstream ML.

### Machine learning

All model outputs are stored in the `model_results` SQL table and reloadable via `GET /models/results/{result_id}`.

#### Regression

Predict a continuous target from numeric or encoded features.

| Algorithm | Notes |
|-----------|-------|
| `linear` | Ordinary least squares with coefficient-based feature importance |
| `polynomial` | Polynomial feature expansion with linear regression |
| `decision_tree` | Tree impurity feature importance |
| `random_forest` | Ensemble with aggregated importance |

**Metrics**: MAE, RMSE, R². **Outputs**: actual-vs-predicted series, residual charts, feature importance.

#### Classification

Predict a categorical label.

| Algorithm | Notes |
|-----------|-------|
| `logistic` | Multinomial logistic regression |
| `decision_tree` | Interpretable splits |
| `random_forest` | Robust ensemble classifier |
| `knn` | k-nearest neighbours |
| `svm` | Support vector machine |
| `naive_bayes` | Probabilistic baseline |

**Metrics**: accuracy, precision, recall, F1. **Outputs**: confusion matrix, per-class report, prediction confidence scores.

#### Clustering

Group rows without labels.

| Algorithm | Notes |
|-----------|-------|
| `kmeans` | Partition-based clustering with elbow support |
| `hierarchical` | Agglomerative clustering |

**Outputs**: cluster assignments, centroids, silhouette-style diagnostics.

#### Principal component analysis (PCA)

Reduce dimensionality while preserving variance. Returns component loadings, explained variance ratios, and a 2D scatter projection.

#### Time series forecasting

Forecast future values from dated observations.

| Algorithm | Notes |
|-----------|-------|
| `moving_average` | Simple rolling baseline |
| `autoregressive` | AR model |
| `arima` | Auto-regressive integrated moving average |
| `sarimax` | Seasonal ARIMA with exogenous support where applicable |

**Outputs**: forecast series, error metrics, and chart-ready payloads.

#### Similarity and recommendations

Find similar rows or items using cosine similarity on selected feature columns. Returns top pairs and a suitability note when the dataset is not appropriate.

#### Analytics plugins

Extensible plugin registry (`GET /plugins`, `POST /plugins/{name}/run`):

| Plugin | Purpose |
|--------|---------|
| `anomaly_detection` | Isolation forest on numeric columns |
| `customer_churn` | Logistic regression on a categorical label |
| `fraud_detection` | Z-score outlier scoring |
| `demand_forecast` | Moving-average forecast from date + value columns |

Plugins report `applicable: false` when required columns are missing.

### Business analytics and KPIs

Automatically infers date, revenue, cost, customer, technician, pest, and location columns from headers. Computes:

- Total revenue, cost, gross margin, profit, and margin %
- Average revenue and average job value
- Total jobs and January sales
- Repeat customer count
- Busiest month and best-performing service
- Month-over-month growth and next-month revenue forecast
- Yearly revenue and named-month breakdowns
- Jobs by technician, pest type, and location

Includes a **pest control preset** that maps `job_date`, `revenue`, and `cost` for demo datasets like `temp_assets/pest_control_sample.csv`.

### SQL analysis

- Import uploaded CSV rows into an in-memory SQLite table per file.
- Run **read-only validated SQL** with parameter binding.
- Execute built-in **presets** (group-by aggregations, top-N, filtered counts).
- **Dataset groups**: combine multiple files and run group-level SQL imports and queries.

### Background jobs

Long-running work (EDA on large files, queued model training) is tracked in `analysis_jobs`:

- States: `queued` → `running` → `complete` / `failed` / `cancelled`
- Progress percentage updated throughout execution
- Cancel endpoint for queued or running jobs
- Result payload and `result_id` stored on completion

### Insights and explainability

- **Insights**: plain-English summaries of analysis results (LLM-backed when `LLM_API_KEY` is set; rule-based fallback otherwise).
- **Explainability**: feature importance, confidence summaries, and descriptive notes via `/explainability/{result_id}`.
- **SHAP endpoint**: structured fallback response when full SHAP values are not computed locally.

### Quick scan

A fast, lightweight file scan distinct from the full security scanner — produces a `report_id` used by the export pipeline for rapid suitability assessment.

### Export and reporting

| Format | Description |
|--------|-------------|
| **JSON** | Structured report payload for programmatic use |
| **CSV** | Flattened tabular export |
| **PDF** | Professional report with charts via ReportLab |

Scan results stored on disk can also be downloaded individually.

### Monitoring and operations

| Endpoint | Purpose |
|----------|---------|
| `GET /monitoring/health` | Liveness, database connectivity, disk space |
| `GET /monitoring/metrics` | Request counts, latency, error rate, active jobs |
| `GET /monitoring/db/stats` | Table row counts and slow-query log |

Structured JSON logging and a separate audit log stream cover uploads, scans, and analysis events.

### Audit logging

Persistent `audit_logs` table plus structured log output for security-relevant events: uploads, scans, analysis starts, exports, and authentication actions.

---

## User roles

| Role | Capabilities |
|------|--------------|
| **Viewer** | Read uploads, EDA results, model outputs, and dashboards. Cannot upload or run analysis. |
| **Analyst** | Full analysis workflow: upload, scan, EDA, ML, SQL, business KPIs, exports, background jobs. |
| **Admin** | All Analyst permissions plus user management, file deletion, and integrity manifest administration. |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Browser (React SPA)                              │
│   Pages · Components · Hooks · Recharts · api/ client (JWT in headers)      │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │  HTTPS  /api/v1/*
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI backend (Python 3.12)                         │
│  ┌─────────────┐    ┌──────────────────────────────────────────────────────┐  │
│  │ routers/    │───▶│ services/  EDA · ML · scans · reports · jobs · SQL  │  │
│  │ thin HTTP   │    │ plugin_registry · result_persistence · exports       │  │
│  └─────────────┘    └──────────────────────────────────────────────────────┘  │
│  auth/ · schemas/ · middleware/ · Alembic migrations · JSON logging           │
└───────┬──────────────────────┬──────────────────────┬────────────────────────┘
        ▼                      ▼                      ▼
  File storage           SQLite / PostgreSQL      Optional LLM API
  (uploads, scans)       (users, jobs, results)
```

### Design principles

- **Routers stay thin** — no pandas, ML, or SQL in route handlers.
- **Services own business logic** — testable in isolation with 80%+ coverage target.
- **Results persist in SQL** — `model_results` table stores EDA, ML, and business outputs.
- **Frontend never touches the database** — all access through `/api/v1`.
- **Uploads never live in `public/`** — files stored outside the web root by content hash.

Full diagrams and layer tables: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## End-to-end workflow

```
Register / Login
      │
      ▼
Upload CSV or XLSX  ──or──  Select temp asset
      │
      ▼
Security scan (safe / warning / blocked)
      │
      ▼
EDA ──────────────────────────────┐
      │                           │
      ▼                           ▼
Choose analysis path:      Review quality warnings
  • Regression / Classification
  • Clustering / PCA
  • Time series / Similarity
  • Business KPIs
  • SQL query / presets
  • Analytics plugins
      │
      ▼
View dashboards + explainability
      │
      ▼
Export JSON / CSV / PDF
```

**Demo path** — import `temp_assets/pest_control_sample.csv` → Business analytics → pest control preset → Calculate KPIs → Export report.

---

## Technology stack

| Layer | Technologies |
|-------|--------------|
| **API** | FastAPI, Uvicorn, Pydantic, python-jose, bcrypt |
| **Data** | SQLAlchemy, Alembic, pandas, NumPy, openpyxl |
| **ML / stats** | scikit-learn, statsmodels |
| **Reports** | ReportLab |
| **Frontend** | React 18, Vite, Vitest, ESLint, Prettier, Recharts |
| **Testing** | pytest, pytest-cov, Playwright |
| **Quality** | ruff, black, isort, mypy, bandit |
| **Ops** | Docker, Docker Compose, GitHub Actions |

---

## Repository structure

```
.
├── backend/                 # FastAPI app, migrations, pytest (128+ tests)
│   ├── app/routers/         # HTTP endpoints
│   ├── app/services/        # Business logic and ML
│   ├── app/models/          # SQLAlchemy ORM
│   ├── app/schemas/         # Pydantic models
│   └── alembic/versions/    # Database migrations (001–010)
├── frontend/                # React SPA
│   └── src/
│       ├── pages/           # Route-level views (EDA, ML, Business, …)
│       ├── components/      # Reusable UI including charts/
│       ├── hooks/           # Data-fetching and form state
│       └── api/             # HTTP client layer
├── e2e/                     # Playwright end-to-end tests
├── docs/                    # Architecture, API, schema, security guides
├── temp_assets/             # Bundled sample CSV datasets
├── docker/                  # Dockerfiles and nginx config
├── scripts/validate.sh      # Full local validation script
└── .github/workflows/ci.yml # CI pipeline
```

---

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm 9+

### Local development

**1. Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**2. Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| Web application | http://localhost:5173 |
| Interactive API docs | http://localhost:8000/api/v1/docs |
| Health check | http://localhost:8000/api/v1/monitoring/health |

The Vite dev server proxies `/api` to the backend automatically.

### Docker

```bash
docker compose up --build
```

### Full validation

```bash
chmod +x scripts/validate.sh
./scripts/validate.sh
```

---

## Configuration

Copy [backend/.env.example](backend/.env.example) and adjust as needed.

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./data/app.db` |
| `JWT_SECRET_KEY` | Token signing key | Change in production |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` |
| `UPLOAD_DIR` | Stored upload path | `./data/uploads` |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit | `250` |
| `EDA_SAMPLE_MAX_ROWS` | Row cap for in-process EDA | `100000` |
| `LLM_API_KEY` | Optional insight generation | Empty (fallback text) |
| `ALLOW_PUBLIC_REGISTRATION` | Open sign-up | `true` |

Frontend: [frontend/.env.example](frontend/.env.example) — set `VITE_API_BASE_URL` in production builds.

---

## Quality assurance

| Suite | Command | Target |
|-------|---------|--------|
| Backend tests | `cd backend && .venv/bin/pytest -q` | 128+ tests |
| Service coverage | `pytest --cov=app/services --cov-fail-under=80` | ≥ 80% |
| Frontend unit | `cd frontend && npm run test -- --run` | 41+ tests |
| Lint / format | ruff, black, isort, eslint, prettier | Enforced in CI |
| Static analysis | mypy, bandit | Enforced in CI |
| End-to-end | `cd e2e && npm test` | Upload → EDA → export |

GitHub Actions runs all of the above on every push and pull request to `main`.

---

## Deployment

- **Docker Compose** — `docker compose up --build` for local or single-host deployment.
- **Railway** — step-by-step guide: [deploy/railway.md](deploy/railway.md).
- **Production checklist**:
  - PostgreSQL instead of SQLite
  - Strong `JWT_SECRET_KEY` via platform secrets
  - Restrict `CORS_ORIGINS` to your domain
  - Set `ALLOW_PUBLIC_REGISTRATION=false` unless open sign-up is intended
  - TLS at the load balancer or platform edge

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system diagram, observability, security boundaries |
| [docs/API.md](docs/API.md) | Complete REST endpoint catalogue |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Tables, relationships, migrations |
| [docs/COMPONENT_TREE.md](docs/COMPONENT_TREE.md) | React pages, components, and hooks |
| [docs/DATA_WORKFLOW.md](docs/DATA_WORKFLOW.md) | Step-by-step analysis paths |
| [docs/SECURITY.md](docs/SECURITY.md) | Scanner rules and defensive controls |
| [docs/MODELS.md](docs/MODELS.md) | ML algorithms and explainability matrix |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy and CI integration |
| [docs/TASKS.md](docs/TASKS.md) | Implementation task index |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Feature history |
| [docs/COURSE_COVERAGE_AUDIT.md](docs/COURSE_COVERAGE_AUDIT.md) | Course specification coverage audit |

---

## License

MIT — see [LICENSE](LICENSE).
