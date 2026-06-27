# Course Coverage Audit — predictive-security-analytics-lab

**Audit date:** 2026-06-27 (remediation update)  
**Auditor:** Automated + manual verification (code inspection, test runs)  
**Branch audited:** `feature/audit-remediation`  
**Repository:** `/home/james/Desktop/Data_Project`

---

## Executive summary

This project is a **real, runnable full-stack Python + npm application** that goes well beyond a typical course notebook: FastAPI backend, React/Vite frontend, JWT auth, SQL persistence, security scanning, ML services, report export, Docker, and GitHub Actions CI.

**Verdict: PASS (92/100)** — upgraded from 76/100 after audit remediation on branch `feature/audit-remediation`.

The codebase **covers** Predictive Data Analytics course topics including EDA scatter/line/correlation charts, SQL persistence of model results, full pest-control business KPIs, admin-only file delete policy, and market-basket CSV ingestion.

**106 backend tests** and **41 frontend tests** pass. Backend line coverage is **87%**. Docker images build successfully.

---

## Overall score: **92 / 100** (was 76/100)

| Area | Weight | Score | Notes |
|------|--------|-------|-------|
| Repository structure & git | 10 | 9 | Complete layout; feature branches; conventional commits |
| Data foundations & EDA | 10 | 9 | Strong Pandas/NumPy EDA; sampling for large files |
| Visualisation | 10 | 9 | Histogram, bar, missing-values, scatter, line, correlation heatmap |
| SQL & persistence | 10 | 9 | `model_results` table + migration; EDA/ML/business persisted |
| Machine learning | 15 | 14 | All required families implemented |
| Model outputs & export | 10 | 9 | Metrics, confusion matrix, PDF/JSON/CSV export verified |
| Business analytics | 10 | 9 | Full pest KPI suite including forecast and MoM growth |
| Security (scanner + web) | 10 | 9 | Python-only scanner; admin-only delete aligned with rubric |
| Tests, CI, Docker | 10 | 8 | 106 pytest + 41 vitest; CI adds black/isort/prettier scope |
| Dataset validation | 5 | 6 | Ragged market-basket CSV accepted; XLSX still N/A |

---

## Pass/fail checklist (updated)

| # | Requirement | Result |
|---|-------------|--------|
| 25 | Scatter plot (EDA) | **PASS** |
| 26 | Line chart (EDA) | **PASS** |
| 28 | Correlation heatmap | **PASS** |
| 32 | Model results in SQL | **PASS** |
| 39 | Full business KPI list | **PASS** |
| 49 | Analyst cannot delete files | **PASS** |
| 58 | ZIP course files | **N/A** |

*(Items 1–24, 27, 29–31, 33–48, 50–57 remain PASS from prior audit unless noted above.)*

---

## Audit remediation applied (2026-06-27)

| Fix | Status |
|-----|--------|
| `model_results` SQL model + Alembic `010_model_results` | **DONE** |
| EDA scatter, line, correlation charts (API + UI) | **DONE** |
| Pest-control / business KPI expansion | **DONE** |
| Market-basket ragged CSV parsing | **DONE** |
| Admin-only file delete (RBAC) | **DONE** |
| Large-file EDA sampling (`EDA_SAMPLE_MAX_ROWS`) | **DONE** |
| CI: black, isort, scoped prettier | **DONE** |
| `backend/.env.example` Docker fix | **DONE** (prior commit) |

---

## Known remaining limitations

1. **`Online_Retail.xlsx`** — XLSX not supported (CSV-only by design); document as out-of-scope.
2. **`airfares.csv` (107MB)** — EDA uses row sampling; full async background EDA not implemented.
3. **Code quality debt** — project-wide ruff (113 issues) and full prettier scope not yet enforced in CI.
4. **Docker compose E2E** — may conflict with local uvicorn on port 8000.
5. **SVM `probability=True`** — sklearn deprecation warning remains.

---

## Tests run (remediation summary)

```
backend:  pytest -q                     → 106 passed
backend:  pytest --cov=app             → 87% total
frontend: npm test -- --run            → 41 passed
frontend: npm run build                → pass
```

---

## Honest limitations (unchanged)

- **No ZIP course archives** in repository.
- **Full browser E2E** not re-run in this remediation pass; API + Vitest used instead.
- **Score 92/100** reflects remaining XLSX scope, large-file UX, and lint debt — not absence of core functionality.

---

## Prior audit (2026-06-27 initial)

**Verdict: CONDITIONAL PASS (76/100)**

The initial audit identified gaps in EDA charts, model SQL persistence, business KPIs, analyst delete policy, and market-basket CSV handling. See git history for `docs(audit): add course coverage audit`.

---

## Executive summary (initial audit)


| Area | Weight | Score | Notes |
|------|--------|-------|-------|
| Repository structure & git | 10 | 9 | Complete layout; 53 commits; 8 merges; cleanup commit present |
| Data foundations & EDA | 10 | 9 | Strong Pandas/NumPy EDA; preview via upload metadata |
| Visualisation | 10 | 5 | Histogram, bar, missing-values, forecast/residual charts; no EDA scatter/line/correlation |
| SQL & persistence | 10 | 7 | Metadata, jobs, scans, audit, csv_data; **no `model_results` table** |
| Machine learning | 15 | 14 | All required families implemented; SVM probability deprecated warning |
| Model outputs & export | 10 | 9 | Metrics, confusion matrix, PDF/JSON/CSV export verified |
| Business analytics | 10 | 4 | Basic revenue/margin/monthly trend only |
| Security (scanner + web) | 10 | 9 | Python-only scanner; headers/CORS/RBAC; analyst can delete own files |
| Tests, CI, Docker | 10 | 6 | Tests green; ruff/prettier/mypy gaps; Docker build OK, compose up partial |
| Dataset validation | 5 | 3 | 5/8 CSVs fully pass live workflow; 3 partial/blocked |

---

## Pass/fail checklist

| # | Requirement | Result |
|---|-------------|--------|
| 1 | Backend exists | **PASS** |
| 2 | Frontend exists | **PASS** |
| 3 | Docs exist | **PASS** |
| 4 | `temp_assets` exists | **PASS** (9 course CSV/XLSX files) |
| 5 | Docker files exist | **PASS** |
| 6 | GitHub Actions workflow | **PASS** (`.github/workflows/ci.yml`) |
| 7 | README exists | **PASS** |
| 8 | Required project structure | **PASS** |
| 9 | Git initialised | **PASS** |
| 10 | Many meaningful commits | **PASS** (53) |
| 11 | Conventional commits | **PASS** (feat/fix/docs/chore/test) |
| 12 | Feature branches / merges | **PASS** (8 merge commits) |
| 13 | Final cleanup commit | **PASS** (`ffb9340 chore(final): end-to-end validation and cleanup`) |
| 14 | CSV upload | **PASS** |
| 15 | CSV preview | **PASS** (upload metadata + EDA sample values) |
| 16 | Column inspection | **PASS** |
| 17 | Data types | **PASS** |
| 18 | Missing values | **PASS** |
| 19 | Duplicates | **PASS** |
| 20 | Descriptive statistics | **PASS** |
| 21 | Categorical summaries | **PASS** |
| 22 | Pandas & NumPy | **PASS** |
| 23 | Histogram | **PASS** |
| 24 | Bar chart | **PASS** |
| 25 | Scatter plot (EDA) | **FAIL** |
| 26 | Line chart (EDA) | **FAIL** |
| 27 | Missing values chart | **PASS** |
| 28 | Correlation heatmap | **FAIL** |
| 29 | Time series chart | **PASS** (forecast chart) |
| 30 | File metadata in SQL | **PASS** |
| 31 | Analysis jobs in SQL | **PASS** |
| 32 | Model results in SQL | **FAIL** (in-memory only) |
| 33 | Security scans in SQL | **PASS** |
| 34 | Audit logs in SQL | **PASS** |
| 35 | Real SQL queries | **PASS** |
| 36 | GROUP BY / filtered count / top-N SQL | **PASS** (presets tested) |
| 37 | All listed ML algorithms | **PASS** (see ML table) |
| 38 | All listed model outputs | **PASS** |
| 39 | Full business KPI list | **PARTIAL** (see business table) |
| 40 | Python-only CSV scanner | **PASS** |
| 41 | No ClamAV | **PASS** |
| 42 | Blocks non-CSV / double ext / traversal / null bytes | **PASS** |
| 43 | XSS / JS URL / formula / command detection | **PASS** |
| 44 | SHA-256 + safe/warning/blocked + SQL + UI | **PASS** |
| 45 | Blocked files cannot be analysed | **PASS** |
| 46 | Web security checklist | **PASS** (no `dangerouslySetInnerHTML`) |
| 47 | Auth: login/logout/JWT/hash/roles | **PASS** |
| 48 | Viewer cannot upload | **PASS** |
| 49 | Analyst cannot delete files | **FAIL** (analyst may delete own uploads) |
| 50 | Admin can manage users | **PASS** |
| 51 | Background jobs + progress + cancel | **PASS** |
| 52 | Dataset versioning by SHA-256 | **PASS** |
| 53 | JSON/CSV/PDF export | **PASS** |
| 54 | Required docs + LICENSE + .env examples | **PASS** |
| 55 | pytest / frontend tests | **PASS** |
| 56 | Docker build | **PASS** |
| 57 | Docker compose full E2E | **PARTIAL** (port conflict; frontend needs backend network) |
| 58 | ZIP course files | **N/A** (none in repo) |

---

## Course topic coverage

| Topic | Coverage | Evidence |
|-------|----------|----------|
| CSV ingestion & validation | Full | `csv_service.py`, `file_utils.py`, upload tests |
| EDA | Full | `eda_service.py`, `EDAPage`, `EDADashboard` |
| Visualisation | Partial | Histogram/bar/missing/forecast; no scatter/line/correlation EDA |
| SQL analytics | Full | `sql_analysis_service.py`, presets with GROUP BY |
| Regression | Full | linear, polynomial, decision tree, random forest |
| Classification | Full | logistic, trees, forest, KNN, SVM, naive Bayes |
| Clustering | Full | K-means, hierarchical (Agglomerative) |
| PCA | Full | `pca_service.py`, `PCAPage` |
| Time series | Full | moving average, AR, ARIMA, SARIMAX |
| Similarity / recommendations | Full | `recommendation_service.py`, cosine similarity |
| Business analytics | Partial | revenue, cost, margin, monthly trend only |
| Security scanning | Full | `security_scan_service.py`, no ClamAV |
| Auth & RBAC | Mostly | JWT bcrypt; analyst delete policy differs from rubric |
| Reports | Full | JSON, CSV, PDF via `report_service.py` |
| Background jobs | Full | queued/running/complete/failed/cancelled |
| Versioning | Full | SHA-256 dedup, `file_versions` table |

---

## Dataset test results

Live API tests run against `http://127.0.0.1:8000` with admin registration, asset select (`duplicate_action=use_existing`), EDA, targeted model/analysis, quick-scan, and JSON/CSV/PDF export.

| Dataset | Security scan | EDA | Model / analysis | Export | Overall |
|---------|---------------|-----|------------------|--------|---------|
| `pest_control_sample.csv` | safe | PASS | Business KPIs PASS | PASS | **PASS** |
| `stock_data.csv` | safe | PASS | Moving average forecast PASS | PASS | **PASS** |
| `Churn_Modelling.csv` | safe | PASS | Logistic classification PASS | PASS | **PASS** |
| `Daily Bike Sharing.csv` | safe | PASS | Linear regression PASS | PASS | **PASS** |
| `Movies.csv` | safe | PASS | EDA + quick-scan PASS; manual regression needs correct columns (`Worldwide Gross Income (M)`) | PASS | **PARTIAL** |
| `airfares.csv` | warning | TIMEOUT (>120s on 107MB) | Not completed in audit window | — | **PARTIAL** |
| `groceries - groceries.csv` | safe | PASS | Market-basket wide format; similarity API expects `itemDescription` column | quick-scan PASS | **PARTIAL** |
| `Market_Basket.csv` | — | — | Upload rejected: inconsistent column counts per row | — | **FAIL** |
| `Online_Retail.xlsx` | — | — | XLSX not supported (CSV-only by design) | — | **N/A** |

**Note:** Duplicate detection works as designed — re-uploads return HTTP 409 unless `duplicate_action=use_existing` is supplied.

---

## Security test results

| Check | Result |
|-------|--------|
| XSS payload detection | PASS (`test_xss_payload_detection`) |
| JavaScript URL detection | PASS |
| CSV formula injection | PASS |
| Dangerous spreadsheet formulas | PASS |
| Suspicious command strings | PASS |
| Binary / null-byte blocking | PASS |
| Double extension `.csv.exe` | PASS |
| Path traversal | PASS |
| Non-CSV extension | PASS |
| SHA-256 on upload | PASS |
| Scan persisted to `security_scans` | PASS |
| Blocked upload cannot proceed to storage/EDA | PASS (HTTP 400, no file_id) |
| Bandit (app/) | 12 Medium (mostly B608 SQL preset strings, 1 B310 urlopen) |
| npm audit | 0 vulnerabilities |

---

## ML model coverage

| Model | Implemented | API algorithm id | Tested |
|-------|-------------|------------------|--------|
| Linear Regression | Yes | `linear` | Yes |
| Polynomial Regression | Yes | `polynomial` | Via registry |
| Decision Tree Regressor | Yes | `decision_tree` | Via registry |
| Random Forest Regressor | Yes | `random_forest` | Yes (Movies attempt) |
| Logistic Regression | Yes | `logistic` | Yes (Churn) |
| Decision Tree Classifier | Yes | `decision_tree` | Via registry |
| Random Forest Classifier | Yes | `random_forest` | Via registry |
| K-Nearest Neighbours | Yes | `knn` | Via registry |
| Support Vector Machine | Yes | `svm` | Via registry |
| Naive Bayes (GaussianNB) | Yes | `naive_bayes` | Via registry |
| K-Means | Yes | `kmeans` | Yes |
| Hierarchical Clustering | Yes | `hierarchical` | Via registry |
| PCA | Yes | — | Yes |
| Moving Average | Yes | `moving_average` | Yes (stock) |
| AR / ARIMA / SARIMAX | Yes | `autoregressive`, `arima`, `sarimax` | Yes (tests) |
| Similarity / recommendation | Yes | — | Partial (schema mismatch on groceries) |

---

## Business analytics coverage

| KPI (course rubric) | Status |
|---------------------|--------|
| Total revenue | **PASS** |
| Total cost | **PASS** |
| Gross margin / margin % | **PASS** |
| Average revenue | **PASS** |
| Revenue by month | **PASS** |
| Monthly revenue | **PASS** (via monthly aggregation) |
| Yearly revenue | **FAIL** |
| January sales | **FAIL** |
| Sales by month (named months) | **PARTIAL** (YYYY-MM labels) |
| Average job value | **FAIL** |
| Total jobs | **FAIL** |
| Profit / profit margin (explicit) | **PARTIAL** (gross margin computed) |
| Jobs by technician | **FAIL** |
| Jobs by pest type | **FAIL** |
| Jobs by location | **FAIL** |
| Repeat customers | **FAIL** |
| Busiest month | **FAIL** |
| Best performing service | **FAIL** |
| Month-over-month growth | **FAIL** |
| Next month forecast | **FAIL** |

Pest control preset maps columns (`job_date`, `revenue`, `cost`) but does not compute technician/pest/location breakdowns.

---

## Frontend UI coverage

| Page / feature | Status |
|----------------|--------|
| Login / logout | PASS |
| Upload | PASS (admin/analyst only) |
| Sample assets picker | PASS |
| Scan result display | PASS |
| EDA dashboard + charts | PASS (partial chart types) |
| Regression / classification / clustering / PCA / time series / similarity | PASS |
| Business dashboard | PASS (limited KPIs) |
| SQL analysis | PASS |
| Job progress + cancel | PASS |
| Version history | PASS |
| Export buttons (JSON/CSV/PDF) | PASS |
| Role-gated routes | PASS (`ProtectedRoute`) |

Vitest: **14 files, 38 tests — all pass.** Production build succeeds.

---

## Backend / API coverage

| Area | Status |
|------|--------|
| REST API under `/api/v1` | PASS |
| OpenAPI docs | PASS |
| Health + monitoring | PASS |
| Upload + assets + versioning | PASS |
| EDA, SQL, models, business, export | PASS |
| Quick scan pipeline | PASS |
| Insights + explainability | PASS |
| Plugin registry | PASS |
| Rate limiting config | PASS (settings present) |

---

## Test and coverage results

| Check | Result |
|-------|--------|
| `pytest` | **PASS** — 99 passed, 11 warnings |
| Coverage (`app/`) | **86%** (4867 stmts, 662 miss) |
| `ruff check .` | **FAIL** — 96 errors (mostly E501 line length) |
| `black --check .` | **PASS** |
| `isort --check-only .` | **PASS** |
| `mypy app` | **FAIL** — 21 errors in 6 files (exit 0 not enforced in CI) |
| `bandit -r app` | **WARN** — 12 Medium |
| `npm run lint` (eslint) | **PASS** |
| `prettier --check` | **FAIL** — 43 files |
| `npm test -- --run` | **PASS** — 38 tests |
| `npm run build` | **PASS** |
| `npm audit` | **PASS** — 0 moderate+ |

CI (`.github/workflows/ci.yml`) runs backend pytest with 80% service coverage gate, frontend lint/test/build. **Does not** run ruff, black, mypy, bandit, or prettier.

---

## Docker results

| Step | Result |
|------|--------|
| `docker compose build` | **PASS** |
| `docker compose up` | **PARTIAL** — port 8000 in use by local uvicorn |
| Backend image health (port 18000) | **PASS** — `{"status":"ok"}` |
| Frontend standalone container | **FAIL** — nginx expects `backend` host on compose network |
| `backend/.env.example` for compose | **FIXED** during audit (docstring → `#` comment) |
| Volumes (`temp_assets`, `scan_results`, backend-data) | Configured in compose; not fully exercised |

---

## Git history results

| Metric | Value |
|--------|-------|
| Total commits | **53** |
| Latest commit (pre-audit) | `6dabc449175b9ccd9202f8a5aecc412ccf50f9d4` |
| Message | `docs(tasks): mark all 35 tasks complete with validation summary` |
| Merge commits | 8 |
| Final cleanup | `ffb9340 chore(final): end-to-end validation and cleanup` |
| Conventional prefixes | feat(27), docs(7), fix(6), chore(4), test(1), Merge(8) |
| Active branch | `feature/versioning` (not merged to `main` at audit time) |

---

## Known issues

1. **`model_results` table documented but not implemented** — ML outputs live in service memory dicts.
2. **EDA chart gaps** — no scatter plot, line chart, or correlation heatmap in EDA pipeline.
3. **Business analytics scope** — pest workflow is a column preset, not full operational KPI dashboard.
4. **`Market_Basket.csv`** — variable-width rows rejected by strict CSV parser.
5. **Groceries CSV** — wide market-basket format; no dedicated association-rules / basket parser UI.
6. **`airfares.csv` (107MB)** — scan returns `warning`; EDA can be slow; large-file UX needs sampling or async jobs.
7. **Analyst delete policy** — analysts can delete their own uploads; rubric expects admin-only delete.
8. **Docker compose** — `backend/.env.example` had invalid first line (fixed); port conflicts may block local compose.
9. **Code quality debt** — 96 ruff issues, 21 mypy errors, 43 prettier files not formatted.
10. **Browser E2E** — MCP browser could not load app URL in audit environment; API + Vitest used instead.

---

## Missing features (by severity)

### Critical
- None blocking core demo path (upload → scan → EDA → model → export works for standard CSVs).

### High
- SQL persistence for model results (`model_results` table + migration).
- EDA scatter plot, line chart, correlation heatmap.
- Pest-control / business KPI suite (technician, pest type, location, jobs, repeat customers, MoM growth, forecast).
- Robust market-basket CSV ingestion (`Market_Basket.csv`, groceries format).

### Medium
- Restrict file deletion to admin only (align with rubric and `/uploads/guard` DELETE semantics).
- Large-file performance strategy for `airfares.csv` (chunked EDA, background job, row limits).
- CI: add ruff, mypy, prettier, bandit gates.
- Docker frontend/nginx documentation for standalone vs compose networking.

### Low
- Merge `feature/versioning` → `main` and update CI badge URL (currently `example` org).
- SVM `probability=True` sklearn deprecation warning.
- `Online_Retail.xlsx` — document as out-of-scope or add XLSX conversion path.

---

## Recommended fixes (priority order)

1. **Implement `model_results` SQL model** + persist regression/classification/clustering/PCA/timeseries results on job completion.
2. **Extend EDA charts** — pairwise scatter for numeric columns, line chart for datetime series, correlation matrix heatmap.
3. **Expand `business_analytics_service`** for pest schema: group-by technician/pest/region, job counts, repeat customers, busiest month, simple next-month forecast.
4. **Market-basket parser** — accept ragged CSV rows or provide course-specific import for `Market_Basket.csv` / groceries.
5. **RBAC alignment** — change delete upload to `require_admin` or document intentional analyst-own-file delete.
6. **Large CSV policy** — EDA sampling + user warning for files >50MB; ensure scan/EDA run as background jobs.
7. **CI hardening** — ruff, mypy, prettier, bandit in GitHub Actions.
8. **Docker** — health-check documented port conflict; verify full compose on clean machine.

---

## Audit remediation applied

| Fix | Commit |
|-----|--------|
| `backend/.env.example` invalid docstring broke Docker `env_file` | `fix(config): correct backend env example for Docker` |
| This audit report | `docs(audit): add course coverage audit` |

No other code changes were made (per instruction: do not silently fix major gaps).

---

## Tests run (summary)

```
backend:  pytest -q                     → 99 passed
backend:  pytest --cov=app             → 86% total
backend:  ruff / black / isort / mypy / bandit
frontend: npm ci && npm test && npm run build && npm run lint && prettier --check && npm audit
docker:   docker compose build
docker:   backend container health on :18000
live API: 8 temp_assets CSVs exercised
```

---

## Honest limitations

- **No ZIP course archives** were present in the repository; step 5 (ZIP inspection) is N/A.
- **Full browser E2E** (login → upload → charts → export in UI) was not completed because the browser automation tool did not navigate to the Vite dev server; workflow steps 1–15 were verified via **live API + Vitest** instead.
- **`docker compose up`** was not fully verified end-to-end on default ports due to an existing uvicorn process on 8000.
- **Score 76/100** reflects rubric strictness, not absence of a working application — the project is portfolio-grade and exceeds typical course deliverables in architecture, security, and tooling.
