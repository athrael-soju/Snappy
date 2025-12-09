"""
Coordinate system utilities for patch-to-region relevance propagation.

This module handles the alignment of three coordinate systems:
1. Patch grid (32×32) → normalized [0,1]
2. DeepSeek-OCR (0-999) → normalized [0,1]
3. Ground truth (absolute pixels) → normalized [0,1]
"""

from typing import List, Optional, Tuple

import numpy as np


# Type alias for bounding boxes: (x1, y1, x2, y2) in normalized [0,1] space
NormalizedBox = Tuple[float, float, float, float]


def normalize_bbox(
    bbox: List[float],
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> NormalizedBox:
    """
    Normalize bounding box to [0, 1] space.

    Handles three input formats:
    - Already normalized: values in [0, 1] - returned as-is
    - DeepSeek-OCR format: values in (1, 999] - always detected by range
    - Pixel coordinates: values > 999, requires image_width and image_height

    Args:
        bbox: Bounding box [x1, y1, x2, y2]
        image_width: Image width for pixel coordinate normalization (only used when coords > 999)
        image_height: Image height for pixel coordinate normalization (only used when coords > 999)

    Returns:
        Normalized (x1, y1, x2, y2) tuple in [0, 1] space

    Raises:
        ValueError: If bbox has fewer than 4 elements or coordinates cannot be normalized
    """
    if len(bbox) < 4:
        raise ValueError(f"Bounding box must have at least 4 elements, got {len(bbox)}")

    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    max_coord = max(x1, y1, x2, y2)

    if max_coord <= 1.0:
        # Already normalized
        return (x1, y1, x2, y2)
    elif max_coord <= 999:
        # DeepSeek-OCR format (0-999) - always use 999 divisor regardless of image dims
        return (x1 / 999.0, y1 / 999.0, x2 / 999.0, y2 / 999.0)
    elif image_width is not None and image_height is not None:
        # Pixel coordinates (> 999) - use provided dimensions
        return (
            x1 / image_width,
            y1 / image_height,
            x2 / image_width,
            y2 / image_height,
        )
    else:
        raise ValueError(
            f"Cannot normalize bbox {bbox}: coordinates exceed 999 (max={max_coord}) "
            f"but image dimensions not provided. Provide image_width/image_height "
            f"for pixel coordinates."
        )


def normalize_patch_to_box(
    patch_idx: int,
    grid_x: int = 32,
    grid_y: int = 32,
) -> NormalizedBox:
    """
    Convert a patch index to normalized bounding box coordinates.

    Args:
        patch_idx: Linear patch index (row-major order)
        grid_x: Number of patches in x dimension (default: 32)
        grid_y: Number of patches in y dimension (default: 32)

    Returns:
        Normalized bounding box (x1, y1, x2, y2) in [0, 1] space
    """
    patch_x = patch_idx % grid_x
    patch_y = patch_idx // grid_x

    x1 = patch_x / grid_x
    y1 = patch_y / grid_y
    x2 = (patch_x + 1) / grid_x
    y2 = (patch_y + 1) / grid_y

    return (x1, y1, x2, y2)


def normalize_ocr_bbox(bbox: Tuple[int, int, int, int]) -> NormalizedBox:
    """
    Normalize DeepSeek-OCR bounding box from 0-999 scale to [0, 1].

    Args:
        bbox: Bounding box (x1, y1, x2, y2) in 0-999 coordinate space

    Returns:
        Normalized bounding box in [0, 1] space
    """
    return (
        bbox[0] / 999.0,
        bbox[1] / 999.0,
        bbox[2] / 999.0,
        bbox[3] / 999.0,
    )


def normalize_gt_bbox(
    bbox: Tuple[float, float, float, float],
    img_width: int,
    img_height: int,
) -> NormalizedBox:
    """
    Normalize ground truth bounding box from absolute pixels to [0, 1].

    Args:
        bbox: Bounding box (x1, y1, x2, y2) in absolute pixel coordinates
        img_width: Image width in pixels
        img_height: Image height in pixels

    Returns:
        Normalized bounding box in [0, 1] space
    """
    x1, y1, x2, y2 = bbox
    return (
        x1 / img_width,
        y1 / img_height,
        x2 / img_width,
        y2 / img_height,
    )


def compute_iou(box1: NormalizedBox, box2: NormalizedBox) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.

    Args:
        box1: First bounding box (x1, y1, x2, y2) in normalized coordinates
        box2: Second bounding box (x1, y1, x2, y2) in normalized coordinates

    Returns:
        IoU score in [0, 1]
    """
    # Compute intersection
    inter_x1 = max(box1[0], box2[0])
    inter_y1 = max(box1[1], box2[1])
    inter_x2 = min(box1[2], box2[2])
    inter_y2 = min(box1[3], box2[3])

    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)
    intersection = inter_width * inter_height

    # Compute areas
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    # Compute union
    union = area1 + area2 - intersection

    # Avoid division by zero
    if union <= 0:
        return 0.0

    return intersection / union


def compute_patch_region_iou(
    patch_x: int,
    patch_y: int,
    region_box: NormalizedBox,
    grid_x: int = 32,
    grid_y: int = 32,
) -> float:
    """
    Compute IoU between a single patch and a region.

    Args:
        patch_x: Patch x coordinate (0 to grid_x-1)
        patch_y: Patch y coordinate (0 to grid_y-1)
        region_box: Region bounding box in normalized coordinates
        grid_x: Number of patches in x dimension
        grid_y: Number of patches in y dimension

    Returns:
        IoU score in [0, 1]
    """
    # Convert patch to normalized box
    patch_box = (
        patch_x / grid_x,
        patch_y / grid_y,
        (patch_x + 1) / grid_x,
        (patch_y + 1) / grid_y,
    )

    return compute_iou(patch_box, region_box)


def get_overlapping_patches(
    region_box: NormalizedBox,
    grid_x: int = 32,
    grid_y: int = 32,
    min_overlap: float = 0.0,
) -> List[Tuple[int, int, float]]:
    """
    Find all patches that overlap with a region and compute their IoU.

    Args:
        region_box: Region bounding box in normalized coordinates (x1, y1, x2, y2)
        grid_x: Number of patches in x dimension
        grid_y: Number of patches in y dimension
        min_overlap: Minimum IoU threshold to include a patch

    Returns:
        List of (patch_x, patch_y, iou) tuples for overlapping patches
    """
    x1, y1, x2, y2 = region_box

    # Determine patch range that could overlap
    # Convert normalized coords to patch indices
    start_patch_x = max(0, int(x1 * grid_x))
    start_patch_y = max(0, int(y1 * grid_y))
    end_patch_x = min(grid_x, int(np.ceil(x2 * grid_x)))
    end_patch_y = min(grid_y, int(np.ceil(y2 * grid_y)))

    overlapping = []
    for py in range(start_patch_y, end_patch_y):
        for px in range(start_patch_x, end_patch_x):
            iou = compute_patch_region_iou(px, py, region_box, grid_x, grid_y)
            if iou > min_overlap:
                overlapping.append((px, py, iou))

    return overlapping


def patches_to_heatmap(
    similarity_maps: List[np.ndarray],
    aggregation: str = "max",
) -> np.ndarray:
    """
    Aggregate per-token similarity maps into a single heatmap.

    Args:
        similarity_maps: List of 2D similarity arrays, one per query token
        aggregation: Aggregation method ('max', 'mean', 'sum')

    Returns:
        Aggregated 2D heatmap array
    """
    if not similarity_maps:
        raise ValueError("No similarity maps provided")

    stacked = np.stack(similarity_maps, axis=0)

    if aggregation == "max":
        return np.max(stacked, axis=0)
    elif aggregation == "mean":
        return np.mean(stacked, axis=0)
    elif aggregation == "sum":
        return np.sum(stacked, axis=0)
    else:
        raise ValueError(f"Unknown aggregation method: {aggregation}")


def pixel_to_patch_coords(
    pixel_bbox: Tuple[float, float, float, float],
    img_width: int,
    img_height: int,
    grid_x: int = 32,
    grid_y: int = 32,
) -> Tuple[int, int, int, int]:
    """
    Convert pixel bounding box to patch grid coordinates.

    Args:
        pixel_bbox: Bounding box (x1, y1, x2, y2) in pixel coordinates
        img_width: Image width in pixels
        img_height: Image height in pixels
        grid_x: Number of patches in x dimension
        grid_y: Number of patches in y dimension

    Returns:
        Patch coordinates (start_x, start_y, end_x, end_y)
    """
    x1, y1, x2, y2 = pixel_bbox

    # Convert to normalized coordinates first
    norm_x1 = x1 / img_width
    norm_y1 = y1 / img_height
    norm_x2 = x2 / img_width
    norm_y2 = y2 / img_height

    # Convert to patch indices
    start_x = max(0, int(norm_x1 * grid_x))
    start_y = max(0, int(norm_y1 * grid_y))
    end_x = min(grid_x, int(np.ceil(norm_x2 * grid_x)))
    end_y = min(grid_y, int(np.ceil(norm_y2 * grid_y)))

    return (start_x, start_y, end_x, end_y)
