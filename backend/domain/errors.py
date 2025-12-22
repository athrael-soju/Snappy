"""Domain-specific exceptions for business logic layer.

These exceptions are framework-agnostic and should be caught by the API layer
to translate into appropriate HTTP responses.
"""


class DomainError(Exception):
    """Base exception for all domain layer errors."""


class DocumentNotFoundError(DomainError):
    """Raised when a requested document does not exist."""


class PageNotFoundError(DomainError):
    """Raised when a requested page does not exist."""


class QueryExecutionError(DomainError):
    """Raised when a database query fails to execute."""


class SearchError(DomainError):
    """Raised when a search operation fails."""


class StatisticsError(DomainError):
    """Raised when retrieving statistics fails."""


class ServiceUnavailableError(DomainError):
    """Raised when a required service is unavailable."""


class UploadError(DomainError):
    """Raised when file upload fails."""


class UploadTimeoutError(UploadError):
    """Raised when file upload exceeds timeout."""


class FileSizeExceededError(UploadError):
    """Raised when file size exceeds maximum allowed."""


class InvalidFileTypeError(UploadError):
    """Raised when file type is not allowed."""
