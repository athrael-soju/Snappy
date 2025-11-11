"""FastAPI application factory for DuckDB analytics."""

from __future__ import annotations

from contextlib import asynccontextmanager

from app.api.routes import router
from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import logger
from fastapi import FastAPI


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

    app.include_router(router)
    return app
