#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Backend tests + coverage =="
cd "$ROOT/backend"
.venv/bin/pytest -q --cov=app/services --cov-report=term --cov-fail-under=80

echo "== Frontend lint, test, build =="
cd "$ROOT/frontend"
npm run lint
npm run test -- --run
npm run build

echo "== Alembic head =="
cd "$ROOT/backend"
.venv/bin/alembic upgrade head

echo "Validation complete."
