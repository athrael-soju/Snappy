"""
Retrieval strategies for benchmarking.

Available strategies:
- SnappyFullStrategy: ColPali + OCR + Spatially-Grounded Region Relevance
- ColPaliOnlyStrategy: Pure vision-language model retrieval
- OCROnlyStrategy: Traditional text-based retrieval
- OnTheFlyStrategy: On-the-fly OCR + filtering (no storage required)
"""

from benchmarks.strategies.base import BaseRetrievalStrategy, RetrievalResult
from benchmarks.strategies.snappy_full import SnappyFullStrategy
from benchmarks.strategies.colpali_only import ColPaliOnlyStrategy
from benchmarks.strategies.ocr_only import OCROnlyStrategy
from benchmarks.strategies.on_the_fly import OnTheFlyStrategy

__all__ = [
    "BaseRetrievalStrategy",
    "RetrievalResult",
    "SnappyFullStrategy",
    "ColPaliOnlyStrategy",
    "OCROnlyStrategy",
    "OnTheFlyStrategy",
]
