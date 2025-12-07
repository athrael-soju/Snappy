"""
Benchmarking suite for patch-to-region relevance propagation.

This module implements the evaluation framework from:
"Spatially-Grounded Document Retrieval via Patch-to-Region Relevance Propagation"
(https://arxiv.org/abs/2512.02660)

Components:
- loaders: Dataset loaders (BBox_DocVQA_Bench)
- utils: Coordinate utilities and helpers
- aggregation: Patch-to-region aggregation methods
- selection: Region selection strategies
- evaluation: Metrics and ground truth matching
- baselines: Baseline comparison methods
- visualization: Debug overlay generation
"""

from .aggregation import PatchToRegionAggregator
from .selection import RegionSelector
from .evaluation import BBoxEvaluator
from .baselines import BaselineGenerator

__all__ = [
    "PatchToRegionAggregator",
    "RegionSelector",
    "BBoxEvaluator",
    "BaselineGenerator",
]
