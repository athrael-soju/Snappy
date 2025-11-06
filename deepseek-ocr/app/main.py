"""
FastAPI application factory and lifecycle management.
"""

from contextlib import asynccontextmanager

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.services.model_service import model_service
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    logger.info("")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 12 + "DeepSeek OCR Service Starting" + " " * 16 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")

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
