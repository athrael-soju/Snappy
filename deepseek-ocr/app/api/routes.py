"""
API routes for DeepSeek OCR service.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import (
    HealthResponse,
    InfoResponse,
    OCRResponse,
    ProcessingMode,
    TaskType,
)
from app.services.ocr_processor import ocr_processor
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": settings.MODEL_NAME,
        "device": settings.DEVICE,
        "torch_dtype": str(settings.TORCH_DTYPE),
    }


@router.post("/restart")
async def restart_service():
    """
    Restart the service by exiting the process.
    The container will automatically restart if configured with restart policy.
    This is useful for stopping any ongoing processing and resetting service state.
    """
    import threading
    import os

    logger.info("Restart requested - initiating service shutdown")

    def force_exit():
        """Force exit in a separate thread to bypass event loop blocking"""
        import time

        time.sleep(0.1)  # Small delay to allow response to be sent
        logger.info("Exiting process for restart")
        os._exit(1)  # Hard exit with code 1 - terminates immediately

    # Use a daemon thread to force exit regardless of event loop state
    exit_thread = threading.Thread(target=force_exit, daemon=True)
    exit_thread.start()

    return JSONResponse(
        content={"status": "restarting", "message": "Service will restart momentarily"}
    )


@router.get("/info", response_model=InfoResponse)
async def get_info():
    """Get model information and available options."""
    return {
        "model": settings.MODEL_NAME,
        "device": settings.DEVICE,
        "modes": list(settings.MODEL_CONFIGS.keys()),
        "tasks": [task.value for task in TaskType],
        "model_configs": settings.MODEL_CONFIGS,
    }


@router.post("/api/ocr", response_model=OCRResponse)
async def ocr_endpoint(
    image: UploadFile = File(..., description="Image or PDF file to process"),
    mode: ProcessingMode = Form(default=ProcessingMode.GUNDAM),
    task: TaskType = Form(default=TaskType.MARKDOWN),
    custom_prompt: Optional[str] = Form(default=None),
    include_grounding: bool = Form(default=True),
    include_images: bool = Form(default=True),
):
    """
    Perform OCR on uploaded image or PDF.

    - **image**: Image file (PNG, JPEG) or PDF document
    - **mode**: Processing mode (affects quality/speed)
    - **task**: Type of OCR task (markdown, plain_ocr, locate, describe, custom)
    - **custom_prompt**: Custom prompt (required for 'custom' and 'locate' tasks)
    - **include_grounding**: Include bounding box information
    - **include_images**: Extract and embed images from document
    """
    # Validate file type
    if not image.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    filename = image.filename.lower()
    is_pdf = filename.endswith(".pdf")
    is_image = any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"])

    if not (is_pdf or is_image):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload an image (PNG, JPEG) or PDF.",
        )

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Run OCR processing in thread pool to avoid blocking the async event loop
        # This allows /health and /restart endpoints to respond during OCR processing
        # Note: GPU inference is internally serialized, but multiple workers allow
        # overlapping file I/O, image preprocessing, and HTTP handling with GPU work
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # Use a shared thread pool executor for OCR operations
        if not hasattr(ocr_endpoint, "_executor"):
            ocr_endpoint._executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="ocr"
            )

        if is_pdf:
            result = await asyncio.get_event_loop().run_in_executor(
                ocr_endpoint._executor,
                ocr_processor.process_pdf,
                tmp_path,
                mode.value,
                task.value,
                custom_prompt or "",
                include_grounding,
                include_images,
            )
        else:
            img = Image.open(tmp_path)
            result = await asyncio.get_event_loop().run_in_executor(
                ocr_endpoint._executor,
                ocr_processor.process_image,
                img,
                mode.value,
                task.value,
                custom_prompt or "",
                include_grounding,
                include_images,
            )

        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
