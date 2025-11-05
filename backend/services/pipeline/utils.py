"""Utility helpers for pipeline processing."""

from itertools import islice
from typing import Iterator, List, Tuple


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
