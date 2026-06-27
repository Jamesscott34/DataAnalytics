"""FastAPI application entry point.

Configures the ASGI app, registers API routers under ``/api/v1``, and applies
middleware. Does not contain business logic or route handlers beyond wiring.
"""

import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.timing import RequestTimingMiddleware
from app.routers import (
    asset_integrity,
    assets,
    audit,
    auth,
    business,
    eda,
    explainability,
    export,
    groups,
    health,
    insights,
    jobs,
    models_regression,
    monitoring,
    plugins,
    quick_scan,
    scans,
    sql,
    uploads,
    users,
)

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle hooks."""
    configure_logging()
    from app.services.asset_integrity_service import asset_integrity_service

    # Hash watched asset folders in the background so login/API are not blocked
    # while large CSV/XLSX files in temp_assets are scanned.
    threading.Thread(
        target=asset_integrity_service.refresh_disk_scan,
        name="asset-integrity-scan",
        daemon=True,
    ).start()
    yield
    asset_integrity_service.lock_manifest()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance.

    Returns:
        Configured FastAPI app with routers, middleware, and error handlers.
    """
    settings = get_settings()

    app = FastAPI(
        title="Predictive Security Analytics Lab",
        version="0.1.0",
        docs_url=f"{API_V1_PREFIX}/docs",
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestTimingMiddleware)

    register_exception_handlers(app)
    app.include_router(health.router, prefix=API_V1_PREFIX)
    app.include_router(monitoring.router, prefix=API_V1_PREFIX)
    app.include_router(auth.router, prefix=API_V1_PREFIX)
    app.include_router(users.router, prefix=API_V1_PREFIX)
    app.include_router(uploads.router, prefix=API_V1_PREFIX)
    app.include_router(assets.router, prefix=API_V1_PREFIX)
    app.include_router(asset_integrity.router, prefix=API_V1_PREFIX)
    app.include_router(audit.router, prefix=API_V1_PREFIX)
    app.include_router(jobs.router, prefix=API_V1_PREFIX)
    app.include_router(scans.router, prefix=API_V1_PREFIX)
    app.include_router(eda.router, prefix=API_V1_PREFIX)
    app.include_router(business.router, prefix=API_V1_PREFIX)
    app.include_router(groups.router, prefix=API_V1_PREFIX)
    app.include_router(sql.router, prefix=API_V1_PREFIX)
    app.include_router(models_regression.router, prefix=API_V1_PREFIX)
    app.include_router(plugins.router, prefix=API_V1_PREFIX)
    app.include_router(explainability.router, prefix=API_V1_PREFIX)
    app.include_router(quick_scan.router, prefix=API_V1_PREFIX)
    app.include_router(insights.router, prefix=API_V1_PREFIX)
    app.include_router(export.router, prefix=API_V1_PREFIX)

    return app


app = create_app()
