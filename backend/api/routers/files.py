"""
Static file serving router for local storage.

Serves files stored by LocalStorageClient via HTTP.
"""

import logging

from clients.local_storage_utils import (
    FileNotFoundInStorageError,
    InvalidBucketError,
    PathTraversalError,
    resolve_storage_path,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

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
    try:
        resolved_path = resolve_storage_path(bucket, path)
    except InvalidBucketError:
        raise HTTPException(status_code=404, detail="Bucket not found")
    except PathTraversalError:
        raise HTTPException(status_code=403, detail="Access denied")
    except FileNotFoundInStorageError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        raise HTTPException(status_code=400, detail="Invalid path")

    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Not a file")

    # Determine content type
    content_type = _get_content_type(resolved_path.suffix)

    return FileResponse(
        resolved_path,
        media_type=content_type,
        headers={
            # Cache for 24 hours; files may be re-uploaded with same path
            "Cache-Control": "public, max-age=86400",
        },
    )
