"""
Coordinate normalization and IoU computation utilities.

All coordinate systems are normalized to [0, 1] for uniform comparison:
- Patch grid (32x32): x = (idx % 32)/32, y = (idx // 32)/32
- DeepSeek-OCR (0-999): coord / 999
- Ground truth (pixels): coord / image_dimension
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np
from numpy.typing import NDArray


@dataclass
class Box:
    """Normalized bounding box with coordinates in [0, 1] range."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        """Validate box coordinates."""
        if self.x2 < self.x1:
            raise ValueError(f"x2 ({self.x2}) must be >= x1 ({self.x1})")
        if self.y2 < self.y1:
            raise ValueError(f"y2 ({self.y2}) must be >= y1 ({self.y1})")

    @property
    def width(self) -> float:
        """Box width."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Box height."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Box area."""
        return self.width * self.height

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to tuple (x1, y1, x2, y2)."""
        return (self.x1, self.y1, self.x2, self.y2)

    def to_array(self) -> NDArray[np.float64]:
        """Convert to numpy array [x1, y1, x2, y2]."""
        return np.array([self.x1, self.y1, self.x2, self.y2], dtype=np.float64)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float, float]) -> "Box":
        """Create Box from tuple (x1, y1, x2, y2)."""
        return cls(x1=coords[0], y1=coords[1], x2=coords[2], y2=coords[3])

    @classmethod
    def from_array(cls, arr: NDArray[np.floating]) -> "Box":
        """Create Box from numpy array [x1, y1, x2, y2]."""
        if arr.shape != (4,):
            raise ValueError(f"Expected array of shape (4,), got {arr.shape}")
        return cls(x1=float(arr[0]), y1=float(arr[1]), x2=float(arr[2]), y2=float(arr[3]))


def patch_index_to_normalized_box(
    patch_idx: int,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> Box:
    """
    Convert a linear patch index to a normalized bounding box.

    Args:
        patch_idx: Linear index of the patch (row-major order)
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Normalized Box with coordinates in [0, 1]
    """
    if patch_idx < 0 or patch_idx >= n_patches_x * n_patches_y:
        raise ValueError(
            f"patch_idx {patch_idx} out of range [0, {n_patches_x * n_patches_y})"
        )

    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    # Row-major order: idx = y * n_patches_x + x
    patch_x = patch_idx % n_patches_x
    patch_y = patch_idx // n_patches_x

    x1 = patch_x * patch_width
    y1 = patch_y * patch_height
    x2 = x1 + patch_width
    y2 = y1 + patch_height

    return Box(x1=x1, y1=y1, x2=x2, y2=y2)


def normalize_bbox_deepseek(
    coords: Tuple[int, int, int, int],
    coord_range: int = 999,
) -> Box:
    """
    Normalize DeepSeek-OCR coordinates (0-999) to [0, 1] range.

    Args:
        coords: Tuple (x1, y1, x2, y2) in DeepSeek format (0-999)
        coord_range: Maximum coordinate value (default 999)

    Returns:
        Normalized Box with coordinates in [0, 1]
    """
    x1 = coords[0] / coord_range
    y1 = coords[1] / coord_range
    x2 = coords[2] / coord_range
    y2 = coords[3] / coord_range

    # Clamp to [0, 1] range
    x1 = max(0.0, min(1.0, x1))
    y1 = max(0.0, min(1.0, y1))
    x2 = max(0.0, min(1.0, x2))
    y2 = max(0.0, min(1.0, y2))

    # Ensure proper ordering
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1

    return Box(x1=x1, y1=y1, x2=x2, y2=y2)


def normalize_bbox_pixels(
    coords: Tuple[float, float, float, float],
    image_width: int,
    image_height: int,
) -> Box:
    """
    Normalize pixel coordinates to [0, 1] range.

    Args:
        coords: Tuple (x1, y1, x2, y2) in pixels
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Normalized Box with coordinates in [0, 1]
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError(
            f"Invalid image dimensions: {image_width}x{image_height}"
        )

    x1 = coords[0] / image_width
    y1 = coords[1] / image_height
    x2 = coords[2] / image_width
    y2 = coords[3] / image_height

    # Clamp to [0, 1] range
    x1 = max(0.0, min(1.0, x1))
    y1 = max(0.0, min(1.0, y1))
    x2 = max(0.0, min(1.0, x2))
    y2 = max(0.0, min(1.0, y2))

    # Ensure proper ordering
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1

    return Box(x1=x1, y1=y1, x2=x2, y2=y2)


def compute_iou(box1: Box, box2: Box) -> float:
    """
    Compute Intersection over Union (IoU) between two boxes.

    Args:
        box1: First bounding box
        box2: Second bounding box

    Returns:
        IoU value in [0, 1]
    """
    # Compute intersection
    inter_x1 = max(box1.x1, box2.x1)
    inter_y1 = max(box1.y1, box2.y1)
    inter_x2 = min(box1.x2, box2.x2)
    inter_y2 = min(box1.y2, box2.y2)

    # Check for no intersection
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)

    # Compute union
    union_area = box1.area + box2.area - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def compute_iou_matrix(
    boxes1: List[Box],
    boxes2: List[Box],
) -> NDArray[np.float64]:
    """
    Compute pairwise IoU matrix between two sets of boxes.

    Args:
        boxes1: First list of boxes (predictions)
        boxes2: Second list of boxes (ground truth)

    Returns:
        IoU matrix of shape (len(boxes1), len(boxes2))
    """
    n1 = len(boxes1)
    n2 = len(boxes2)

    if n1 == 0 or n2 == 0:
        return np.zeros((n1, n2), dtype=np.float64)

    # Convert to numpy arrays for vectorized computation
    arr1 = np.array([b.to_array() for b in boxes1])  # (n1, 4)
    arr2 = np.array([b.to_array() for b in boxes2])  # (n2, 4)

    # Compute intersection coordinates
    # Shape: (n1, n2)
    inter_x1 = np.maximum(arr1[:, 0:1], arr2[:, 0].T)
    inter_y1 = np.maximum(arr1[:, 1:2], arr2[:, 1].T)
    inter_x2 = np.minimum(arr1[:, 2:3], arr2[:, 2].T)
    inter_y2 = np.minimum(arr1[:, 3:4], arr2[:, 3].T)

    # Compute intersection area
    inter_w = np.maximum(0, inter_x2 - inter_x1)
    inter_h = np.maximum(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    # Compute areas
    area1 = (arr1[:, 2] - arr1[:, 0]) * (arr1[:, 3] - arr1[:, 1])  # (n1,)
    area2 = (arr2[:, 2] - arr2[:, 0]) * (arr2[:, 3] - arr2[:, 1])  # (n2,)

    # Compute union
    union_area = area1[:, np.newaxis] + area2[np.newaxis, :] - inter_area

    # Avoid division by zero
    iou_matrix = np.where(union_area > 0, inter_area / union_area, 0.0)

    return iou_matrix.astype(np.float64)


def get_overlapping_patches(
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> List[Tuple[int, int, float]]:
    """
    Get all patches that overlap with a region, along with their IoU.

    Args:
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        List of tuples (patch_x, patch_y, iou) for overlapping patches
    """
    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    # Find patch range that could overlap
    start_x = max(0, int(region.x1 / patch_width))
    end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
    start_y = max(0, int(region.y1 / patch_height))
    end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

    overlapping = []
    for py in range(start_y, end_y):
        for px in range(start_x, end_x):
            patch_box = Box(
                x1=px * patch_width,
                y1=py * patch_height,
                x2=(px + 1) * patch_width,
                y2=(py + 1) * patch_height,
            )
            iou = compute_iou(region, patch_box)
            if iou > 0:
                overlapping.append((px, py, iou))

    return overlapping


def patches_to_region_iou_weights(
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> NDArray[np.float64]:
    """
    Compute IoU weights for all patches with respect to a region.

    Args:
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        2D array of shape (n_patches_y, n_patches_x) with IoU weights
    """
    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    weights = np.zeros((n_patches_y, n_patches_x), dtype=np.float64)

    # Find patch range that could overlap
    start_x = max(0, int(region.x1 / patch_width))
    end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
    start_y = max(0, int(region.y1 / patch_height))
    end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

    for py in range(start_y, end_y):
        for px in range(start_x, end_x):
            patch_box = Box(
                x1=px * patch_width,
                y1=py * patch_height,
                x2=(px + 1) * patch_width,
                y2=(py + 1) * patch_height,
            )
            weights[py, px] = compute_iou(region, patch_box)

    return weights
