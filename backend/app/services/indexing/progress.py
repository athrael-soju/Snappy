"""Progress notification utilities for long-running indexing tasks."""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ProgressNotifier:
    """Lightweight helper for progress callback orchestration."""

    def __init__(self, callback: Optional[Callable[[int, dict | None], None]]):
        self._callback = callback

    def emit(
        self,
        current: int,
        info: Optional[dict],
        *,
        skip_updates: bool = False,
    ) -> None:
        if not self._callback:
            return
        if skip_updates and info and info.get("stage") != "check_cancel":
            return
        try:
            self._callback(current, info)
        except Exception as exc:  # pragma: no cover - defensive guard
            if (
                "cancelled" in str(exc).lower()
                or exc.__class__.__name__ == "CancellationError"
            ):
                raise
            logger.debug("Progress callback raised %s (ignored)", exc)

    def check_cancel(self, current: int) -> None:
        self.emit(current, {"stage": "check_cancel"}, skip_updates=True)

    def stage(
        self,
        *,
        current: int,
        stage: str,
        batch_start: int,
        batch_size: int,
        total: int,
    ) -> None:
        info = {
            "stage": stage,
            "batch_start": batch_start,
            "batch_size": batch_size,
            "total": total,
        }
        self.emit(current, info)
