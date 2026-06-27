# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-06-27

First stable release of the Predictive Data Analytics Platform.

### Added

- Full-stack analytics workflow: upload, security scan, EDA, ML, SQL, business KPIs, and export.
- JWT authentication with refresh tokens, RBAC (admin/analyst/viewer), and user management.
- Python-only CSV security scanner with risk scoring and persisted scan results.
- Exploratory data analysis with charts, caching, sampling, and background jobs for large files.
- Machine learning: regression, classification, clustering, PCA, time series, similarity, and plugins.
- Business analytics with pest-control preset and expanded KPI calculations.
- SQL analysis with presets, dataset groups, and read-only validated queries.
- Background job queue with progress polling and cancellation.
- Asset integrity manifest for bundled datasets.
- XLSX upload and temp-asset conversion endpoints.
- JSON, CSV, and PDF export pipeline.
- Monitoring, audit logging, and structured JSON logs.
- React SPA with Recharts dashboards and role-aware UI.
- Docker Compose deployment and Railway guide.
- `setup.sh` one-command local development bootstrap.
- 128+ backend tests, 41+ frontend tests, and CI for lint, type check, and coverage.

### Changed

- File deletion restricted to administrators only.
- Business and model `get_result` endpoints reload results from SQL when in-memory cache is cleared.
- CI runs backend and frontend checks; Playwright E2E remains available locally only.

[1.0.0]: https://github.com/Jamesscott34/DataAnalytics/releases/tag/v1.0.0
