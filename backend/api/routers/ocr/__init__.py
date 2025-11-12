from fastapi import APIRouter

from .operations import router as operations_router
from .progress import router as progress_router

router = APIRouter(prefix="/ocr", tags=["ocr"])
router.include_router(operations_router)
router.include_router(progress_router)

__all__ = ["router"]
