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
            # Extract batch info if available
            batch = None
            if args and hasattr(args[0], '__class__'):
                # First arg is self, check second arg for batch
                if len(args) > 1 and hasattr(args[1], 'batch_id'):
                    batch = args[1]
            
            # Log start with batch info
            if batch:
                # Handle both PageBatch (has images) and EmbeddedBatch (has image_ids)
                num_pages = len(batch.images) if hasattr(batch, 'images') else len(batch.image_ids)
                batch_info = f"batch {batch.batch_id} ({num_pages} pages)"
                logger.info(f"┌─ [{stage_name}] Processing {batch_info}")
            
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Log completion with timing
            if batch:
                num_pages = len(batch.images) if hasattr(batch, 'images') else len(batch.image_ids)
                batch_info = f"batch {batch.batch_id} ({num_pages} pages)"
                logger.info(f"└─ [{stage_name}] Completed {batch_info} in {elapsed:.2f}s")
            else:
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
