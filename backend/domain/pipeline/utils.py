"""Utility helpers for pipeline processing."""

import time
from typing import Callable

from .console import get_pipeline_console


# Map stage names to console stage keys
_STAGE_KEY_MAP = {
    "Embedding": "embedding",
    "Storage": "storage",
    "OCR": "ocr",
    "Upsert": "upsert",
}


def log_stage_timing(stage_name: str) -> Callable:
    """Decorator to log execution time for pipeline stages with Rich output.

    Args:
        stage_name: Name of the stage (Embedding, Storage, OCR, or Upsert)

    Returns:
        Decorator function

    Example:
        @log_stage_timing("Embedding")
        def process_batch(self, batch: PageBatch):
            ...
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Extract batch from second argument (first is self)
            batch = args[1]
            batch_id = batch.batch_id

            # Get console and mark stage as started
            console = get_pipeline_console()
            stage_key = _STAGE_KEY_MAP[stage_name]
            console.stage_started(batch_id, stage_key)

            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            # Log completion with Rich console
            # Handle both PageBatch (has images) and EmbeddedBatch (has image_ids)
            num_pages = (
                len(batch.images) if hasattr(batch, "images") else len(batch.image_ids)
            )
            console.stage_completed(batch_id, stage_key, elapsed, f"{num_pages} pages")

            return result

        return wrapper

    return decorator
