"""Alternative entrypoint for running the DuckDB service."""

from __future__ import annotations

import uvicorn
from app.core.config import settings
from app.main import create_app

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
