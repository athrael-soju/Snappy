"""
Static file serving router for local storage.

Serves files stored by LocalStorageClient via HTTP.
"""

import logging
from pathlib import Path

from config import LOCAL_STORAGE_BUCKET_NAME, LOCAL_STORAGE_PATH
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

STORAGE_BASE = Path(LOCAL_STORAGE_PATH)

# MIME type mapping
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".json": "application/json",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}


def _get_content_type(suffix: str) -> str:
    """Map file extension to MIME type."""
    return CONTENT_TYPES.get(suffix.lower(), "application/octet-stream")


@router.get("/{bucket}/{path:path}")
async def serve_file(bucket: str, path: str):
    """
    Serve files from local storage.

    Security measures:
    - Validates bucket name matches configured bucket
    - Resolves path and ensures it stays within storage directory
    - Returns appropriate content types
    """
    # Validate bucket name
    if bucket != LOCAL_STORAGE_BUCKET_NAME:
        raise HTTPException(status_code=404, detail="Bucket not found")

    # Construct file path
    file_path = STORAGE_BASE / bucket / path

    # Security: Ensure path doesn't escape storage directory via path traversal
    try:
        resolved_path = file_path.resolve()
        storage_resolved = STORAGE_BASE.resolve()

        if not str(resolved_path).startswith(str(storage_resolved)):
            logger.warning(f"Path traversal attempt detected: {path}")
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Path resolution error: {e}")
        raise HTTPException(status_code=400, detail="Invalid path")

    # Check file exists
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Not a file")

    # Determine content type
    content_type = _get_content_type(resolved_path.suffix)

    return FileResponse(
        resolved_path,
        media_type=content_type,
        headers={
            # Cache for 1 year (immutable content-addressed files)
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )
