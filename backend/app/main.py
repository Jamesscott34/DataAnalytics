"""FastAPI application entry point.

Configures the ASGI app, registers API routers under ``/api/v1``, and applies
middleware. Does not contain business logic or route handlers beyond wiring.
"""

from collections.abc import AsyncIterator

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.timing import RequestTimingMiddleware
from app.routers import health

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle hooks."""
    configure_logging()
    yield


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

    return app


app = create_app()
