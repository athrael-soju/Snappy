from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import meta, retrieval, indexing, maintenance
from config import ALLOWED_ORIGINS


def create_app() -> FastAPI:
    app = FastAPI(title="Vision RAG API", version="1.0.0")

    # CORS (adjust origins for production)
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

    return app
