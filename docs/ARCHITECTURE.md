# Architecture — predictive-security-analytics-lab

> Phase 0 planning document (0.1). Implementation follows approval of this plan.

## System overview

Full-stack analytics platform: users authenticate, upload or select CSV datasets, pass a Python-only security scan, run EDA / SQL / ML / business analytics, view results in React, and export reports. Background jobs handle long-running work; audit and versioning track every action.

## Architecture diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS / OPERATORS                                 │
│         Browser (React + Vite)  │  CI/CD  │  Cloud monitors / load balancers    │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT TARGET (choose one)                           │
│  ┌──────────────┐   Railway / Render / Azure App Service / VPS + Docker Compose │
│  │   nginx:80   │   TLS termination at edge (production)                         │
│  └──────┬───────┘                                                                │
└─────────┼──────────────────────────────────────────────────────────────────────┘
          │
          │  /          → static React build (SPA)
          │  /api/v1/*  → reverse proxy
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │ pages/      │  │ components/  │  │ hooks/      │  │ api/ (sole HTTP layer)│ │
│  │ charts/     │  │ types/       │  │ Recharts    │  │ JWT in Authorization  │ │
│  └─────────────┘  └──────────────┘  └─────────────┘  └────────────────────────┘ │
│  Security: no dangerouslySetInnerHTML, escaped CSV display, client upload checks  │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │ REST JSON /api/v1/
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY & EDGE LAYER (backend)                          │
│  ┌────────────────┐ ┌─────────────────┐ ┌──────────────────────────────────┐  │
│  │ CORS (env)     │ │ Rate limiting   │ │ Response headers                  │  │
│  │ JWT auth deps  │ │ (upload/analyze)│ │ X-Content-Type-Options, CSP, etc. │  │
│  │ RBAC roles     │ │ slowapi         │ │ Request timing middleware         │  │
│  └────────────────┘ └─────────────────┘ └──────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI — Python 3.12)                             │
│  ┌──────────┐   ┌────────────┐   ┌─────────────────────────────────────────┐  │
│  │ main.py  │──▶│ routers/   │──▶│ services/ (business logic, ML, EDA, …)   │  │
│  │ middleware│  │ thin only  │   │ plugin_registry.py → extensible models   │  │
│  └──────────┘   └────────────┘   └─────────────────────────────────────────┘  │
│  ┌──────────┐   ┌────────────┐   ┌─────────────────────────────────────────┐  │
│  │ schemas/ │   │ auth/      │   │ utils/ (file, hash, encoding, …)        │  │
│  │ Pydantic │   │ JWT+bcrypt │   │ structured JSON logging                  │  │
│  └──────────┘   └────────────┘   └─────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Background: FastAPI BackgroundTasks (dev) │ Celery/RQ + Redis (prod opt.) │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└───────┬──────────────────────┬──────────────────────┬──────────────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌─────────────────────────────────┐
│ FILE STORAGE  │    │ DATABASE        │    │ EXTERNAL (optional)              │
│ upload volume │    │ SQLite (dev)    │    │ LLM API (insights, if key set)   │
│ temp_assets/  │    │ PostgreSQL      │    │                                  │
│ (read-only    │    │ (prod profile)  │    │                                  │
│  sample CSVs) │    │ SQLAlchemy +    │    │                                  │
│ SHA-256 dedup │    │ Alembic         │    │                                  │
└───────────────┘    └─────────────────┘    └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD (GitHub Actions)                              │
│  PR / push → lint (ruff, black, isort, mypy, bandit, eslint, prettier)          │
│           → pytest (backend 80%+ services) → vitest → vite build                │
│           → docker build smoke (optional job)                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE (local / deploy)                          │
│                                                                                  │
│   [frontend:nginx] ──proxy /api──▶ [backend:uvicorn] ──▶ [db:postgres] (opt.)   │
│                                         │                      ▲               │
│                                         ├── sqlite_data vol      │               │
│                                         ├── upload_data vol      │               │
│                                         └── redis] (opt. Celery)                 │
│                                                                                  │
│   Network: internal bridge; DB not exposed to host in production pattern          │
│   Backend runs as non-root user (appuser)                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Layer responsibilities

| Layer | Responsibility | Does not |
|-------|----------------|----------|
| Frontend | UX, charts, auth token storage, polling job progress | Direct DB access, server-side PDF |
| Routers | Validate input, call one service, map errors | Pandas/ML, SQL, business logic |
| Services | EDA, ML, scans, reports, insights | HTTP objects, raw router logic |
| Auth | JWT issue/validate, RBAC, password hash | Mixed into services |
| File storage | Persist uploads by hash path; serve metadata | Execute file content |
| DB | Users, files, jobs, results, audit, optional `csv_data` | Store duplicate file blobs |
| Security scanner | Defensive CSV validation (Python-only) | Antivirus, archive scan |

## Data flow (happy path)

1. User logs in → JWT + refresh token stored client-side.
2. User uploads CSV or selects from `temp_assets/`.
3. Upload service sanitises filename, checks size/extension, computes SHA-256.
4. Security scanner runs → `security_scans` + audit log.
5. If not `blocked`, EDA runs (cached by file hash where practical).
6. User picks analysis type (or accepts auto-detected suggestions).
7. `analysis_jobs` created → background worker runs service via plugin registry.
8. `job_progress` updated; frontend polls `/jobs/{id}`.
9. Results stored in `model_results`; insights generated (LLM or fallback).
10. User views dashboards; exports JSON/CSV/PDF via report service.

## Environment profiles

| Profile | DB | Background | Notes |
|---------|-----|------------|-------|
| `development` | SQLite file | BackgroundTasks | Local uvicorn + Vite dev server |
| `docker` | SQLite volume or Postgres profile | BackgroundTasks or RQ | `docker-compose up` |
| `production` | PostgreSQL | Celery/RQ + Redis | Secrets via platform env, no `.env` in images |

## Observability

- Application logs: JSON structured (`logging_config.py`).
- Audit logs: separate stream for upload/scan/analysis events (also persisted in `audit_logs`).
- `/api/v1/monitoring/health` — liveness + DB + disk (unauthenticated).
- `/api/v1/monitoring/metrics` — request counts, latency, errors, active jobs.
- `/api/v1/monitoring/db/stats` — table counts, slow query log entries.
- Middleware logs requests exceeding configurable threshold (default 2s).

## Security boundaries

- Uploaded files never under frontend `public/`.
- `temp_assets` listing resolves realpath and rejects traversal.
- All write/analysis endpoints require Analyst or Admin role except where noted.
- Monitoring health/metrics public for orchestrator health checks.

## Related documents

- [API.md](./API.md) — endpoint catalogue
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) — tables and migrations
- [COMPONENT_TREE.md](./COMPONENT_TREE.md) — React structure
- [TASKS.md](./TASKS.md) — implementation task list and git sequence
