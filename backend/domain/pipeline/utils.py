"""Utility helpers for pipeline processing."""

import logging
import time
from itertools import islice
from typing import Callable, Iterator, List, Tuple

logger = logging.getLogger(__name__)


def log_stage_timing(stage_name: str) -> Callable:
    """Decorator to log execution time for pipeline stages.

    Args:
        stage_name: Name of the stage for logging

    Returns:
        Decorator function

    Example:
        @log_stage_timing("Embedding")
        def process_batch(self, batch):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"[{stage_name}] Completed in {elapsed:.2f}s")
            return result
        return wrapper
    return decorator


def iter_image_batches(
    images_iter: Iterator,
    batch_size: int,
) -> Iterator[Tuple[int, List]]:
    """Iterate over images in batches.

    Args:
        images_iter: Iterator of images
        batch_size: Size of each batch

    Yields:
        Tuple of (batch_start_index, batch_items)
    """
    batch_start = 0
    while True:
        batch = list(islice(images_iter, batch_size))
        if not batch:
            break
        yield batch_start, batch
        batch_start += len(batch)
