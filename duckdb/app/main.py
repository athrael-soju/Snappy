"""FastAPI application factory for DuckDB analytics."""

from __future__ import annotations

from contextlib import asynccontextmanager

from app.api.routes import router
from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import logger
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database lifecycle."""
    logger.info("Starting DuckDB analytics service")
    db_manager.connect()

    logger.info("Service ready at http://%s:%s", settings.API_HOST, settings.API_PORT)

    try:
        yield
    finally:
        logger.info("Shutting down DuckDB analytics service")
        db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DuckDB Analytics Service",
        description="Columnar analytics storage for OCR data",
        version=settings.API_VERSION,
        lifespan=lifespan,
    )

    # Global exception handler for structured error logging
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Log unhandled exceptions with structured context."""
        logger.error(
            "Unhandled exception occurred",
            exc_info=exc,
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Add middleware (order matters - first added = outermost layer)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)

    app.include_router(router)
    return app
