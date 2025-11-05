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
    logger.info("Starting DeepSeek OCR service")

    # Load model on startup
    try:
        model_service.load_model()
    except Exception as e:
        logger.error(f"Failed to load model during startup: {e}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("Shutting down DeepSeek OCR service")


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
