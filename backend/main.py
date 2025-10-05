import logging
import os

import uvicorn

from api.app import create_app
from config import LOG_LEVEL


def _configure_logging() -> None:
    """Configure root logging once based on configured log level."""
    level = getattr(logging, str(LOG_LEVEL).upper(), logging.INFO)
    logging.basicConfig(level=level)
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)


_configure_logging()
app = create_app()


def run() -> None:
    """Run the FastAPI application with uvicorn."""
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError as exc:
        raise ValueError("Invalid PORT") from exc

    log_level = os.getenv("LOG_LEVEL", str(LOG_LEVEL)).lower()
    uvicorn.run("main:app", host=host, port=port, log_level=log_level, reload=True)


if __name__ == "__main__":
    run()
