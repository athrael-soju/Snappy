"""
Shared utilities for local storage path resolution.

Provides secure path resolution with validation for both
the files router and interpretability endpoint.
"""

import logging
from pathlib import Path
from typing import Tuple

import config

logger = logging.getLogger(__name__)


class StoragePathError(Exception):
    """Base exception for storage path errors."""


class InvalidBucketError(StoragePathError):
    """Raised when bucket name doesn't match configured bucket."""


class PathTraversalError(StoragePathError):
    """Raised when path traversal is detected."""


class FileNotFoundInStorageError(StoragePathError):
    """Raised when file doesn't exist in storage."""


def resolve_storage_path(bucket: str, relative_path: str) -> Path:
    """
    Securely resolve a storage path.

    Args:
        bucket: The bucket name (must match LOCAL_STORAGE_BUCKET_NAME)
        relative_path: The path within the bucket

    Returns:
        Resolved Path object to the file

    Raises:
        InvalidBucketError: If bucket doesn't match configured bucket
        PathTraversalError: If path attempts to escape storage directory
        FileNotFoundInStorageError: If file doesn't exist
    """
    storage_base = Path(config.LOCAL_STORAGE_PATH)
    bucket_name = config.LOCAL_STORAGE_BUCKET_NAME

    # Validate bucket name
    if bucket != bucket_name:
        raise InvalidBucketError(f"Invalid bucket: {bucket}")

    # Construct file path rooted in the configured bucket directory
    bucket_base = storage_base / bucket_name
    file_path = bucket_base / relative_path
    resolved_path = file_path.resolve()
    bucket_resolved = bucket_base.resolve()

    # Security: ensure path stays within the bucket directory
    if not resolved_path.is_relative_to(bucket_resolved):
        logger.warning(f"Path traversal attempt detected: {relative_path}")
        raise PathTraversalError("Path traversal detected")

    if not resolved_path.exists():
        raise FileNotFoundInStorageError(f"File not found: {relative_path}")

    return resolved_path


def parse_files_url(image_url: str) -> Tuple[str, str]:
    """
    Parse a /files/ URL into bucket and relative path components.

    Args:
        image_url: URL containing /files/{bucket}/{path}

    Returns:
        Tuple of (bucket, relative_path)

    Raises:
        ValueError: If URL format is invalid
    """
    if "/files/" not in image_url:
        raise ValueError(f"URL does not contain /files/: {image_url}")

    parts = image_url.split("/files/")
    if len(parts) < 2:
        raise ValueError("Invalid /files/ URL format")

    file_path_part = parts[1]  # e.g., "documents/doc-id/page/image.jpg"
    path_components = file_path_part.split("/", 1)

    if len(path_components) < 2:
        raise ValueError("Missing path in /files/ URL")

    bucket = path_components[0]
    relative_path = path_components[1]

    return bucket, relative_path
