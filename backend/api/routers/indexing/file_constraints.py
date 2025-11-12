from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable

import config

logger = logging.getLogger(__name__)

# Default upload chunk size in MB
DEFAULT_UPLOAD_CHUNK_SIZE_MB = 4.0
MIN_UPLOAD_CHUNK_SIZE_MB = 0.5
MAX_UPLOAD_CHUNK_SIZE_MB = 16.0

DEFAULT_ALLOWED_TYPES = ["pdf"]
SUPPORTED_FILE_TYPES = {
    "pdf": {
        "extensions": {".pdf"},
        "mime_types": {"application/pdf"},
        "label": "PDF",
    },
}


@dataclass(frozen=True)
class UploadConstraints:
    allowed_types: list[str]
    allowed_extensions: set[str]
    allowed_mime_types: set[str]
    description: str
    max_files: int
    max_file_size_mb: int

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def _normalise_type(value: str) -> str:
    return value.strip().lower()


def _describe_allowed_types(type_keys: Iterable[str]) -> str:
    labels = []
    for key in type_keys:
        meta = SUPPORTED_FILE_TYPES.get(key)
        labels.append(meta.get("label", key.upper()) if meta else key.upper())
    return ", ".join(labels) if labels else "unknown"


def resolve_upload_constraints() -> UploadConstraints:
    """Resolve allowed file types and limits from runtime configuration."""
    raw_types = getattr(config, "UPLOAD_ALLOWED_FILE_TYPES", DEFAULT_ALLOWED_TYPES)
    allowed_types: list[str] = []

    for entry in raw_types:
        key = _normalise_type(str(entry))
        if not key:
            continue
        if key in SUPPORTED_FILE_TYPES:
            allowed_types.append(key)
        else:
            logger.warning(
                "Ignoring unsupported file type '%s' in UPLOAD_ALLOWED_FILE_TYPES",
                entry,
            )

    if not allowed_types:
        allowed_types = DEFAULT_ALLOWED_TYPES.copy()

    max_files = getattr(config, "UPLOAD_MAX_FILES", 5)
    max_file_size_mb = getattr(config, "UPLOAD_MAX_FILE_SIZE_MB", 10)

    max_files = max(1, min(20, max_files))
    max_file_size_mb = max(1, min(200, max_file_size_mb))

    allowed_extensions: set[str] = set()
    allowed_mime_types: set[str] = set()
    for type_key in allowed_types:
        meta = SUPPORTED_FILE_TYPES.get(type_key) or {}
        allowed_extensions.update(
            {str(ext).lower() for ext in meta.get("extensions", [])}
        )
        allowed_mime_types.update(
            {str(mime).lower() for mime in meta.get("mime_types", [])}
        )

    return UploadConstraints(
        allowed_types=allowed_types,
        allowed_extensions=allowed_extensions,
        allowed_mime_types=allowed_mime_types,
        description=_describe_allowed_types(allowed_types),
        max_files=max_files,
        max_file_size_mb=max_file_size_mb,
    )


def is_allowed_file(
    filename: str | None,
    content_type: str | None,
    constraints: UploadConstraints,
) -> bool:
    extension = os.path.splitext(filename or "")[1].lower()
    mime = (content_type or "").lower()

    if extension and extension in constraints.allowed_extensions:
        return True
    if mime and mime in constraints.allowed_mime_types:
        return True
    return False


def get_upload_chunk_size_bytes() -> int:
    """Get upload chunk size in bytes, reading value in MB from config."""
    raw_value = getattr(config, "UPLOAD_CHUNK_SIZE_BYTES", DEFAULT_UPLOAD_CHUNK_SIZE_MB)
    try:
        chunk_size_mb = float(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid UPLOAD_CHUNK_SIZE_BYTES value '%s'; using default", raw_value
        )
        chunk_size_mb = DEFAULT_UPLOAD_CHUNK_SIZE_MB

    if chunk_size_mb < MIN_UPLOAD_CHUNK_SIZE_MB:
        logger.warning(
            "UPLOAD_CHUNK_SIZE_BYTES %.1f MB below minimum; clamping to %.1f MB",
            chunk_size_mb,
            MIN_UPLOAD_CHUNK_SIZE_MB,
        )
        chunk_size_mb = MIN_UPLOAD_CHUNK_SIZE_MB
    if chunk_size_mb > MAX_UPLOAD_CHUNK_SIZE_MB:
        logger.warning(
            "UPLOAD_CHUNK_SIZE_BYTES %.1f MB above maximum; clamping to %.1f MB",
            chunk_size_mb,
            MAX_UPLOAD_CHUNK_SIZE_MB,
        )
        chunk_size_mb = MAX_UPLOAD_CHUNK_SIZE_MB

    return int(chunk_size_mb * 1024 * 1024)


__all__ = [
    "DEFAULT_ALLOWED_TYPES",
    "DEFAULT_UPLOAD_CHUNK_SIZE_MB",
    "MAX_UPLOAD_CHUNK_SIZE_MB",
    "MIN_UPLOAD_CHUNK_SIZE_MB",
    "SUPPORTED_FILE_TYPES",
    "UploadConstraints",
    "get_upload_chunk_size_bytes",
    "is_allowed_file",
    "resolve_upload_constraints",
]
