"""
Streaming ingestion job handler.

Uses streaming pipeline for 6x faster ingestion with progressive results.
"""

import logging
import os
from typing import Dict, List

import config
from api.dependencies import get_duckdb_service, get_qdrant_service, qdrant_init_error
from api.progress import progress_manager
from clients.qdrant.indexing.points import PointFactory
from domain.pipeline.errors import CancellationError
from domain.pipeline.streaming_pipeline import StreamingPipeline

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
