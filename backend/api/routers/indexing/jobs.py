"""
Streaming ingestion job handler.

Uses streaming pipeline for 6x faster ingestion with progressive results.
"""

import logging

from domain.pipeline.errors import CancellationError

logger = logging.getLogger(__name__)


from domain.indexing import cleanup_temp_files, run_indexing_job

__all__ = [
    "CancellationError",
    "cleanup_temp_files",
    "run_indexing_job",
]


__all__ = [
    "CancellationError",
    "cleanup_temp_files",
    "run_indexing_job",
]
