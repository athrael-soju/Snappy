from fastapi import APIRouter

from .actions import router as actions_router
from .status import router as status_router

router = APIRouter()
router.include_router(actions_router)
router.include_router(status_router)

__all__ = ["router"]
