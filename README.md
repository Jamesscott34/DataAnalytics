# predictive-security-analytics-lab

![CI](https://github.com/example/predictive-security-analytics-lab/actions/workflows/ci.yml/badge.svg)

Portfolio-grade full-stack analytics platform: secure CSV ingestion, exploratory data analysis, predictive ML, SQL analytics, business KPIs, AI insights, and professional report export.

## Planning documents

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture diagram and layer responsibilities |
| [docs/API.md](docs/API.md) | Full REST API endpoint catalogue |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | ER diagram, tables, Alembic migration plan |
| [docs/COMPONENT_TREE.md](docs/COMPONENT_TREE.md) | React pages, components, hooks, and data flow |
| [docs/TASKS.md](docs/TASKS.md) | 35-task implementation plan mapped to git branches |
| [docs/TESTING.md](docs/TESTING.md) | Backend and frontend test strategy |
| [docs/DATA_WORKFLOW.md](docs/DATA_WORKFLOW.md) | End-to-end analysis workflow |
| [docs/SECURITY.md](docs/SECURITY.md) | Security model and scanner behaviour |
| [docs/MODELS.md](docs/MODELS.md) | ML model families and explainability matrix |

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy · Alembic · Pandas · scikit-learn · React · Vite · Docker · GitHub Actions

## Quick start

```bash
# Backend
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

Docker:

```bash
docker compose up --build
```

Open http://localhost:5173 (frontend) and http://localhost:8000/api/v1/docs (API).

## Validation

```bash
chmod +x scripts/validate.sh
./scripts/validate.sh
```

## Deployment

See [deploy/railway.md](deploy/railway.md) for Railway deployment notes.

## Licence

MIT (see [LICENSE](LICENSE)).

## Development status

All 35 implementation tasks are complete on branch `feature/versioning`. Task detail and commit mapping: [docs/TASKS.md](docs/TASKS.md).
