#!/usr/bin/env bash
# Install dependencies, configure environment files, migrate the database,
# and start the backend (background) + frontend (foreground).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT}/backend"
FRONTEND_DIR="${ROOT}/frontend"
VENV="${BACKEND_DIR}/.venv"
BACKEND_PID=""
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

log() {
  printf '\n==> %s\n' "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    log "Stopping backend (PID ${BACKEND_PID})"
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

install_only=false
if [[ "${1:-}" == "--install-only" ]]; then
  install_only=true
fi

log "Checking prerequisites"
require_cmd python3
require_cmd npm

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
log "Using Python ${PYTHON_VERSION}"

log "Creating backend virtual environment"
if [[ ! -d "${VENV}" ]]; then
  python3 -m venv "${VENV}"
fi

log "Installing backend dependencies"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" install -r "${BACKEND_DIR}/requirements-dev.txt"

log "Configuring backend environment"
if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
  cp "${BACKEND_DIR}/.env.example" "${BACKEND_DIR}/.env"
  log "Created backend/.env from .env.example"
else
  log "backend/.env already exists — leaving unchanged"
fi

if grep -q '^JWT_SECRET_KEY=change_me_to_random_string' "${BACKEND_DIR}/.env"; then
  if command -v openssl >/dev/null 2>&1; then
    SECRET="$("${VENV}/bin/python" -c 'import secrets; print(secrets.token_hex(32))')"
    sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${SECRET}/" "${BACKEND_DIR}/.env"
    log "Generated a random JWT_SECRET_KEY in backend/.env"
  fi
fi

log "Creating data directories"
mkdir -p "${BACKEND_DIR}/data/uploads" "${ROOT}/scan_results"

log "Running database migrations"
(
  cd "${BACKEND_DIR}"
  "${VENV}/bin/alembic" upgrade head
)

log "Installing frontend dependencies"
(
  cd "${FRONTEND_DIR}"
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
)

log "Configuring frontend environment"
if [[ ! -f "${FRONTEND_DIR}/.env" ]]; then
  cp "${FRONTEND_DIR}/.env.example" "${FRONTEND_DIR}/.env"
  log "Created frontend/.env from .env.example"
else
  log "frontend/.env already exists — leaving unchanged"
fi

if [[ "${install_only}" == true ]]; then
  log "Install complete (--install-only; servers not started)"
  echo ""
  echo "  Start manually:"
  echo "    cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port ${BACKEND_PORT}"
  echo "    cd frontend && npm run dev"
  exit 0
fi

log "Starting backend on http://127.0.0.1:${BACKEND_PORT}"
(
  cd "${BACKEND_DIR}"
  "${VENV}/bin/uvicorn" app.main:app --reload --host 127.0.0.1 --port "${BACKEND_PORT}"
) &
BACKEND_PID=$!

log "Waiting for backend health check"
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/monitoring/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/monitoring/health" >/dev/null 2>&1; then
  echo "Error: backend did not become healthy on port ${BACKEND_PORT}" >&2
  exit 1
fi

log "Backend is ready"
echo ""
echo "  API docs:  http://127.0.0.1:${BACKEND_PORT}/api/v1/docs"
echo "  Health:    http://127.0.0.1:${BACKEND_PORT}/api/v1/monitoring/health"
echo ""

log "Starting frontend on http://127.0.0.1:${FRONTEND_PORT}"
echo "  Press Ctrl+C to stop both servers"
echo ""

cd "${FRONTEND_DIR}"
npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}"
