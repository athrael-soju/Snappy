"""Domain-specific exceptions for business logic layer.

These exceptions are framework-agnostic and should be caught by the API layer
to translate into appropriate HTTP responses.
"""


class DomainError(Exception):
    """Base exception for all domain layer errors."""

    pass


class DocumentNotFoundError(DomainError):
    """Raised when a requested document does not exist."""

    pass


class PageNotFoundError(DomainError):
    """Raised when a requested page does not exist."""

    pass


class QueryExecutionError(DomainError):
    """Raised when a database query fails to execute."""

    pass


class SearchError(DomainError):
    """Raised when a search operation fails."""

    pass


class StatisticsError(DomainError):
    """Raised when retrieving statistics fails."""

    pass


class ServiceUnavailableError(DomainError):
    """Raised when a required service is unavailable."""

    pass


class UploadError(DomainError):
    """Raised when file upload fails."""

    pass


class UploadTimeoutError(UploadError):
    """Raised when file upload exceeds timeout."""

    pass


class FileSizeExceededError(UploadError):
    """Raised when file size exceeds maximum allowed."""

    pass


class InvalidFileTypeError(UploadError):
    """Raised when file type is not allowed."""

    pass
