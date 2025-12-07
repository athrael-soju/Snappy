"""Utility functions for benchmarking."""

from .coordinates import (
    normalize_patch_to_box,
    normalize_ocr_bbox,
    normalize_gt_bbox,
    compute_iou,
    compute_patch_region_iou,
    get_overlapping_patches,
)

__all__ = [
    "normalize_patch_to_box",
    "normalize_ocr_bbox",
    "normalize_gt_bbox",
    "compute_iou",
    "compute_patch_region_iou",
    "get_overlapping_patches",
]
