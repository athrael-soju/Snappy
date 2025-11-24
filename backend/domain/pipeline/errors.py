"""Shared exceptions for pipeline components."""


class CancellationError(Exception):
    """Raised when a job is cancelled mid-flight."""
