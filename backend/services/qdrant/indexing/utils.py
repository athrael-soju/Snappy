"""Utility helpers for Qdrant indexing."""

from itertools import islice
from typing import Iterator, List, Tuple


def iter_image_batches(
    images_iter: Iterator,
    batch_size: int,
) -> Iterator[Tuple[int, List]]:
    batch_start = 0
    while True:
        batch = list(islice(images_iter, batch_size))
        if not batch:
            break
        yield batch_start, batch
        batch_start += len(batch)
