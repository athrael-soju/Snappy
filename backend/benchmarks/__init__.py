"""
BBox-DocVQA Benchmarking Suite for Snappy.

This module implements benchmarks to validate the spatial grounding capabilities
described in arXiv:2512.02660. It evaluates ColPali patch-to-region filtering
against the BBox-DocVQA dataset.

Key Components:
- BBoxDocVQADataset: Loads and iterates over the benchmark dataset
- SpatialGroundingEvaluator: Computes region scores from ColPali similarity maps
- BenchmarkRunner: Orchestrates evaluation across multiple strategies
- Filtering strategies: Various approaches for region selection

Expected Performance (from literature):
- SOTA (Qwen2.5VL-72B): ~35% mean IoU on BBox-DocVQA
- Target for Snappy: 35-50% mean IoU with patch-based approach
"""

from benchmarks.data_loader import BBoxDocVQADataset, BBoxDocVQASample
from benchmarks.evaluator import SpatialGroundingEvaluator, PatchConfig, EvaluationResult
from benchmarks.metrics import (
    BenchmarkResults,
    IoUMetrics,
    aggregate_metrics,
    compute_best_match_iou,
    compute_context_reduction,
    compute_iou,
    compute_recall_at_k,
    evaluate_multi_region,
)
from benchmarks.runner import BenchmarkRunner, BenchmarkConfig, run_ablation_study
from benchmarks.strategies import (
    FilteringStrategy,
    ThresholdFilter,
    TopKFilter,
    AdaptiveFilter,
    KneeFilter,
    PercentileFilter,
    CombinedFilter,
    ScoredRegion,
    STRATEGY_PRESETS,
    get_strategy,
)

__all__ = [
    # Data loading
    "BBoxDocVQADataset",
    "BBoxDocVQASample",
    # Metrics
    "BenchmarkResults",
    "IoUMetrics",
    "aggregate_metrics",
    "compute_best_match_iou",
    "compute_context_reduction",
    "compute_iou",
    "compute_recall_at_k",
    "evaluate_multi_region",
    # Evaluator
    "SpatialGroundingEvaluator",
    "PatchConfig",
    "EvaluationResult",
    # Runner
    "BenchmarkRunner",
    "BenchmarkConfig",
    "run_ablation_study",
    # Strategies
    "FilteringStrategy",
    "ThresholdFilter",
    "TopKFilter",
    "AdaptiveFilter",
    "KneeFilter",
    "PercentileFilter",
    "CombinedFilter",
    "ScoredRegion",
    "STRATEGY_PRESETS",
    "get_strategy",
]
