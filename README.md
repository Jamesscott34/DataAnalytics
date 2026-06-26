# predictive-security-analytics-lab

Portfolio-grade full-stack analytics platform: secure CSV ingestion, exploratory data analysis, predictive ML, SQL analytics, business KPIs, and professional report export.

**Current phase:** Phase 2 — Task 9 (`temp_assets` selector) next.

## Planning documents

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture diagram and layer responsibilities |
| [docs/API.md](docs/API.md) | Full REST API endpoint catalogue |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | ER diagram, tables, Alembic migration plan |
| [docs/COMPONENT_TREE.md](docs/COMPONENT_TREE.md) | React pages, components, hooks, and data flow |
| [docs/TASKS.md](docs/TASKS.md) | 35-task implementation plan mapped to git branches |

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy · Alembic · Pandas · scikit-learn · React · Vite · Recharts · Docker · GitHub Actions

## Licence

MIT (see [LICENSE](LICENSE)).

## Development status

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Planning docs | Done |
| 1 | Tasks 1–5 — scaffold, API, frontend shell, DB, config | Done |
| 2 | Tasks 6–11 — auth, upload, scanner, assets, audit, versioning | In progress (Tasks 6–8 done) |
| 3 | Tasks 12–19 — EDA, SQL, ML models | Pending |
| 4 | Tasks 20–25 — explainability, business, charts, export | Pending |
| 5 | Tasks 26–28 — jobs, plugins, monitoring | Pending |
| 6 | Tasks 29–35 — tests, CI, Docker, deploy, validation | Pending |

Task detail and commit mapping: [docs/TASKS.md](docs/TASKS.md).
