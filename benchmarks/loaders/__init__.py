"""Dataset loaders for benchmarks."""

from .bbox_docvqa import (
    BBoxDocVQALoader,
    BBoxDocVQASample,
    ComplexityType,
    RegionType,
    load_bbox_docvqa,
)

__all__ = [
    "BBoxDocVQALoader",
    "BBoxDocVQASample",
    "ComplexityType",
    "RegionType",
    "load_bbox_docvqa",
]
