"""
FastAPI application factory and lifecycle management.
"""

from contextlib import asynccontextmanager

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware
from app.services.model_service import model_service
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    logger.info("")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 12 + "DeepSeek OCR Service Starting" + " " * 16 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")

    # Patch model files for compatibility (if needed)
    try:
        from pathlib import Path
        import sys

        patch_script = Path(__file__).parent.parent / "patch_model.py"
        if patch_script.exists():
            logger.info("Running model compatibility patcher...")
            import subprocess
            result = subprocess.run(
                [sys.executable, str(patch_script)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✓ Model patcher completed")
            else:
                logger.warning(f"Model patcher warning: {result.stderr}")
    except Exception as e:
        logger.warning(f"Could not run model patcher: {e}")

    # Load model on startup
    try:
        model_service.load_model()

        # Display service info after successful load
        logger.info("")
        logger.info("Service Ready!")
        logger.info(f"→ API endpoint: http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info(
            f"→ Health check: http://{settings.API_HOST}:{settings.API_PORT}/health"
        )
        logger.info(f"→ Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Failed to load model during startup: {e}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("")
    logger.info("Shutting down DeepSeek OCR service")
    logger.info("")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="DeepSeek OCR Service",
        description="FastAPI service for DeepSeek-OCR document analysis",
        version="1.0.0",
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

    # CORS middleware
    origins = (
        settings.ALLOWED_ORIGINS.split(",")
        if settings.ALLOWED_ORIGINS != "*"
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    return app
