"""
Retrieval strategies for benchmarking.

Available strategies:
- OnTheFlyStrategy: On-the-fly OCR + filtering (no storage required)
"""

from benchmarks.strategies.base import BaseRetrievalStrategy, RetrievalResult
from benchmarks.strategies.on_the_fly import OnTheFlyStrategy

__all__ = [
    "BaseRetrievalStrategy",
    "RetrievalResult",
    "OnTheFlyStrategy",
]
