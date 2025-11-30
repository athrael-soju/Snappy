import io
import logging
from typing import Any

from api.dependencies import get_colpali_client
from clients.colpali import ColPaliClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["interpretability"])


@router.post("/interpretability")
async def generate_interpretability_maps(
    query: str = Form(..., description="Query text to interpret"),
    file: UploadFile = File(..., description="Document image to analyze"),
    colpali_client: ColPaliClient = Depends(get_colpali_client),
) -> dict[str, Any]:
    """
    Generate interpretability maps showing query-document token correspondence.

    This endpoint is separate from the search pipeline to avoid performance impact.
    It shows which document regions contribute to similarity scores for each query token.

    Args:
        query: The query text to interpret
        file: The document image to analyze
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
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail=f"File must be an image, got {file.content_type}"
            )

        # Read image
        image_bytes = await file.read()
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
