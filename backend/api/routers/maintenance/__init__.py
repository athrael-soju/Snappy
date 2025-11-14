from fastapi import APIRouter

from .actions import router as actions_router
from .cleanup import router as cleanup_router
from .status import router as status_router

router = APIRouter()
router.include_router(actions_router)
router.include_router(status_router)
router.include_router(cleanup_router)

__all__ = ["router"]
