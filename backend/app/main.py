"""Entry points for the refactored backend application."""

from api.app import create_app as _legacy_create_app
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Temporary bridge that forwards to the legacy FastAPI factory.

    This allows incremental migration to the new `app` package without breaking
    the existing application entry point.
    """

    return _legacy_create_app()
