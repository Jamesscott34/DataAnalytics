# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Background EDA jobs for files above 50MB with job progress polling (`job_type: eda`).
- XLSX upload and temp-asset conversion endpoints (`POST /uploads/xlsx`, `POST /assets/convert-xlsx`).
- Playwright E2E suite (`e2e/`) covering upload → EDA → quick-scan → JSON export.
- CI enforcement for ruff, mypy, bandit, and Playwright E2E.

### Added (prior audit remediation)
- EDA dataset charts: scatter plots, line charts, and correlation heatmaps (backend + React components).
- Expanded pest-control business KPIs: yearly revenue, January sales, technician/pest/location breakdowns, repeat customers, MoM growth, next-month forecast.
- Ragged CSV / market-basket parsing with column padding for variable-width transaction rows.
- EDA row sampling for large files (`EDA_SAMPLE_MAX_ROWS` config).
- CI: Black, isort, and scoped Prettier checks for chart components.

### Changed

- File deletion restricted to administrators only (aligns with course RBAC rubric).
- Business and model `get_result` endpoints reload results from SQL when in-memory cache is cleared.

### Added (prior)

- Phase 0 planning documents: architecture, API design, database schema, component tree, task list.
- FastAPI backend with `/api/v1/health` liveness endpoint.
- React Vite frontend shell with health status panel and Vitest tests.
- SQLAlchemy models (users, sessions, uploaded files stub) and Alembic migration `001_initial`.
- Pydantic settings, JSON logging, security headers, and standard error responses.
- JWT authentication with refresh tokens, RBAC (admin/analyst/viewer), and login UI.
- Secure CSV upload endpoint with filename validation, size checks, SHA-256 deduplication, and upload UI.
- Python-only CSV security scanner with persisted scan results and UI status panel.
