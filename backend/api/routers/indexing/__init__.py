from fastapi import APIRouter

from .status import router as status_router
from .upload import router as upload_router

router = APIRouter()
router.include_router(upload_router)
router.include_router(status_router)

__all__ = ["router"]
