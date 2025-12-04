"""
Evaluation suite for Spatially-Grounded Document Retrieval.

This package provides tools for evaluating the Patch-to-Region Relevance
Propagation method on the BBox-DocVQA dataset.

Components:
- dataset: BBox-DocVQA dataset loader
- metrics: ANLS, IoU, Precision@k, Recall, token counting
- scoring: Standalone region scoring wrapper
- conditions: Context builders for evaluation conditions
- benchmark: Main benchmark runner
- analysis: Results analysis and visualization
"""

__version__ = "0.1.0"

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    """Lazy import for package components."""
    if name == "BBoxDocVQADataset":
        from eval.dataset import BBoxDocVQADataset
        return BBoxDocVQADataset
    elif name == "Sample":
        from eval.dataset import Sample
        return Sample
    elif name == "compute_anls":
        from eval.metrics import compute_anls
        return compute_anls
    elif name == "compute_iou":
        from eval.metrics import compute_iou
        return compute_iou
    elif name == "compute_precision_at_k":
        from eval.metrics import compute_precision_at_k
        return compute_precision_at_k
    elif name == "compute_recall":
        from eval.metrics import compute_recall
        return compute_recall
    elif name == "compute_hit_rate":
        from eval.metrics import compute_hit_rate
        return compute_hit_rate
    elif name == "count_tokens":
        from eval.metrics import count_tokens
        return count_tokens
    elif name == "RegionScorer":
        from eval.scoring import RegionScorer
        return RegionScorer
    elif name == "HybridContextBuilder":
        from eval.conditions import HybridContextBuilder
        return HybridContextBuilder
    elif name == "PageOnlyContextBuilder":
        from eval.conditions import PageOnlyContextBuilder
        return PageOnlyContextBuilder
    elif name == "OCROnlyBM25ContextBuilder":
        from eval.conditions import OCROnlyBM25ContextBuilder
        return OCROnlyBM25ContextBuilder
    elif name == "OCROnlyDenseContextBuilder":
        from eval.conditions import OCROnlyDenseContextBuilder
        return OCROnlyDenseContextBuilder
    elif name == "Benchmark":
        from eval.benchmark import Benchmark
        return Benchmark
    elif name == "BenchmarkConfig":
        from eval.benchmark import BenchmarkConfig
        return BenchmarkConfig
    raise AttributeError(f"module 'eval' has no attribute '{name}'")
