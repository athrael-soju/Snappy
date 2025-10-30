"""
PaddleOCR-VL Service - FastAPI application entry point.

A GPU-accelerated document OCR service using PaddleOCR-VL for extracting text,
tables, charts, and formulas from documents.
"""

from contextlib import asynccontextmanager

import uvicorn
from config import get_logger, settings, setup_logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.api_models import HealthResponse
from routers import ocr_router
from services import paddleocr_vl_service


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    setup_logging()
    logger = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Application lifespan manager for startup and shutdown events.

        Startup:
        - Initialize logging
        - Log configuration
        - PaddleOCR-VL pipeline will be initialized lazily on first request

        Shutdown:
        - Cleanup resources
        """
        # Startup
        logger.info("=" * 80)
        logger.info(f"{settings.app_name} v{settings.app_version} - Starting up")
        logger.info("=" * 80)
        logger.info(f"GPU Enabled: {settings.use_gpu}")
        logger.info(f"Max Upload Size: {settings.max_upload_size / (1024*1024):.1f}MB")
        logger.info(
            "API Endpoint: http://%s:%s%s",
            settings.app_host,
            settings.app_port,
            settings.api_v1_prefix,
        )
        logger.info(
            "Note: PaddleOCR-VL pipeline will be initialized on first request (lazy loading)"
        )
        logger.info("=" * 80)

        yield

        # Shutdown
        logger.info("=" * 80)
        logger.info(f"{settings.app_name} - Shutting down")
        logger.info("=" * 80)

    app = FastAPI(
        title=settings.app_name,
        description="GPU-accelerated document OCR service using PaddleOCR-VL",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(ocr_router, prefix=settings.api_v1_prefix)

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """
        Health check endpoint.

        Returns service status, GPU availability, and pipeline readiness.
        """
        service_status = paddleocr_vl_service.get_status()

        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.app_version,
            gpu_enabled=service_status["gpu_enabled"],
            pipeline_ready=service_status["initialized"],
        )

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": f"{settings.api_v1_prefix}/docs",
            "health": "/health",
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error_type": type(exc).__name__,
            },
        )

    return app


# FastAPI instance used by ASGI servers
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
