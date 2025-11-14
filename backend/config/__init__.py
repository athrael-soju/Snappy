"""
Configuration package for FastAPI backend.

This module re-exports all configuration variables from application.py
to enable standard import patterns:
    from config import LOG_LEVEL
    import config

All configuration logic is in config/application.py
"""

# Import the application module to enable __getattr__ forwarding
from . import application

# Re-export get_pipeline_max_concurrency explicitly
from .application import get_pipeline_max_concurrency  # noqa: F401


def __getattr__(name):
    """Forward attribute lookups to application module for dynamic config access."""
    return getattr(application, name)


__all__ = ["get_pipeline_max_concurrency"]
