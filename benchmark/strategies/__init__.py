"""
Benchmark strategies for comparing different retrieval approaches.
"""

from .base import BaseStrategy, StrategyResult
from .colpali_only import ColPaliOnlyStrategy
from .ocr_only import OCROnlyStrategy
from .spatial_grounding import SpatialGroundingStrategy

__all__ = [
    "BaseStrategy",
    "StrategyResult",
    "OCROnlyStrategy",
    "ColPaliOnlyStrategy",
    "SpatialGroundingStrategy",
]
