"""Utility modules for benchmark operations."""

from .coordinates import (
    Box,
    compute_iou,
    compute_iou_matrix,
    normalize_bbox_deepseek,
    normalize_bbox_pixels,
    patch_index_to_normalized_box,
)

__all__ = [
    "Box",
    "compute_iou",
    "compute_iou_matrix",
    "normalize_bbox_deepseek",
    "normalize_bbox_pixels",
    "patch_index_to_normalized_box",
]
