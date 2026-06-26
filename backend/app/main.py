"""FastAPI application entry point.

Configures the ASGI app, registers API routers under ``/api/v1``, and applies
middleware. Does not contain business logic or route handlers beyond wiring.
"""

from fastapi import FastAPI

from app.routers import health

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="Predictive Security Analytics Lab",
    version="0.1.0",
    docs_url=f"{API_V1_PREFIX}/docs",
    openapi_url=f"{API_V1_PREFIX}/openapi.json",
)

app.include_router(health.router, prefix=API_V1_PREFIX)
