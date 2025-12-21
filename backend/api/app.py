import logging

from api.routers import (
    config,
    files,
    indexing,
    interpretability,
    maintenance,
    meta,
    ocr,
    retrieval,
)
from config import ALLOWED_ORIGINS
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from middleware.request_id import RequestIDMiddleware
from middleware.timing import TimingMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Vision RAG API", version="1.0.0")

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

    # Middleware (order matters - first added = outermost layer)
    # 1. Request ID middleware (must be first for all logs to have request_id)
    app.add_middleware(RequestIDMiddleware)

    # 2. Timing middleware (logs request duration)
    app.add_middleware(TimingMiddleware)

    # 3. CORS (adjust origins for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=(ALLOWED_ORIGINS != ["*"]),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(meta.router)
    app.include_router(retrieval.router)
    app.include_router(indexing.router)
    app.include_router(maintenance.router)
    app.include_router(config.router)
    app.include_router(ocr.router)
    app.include_router(interpretability.router)
    app.include_router(files.router)

    return app
