import io
import logging
from pathlib import Path
from typing import Any, Optional

import config
from api.dependencies import get_colpali_client
from clients.colpali import ColPaliClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["interpretability"])

# Maximum file size in bytes (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def _load_image_from_url(image_url: str) -> bytes:
    """
    Load image bytes from a URL, supporting local file:// URLs and /files/ paths.
    """
    # Handle /files/ URLs by reading directly from local storage
    if "/files/" in image_url:
        # Extract path after /files/{bucket}/
        try:
            # URL format: http://host:port/files/{bucket}/{path}
            parts = image_url.split("/files/")
            if len(parts) < 2:
                raise ValueError("Invalid /files/ URL format")

            file_path_part = parts[1]  # e.g., "documents/doc-id/page/image.jpg"
            path_components = file_path_part.split("/", 1)

            if len(path_components) < 2:
                raise ValueError("Missing path in /files/ URL")

            bucket = path_components[0]
            relative_path = path_components[1]

            # Validate bucket matches configured bucket
            if bucket != config.LOCAL_STORAGE_BUCKET_NAME:
                raise ValueError(f"Invalid bucket: {bucket}")

            # Construct full file path
            storage_base = Path(config.LOCAL_STORAGE_PATH)
            file_path = storage_base / bucket / relative_path
            resolved_path = file_path.resolve()

            # Security: ensure path stays within storage directory
            if not str(resolved_path).startswith(str(storage_base.resolve())):
                raise ValueError("Path traversal detected")

            if not resolved_path.exists():
                raise FileNotFoundError(f"File not found: {resolved_path}")

            return resolved_path.read_bytes()

        except Exception as e:
            logger.error(f"Failed to load image from /files/ URL: {e}")
            raise

    raise ValueError(f"Unsupported URL format: {image_url}")


@router.post("/interpretability")
async def generate_interpretability_maps(
    query: str = Form(..., description="Query text to interpret"),
    file: Optional[UploadFile] = File(None, description="Document image to analyze"),
    image_url: Optional[str] = Form(None, description="URL of the image to analyze"),
    colpali_client: ColPaliClient = Depends(get_colpali_client),
) -> dict[str, Any]:
    """
    Generate interpretability maps showing query-document token correspondence.

    This endpoint is separate from the search pipeline to avoid performance impact.
    It shows which document regions contribute to similarity scores for each query token.

    Accepts either:
    - file: An uploaded image file
    - image_url: A URL to the image (supports /files/ URLs for local storage)

    Args:
        query: The query text to interpret
        file: The document image to analyze (optional if image_url provided)
        image_url: URL of the image to analyze (optional if file provided)
        colpali_client: Injected ColPali client dependency

    Returns:
        Dictionary containing:
        - query: Original query text
        - tokens: List of query tokens (filtered)
        - similarity_maps: Per-token similarity maps
        - n_patches_x: Number of patches in x dimension
        - n_patches_y: Number of patches in y dimension
        - image_width: Original image width
        - image_height: Original image height
    """
    try:
        # Determine image source
        if file is not None and file.filename:
            # Validate file type
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail=f"File must be an image, got {file.content_type}"
                )

            # Read image with size limit
            image_bytes = await file.read()
        elif image_url:
            # Load image from URL
            try:
                image_bytes = _load_image_from_url(image_url)
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'image_url' must be provided"
            )

        # Validate file size
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({len(image_bytes)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes / {MAX_FILE_SIZE // (1024 * 1024)} MB)"
            )
        image = Image.open(io.BytesIO(image_bytes))

        logger.info(
            f"Generating interpretability maps for query: '{query}' "
            f"on image: {image.size[0]}x{image.size[1]}"
        )

        # Call ColPali service
        result = colpali_client.generate_interpretability_maps(query, image)

        logger.info(
            f"Successfully generated {len(result.get('similarity_maps', []))} "
            f"token similarity maps"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate interpretability maps: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate interpretability maps: {str(e)}"
        )
