"""FastAPI application factory and lifecycle management."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.model_service import model_service

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting ColPali service")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Model ID: {settings.MODEL_ID}")

    # Load model
    model_service.load_model()

    yield

    # Shutdown
    logger.info("Shutting down ColPali service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ColModernVBert Embedding API",
        description="API for generating embeddings from images and queries",
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
    # Note: Import middleware locally to avoid circular imports if they reference the app
    from middleware.request_id import RequestIDMiddleware
    from middleware.timing import TimingMiddleware

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)

    # Include routers
    app.include_router(router)

    return app


# Create the app instance
app = create_app()
