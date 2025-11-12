import os
from pathlib import Path

import uvicorn
from api.app import create_app
from logging_config import setup_logging

try:  # pragma: no cover - tooling support
    from config import LOG_LEVEL, UVICORN_RELOAD  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from backend.config import LOG_LEVEL, UVICORN_RELOAD  # type: ignore


def _configure_logging() -> None:
    """Configure root logging once based on configured log level."""
    log_level = str(LOG_LEVEL).upper()
    enable_json = os.getenv("LOG_JSON", "false").lower() == "true"
    log_file_path = os.getenv("LOG_FILE")

    setup_logging(
        log_level=log_level,
        enable_json=enable_json,
        log_file=Path(log_file_path) if log_file_path else None,
    )


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
    reload_override = os.getenv("UVICORN_RELOAD")
    if reload_override is not None:
        reload_enabled = reload_override.strip().lower() in {"1", "true", "yes"}
    else:
        reload_enabled = bool(UVICORN_RELOAD)
    uvicorn.run(
        "main:app", host=host, port=port, log_level=log_level, reload=reload_enabled
    )


if __name__ == "__main__":
    run()
