"""API route handlers for ColPali service."""

import asyncio
import inspect
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from PIL import Image

from app.core.config import settings
from fastapi.responses import Response

from app.models.schemas import (
    HeatmapRequest,
    ImageEmbeddingBatchResponse,
    PatchBatchResponse,
    PatchRequest,
    PatchResult,
    QueryEmbeddingResponse,
    QueryRequest,
)
from app.services.embedding_processor import embedding_processor
from app.services.model_service import model_service
from app.utils.image_processing import load_image_from_bytes

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Thread pool executors for CPU-bound operations
_query_executor: Optional[ThreadPoolExecutor] = None
_image_executor: Optional[ThreadPoolExecutor] = None


def get_query_executor() -> ThreadPoolExecutor:
    """Get or create the query executor."""
    global _query_executor
    if _query_executor is None:
        _query_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="query")
    return _query_executor


def get_image_executor() -> ThreadPoolExecutor:
    """Get or create the image executor."""
    global _image_executor
    if _image_executor is None:
        _image_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embed")
    return _image_executor


# Heatmap executor (shares with image executor to avoid GPU memory conflicts)
def get_heatmap_executor() -> ThreadPoolExecutor:
    """Get or create the heatmap executor (shares with image executor)."""
    return get_image_executor()


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ColModernVBert Embedding API", "version": settings.API_VERSION}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "device": str(model_service.model.device)}


@router.post("/restart")
async def restart_service():
    """Restart the service by exiting the process.

    The container will automatically restart if configured with restart policy.
    This is useful for stopping any ongoing processing and resetting service state.
    """
    logger.info("Restart requested - initiating service shutdown")

    def force_exit():
        """Force exit in a separate thread to bypass event loop blocking."""
        import time

        time.sleep(0.1)  # Small delay to allow response to be sent
        logger.info("Exiting process for restart")
        os._exit(1)  # Hard exit with code 1 - terminates immediately

    # Use a daemon thread to force exit regardless of event loop state
    exit_thread = threading.Thread(target=force_exit, daemon=True)
    exit_thread.start()

    return {"status": "restarting", "message": "Service will restart momentarily"}


@router.get("/info")
async def info():
    """Get model information."""
    return model_service.get_model_info()


@router.post(
    "/patches",
    response_model=PatchBatchResponse,
    response_model_exclude_none=True,
)
async def get_n_patches(
    request: PatchRequest = Body(
        ..., example={"dimensions": [{"width": 1024, "height": 768}]}
    )
):
    """Calculate number of patches for given image dimensions and spatial merge size.

    Args:
        request: PatchRequest containing a list of dimensions with 'width' and 'height' keys
    """
    try:
        # get_n_patches is now mandatory for the model
        get_n_patches_fn = model_service.processor.get_n_patches
        call_kwargs: dict[str, Any] = {}

        # Inspect signature to gather required parameters
        try:
            signature = inspect.signature(get_n_patches_fn)

            for name, param in signature.parameters.items():
                # Skip image_size (provided directly) and variadic parameters (*args, **kwargs)
                if name == "image_size" or param.kind in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    continue

                value: Any = None
                if name in {"patch_size", "spatial_merge_size"}:
                    value = getattr(model_service.model, "spatial_merge_size", None)
                elif hasattr(model_service.processor, name):
                    value = getattr(model_service.processor, name)
                elif hasattr(model_service.model, name):
                    value = getattr(model_service.model, name)

                if value is None:
                    if param.default is inspect._empty:
                        raise ValueError(
                            f"Required parameter '{name}' is not available on the model"
                        )
                    continue

                call_kwargs[name] = value
        except (TypeError, ValueError) as e:
            # If signature inspection fails, proceed without extra kwargs
            logger.warning(f"Could not inspect get_n_patches signature: {e}")
            call_kwargs = {}

        # Calculate patches for all dimensions
        results = []
        for dim in request.dimensions:
            try:
                image_size = (dim.width, dim.height)
                n_patches_x, n_patches_y = get_n_patches_fn(
                    image_size, **call_kwargs
                )

                results.append(
                    PatchResult(
                        width=dim.width,
                        height=dim.height,
                        n_patches_x=int(n_patches_x),
                        n_patches_y=int(n_patches_y),
                    )
                )
            except Exception as e:
                results.append(
                    PatchResult(
                        width=dim.width,
                        height=dim.height,
                        error=str(e),
                    )
                )
        return {"results": results}
    except AttributeError:
        raise HTTPException(
            status_code=501,
            detail="The current model does not support get_n_patches functionality"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing patch request: {str(e)}"
        )


@router.post("/embed/queries", response_model=QueryEmbeddingResponse)
async def embed_queries(request: QueryRequest):
    """Generate embeddings for text queries."""
    try:
        queries = (
            [request.queries] if isinstance(request.queries, str) else request.queries
        )
        if not queries:
            raise HTTPException(status_code=400, detail="No queries provided")

        # Run embedding generation in thread pool to avoid blocking event loop
        embeddings_tensors = await asyncio.get_event_loop().run_in_executor(
            get_query_executor(),
            embedding_processor.generate_query_embeddings,
            queries,
        )
        embeddings_list = [embedding.tolist() for embedding in embeddings_tensors]
        return QueryEmbeddingResponse(embeddings=embeddings_list)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating query embeddings: {str(e)}"
        )


@router.post("/embed/images", response_model=ImageEmbeddingBatchResponse)
async def embed_images(files: List[UploadFile] = File(...)):
    """Generate embeddings for uploaded images + image-token boundaries."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No images provided")

        images: List[Image.Image] = []
        for file in files:
            content_type = file.content_type or ""
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not an image"
                )
            image_bytes = await file.read()
            images.append(load_image_from_bytes(image_bytes))

        # Run embedding generation in thread pool to avoid blocking event loop
        # This allows /restart endpoint to be processed immediately during cancellation
        items = await asyncio.get_event_loop().run_in_executor(
            get_image_executor(),
            embedding_processor.generate_image_embeddings_with_boundaries,
            images,
        )
        return ImageEmbeddingBatchResponse(embeddings=items)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating image embeddings: {str(e)}"
        )


@router.post("/heatmap", response_class=Response)
async def generate_heatmap(
    file: UploadFile = File(..., description="Document page image"),
    query: str = Body(..., embed=True, description="Search query text"),
    alpha: float = Body(0.5, embed=True, ge=0.0, le=1.0, description="Heatmap transparency"),
):
    """Generate attention heatmap for a query-image pair.

    Computes late interaction attention between query tokens and image patches,
    returns a PNG image with heatmap overlaid on the original document.

    The heatmap shows which regions of the document are most relevant to the query:
    - Red/warm colors: High attention (most relevant regions)
    - Blue/cool colors: Low attention (less relevant regions)

    Args:
        file: Document page image (PNG, JPEG, etc.)
        query: The search query to visualize attention for
        alpha: Heatmap overlay transparency (0=invisible, 1=opaque)

    Returns:
        PNG image with heatmap overlay
    """
    try:
        # Validate image file
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail=f"File {file.filename} is not an image"
            )

        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Load image
        image_bytes = await file.read()
        image = load_image_from_bytes(image_bytes)

        # Generate heatmap in thread pool
        heatmap_bytes = await asyncio.get_event_loop().run_in_executor(
            get_heatmap_executor(),
            embedding_processor.generate_heatmap,
            query.strip(),
            image,
            alpha,
        )

        return Response(
            content=heatmap_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=heatmap.png",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating heatmap")
        raise HTTPException(
            status_code=500, detail=f"Error generating heatmap: {str(e)}"
        )
