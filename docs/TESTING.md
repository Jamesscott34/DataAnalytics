# Testing

## Backend

- Framework: pytest
- Location: `backend/tests/`
- Coverage target: **80%+ on `app/services/`**

```bash
cd backend
.venv/bin/pytest -q
.venv/bin/pytest -q --cov=app/services --cov-report=term --cov-fail-under=80
```

Key suites: auth, upload/security scan, EDA, SQL, regression/classification/clustering/PCA/time series, similarity, explainability, business analytics, insights, export, background jobs, plugins, monitoring.

## Frontend

- Framework: Vitest + Testing Library
- Location: `frontend/src/**/*.test.jsx`

```bash
cd frontend
npm run lint
npm run test -- --run
npm run build
```

## CI

GitHub Actions workflow `.github/workflows/ci.yml` runs backend coverage, frontend lint/test/build on push and pull requests.

## Pre-commit (recommended)

- Backend: ruff, black, isort, mypy, bandit
- Frontend: eslint, prettier

See [TASKS.md](./TASKS.md) for per-task test requirements.
