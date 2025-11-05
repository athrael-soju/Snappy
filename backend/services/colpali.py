"""Backward compatibility shims for the legacy services package."""

from app.integrations.colpali_client import ColPaliClient

ColPaliService = ColPaliClient

__all__ = ["ColPaliService", "ColPaliClient"]
