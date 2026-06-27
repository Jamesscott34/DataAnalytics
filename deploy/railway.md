# Railway deployment

## Backend service

1. Create a Railway project and add a Python service from this repository.
2. Set the root directory to `backend`.
3. Configure environment variables from `backend/.env.example`:
   - `DATABASE_URL` (PostgreSQL recommended for production)
   - `JWT_SECRET_KEY`
   - `CORS_ORIGINS` (your frontend URL)
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Run migrations on deploy: `alembic upgrade head`

## Frontend service

1. Add a static site or Node build service with root directory `frontend`.
2. Build command: `npm ci && npm run build`
3. Publish directory: `dist`
4. Set `VITE_API_BASE_URL` or configure reverse proxy to the backend `/api/v1` prefix.

## Smoke checks

- `GET /api/v1/health` returns `{ "status": "ok" }`
- Login, upload CSV, run quick scan, export Markdown/PDF
