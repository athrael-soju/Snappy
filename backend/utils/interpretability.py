"""
Interpretability utilities for ColPali attention-based region filtering.

This module computes similarity maps between query and image embeddings
to identify which document regions are most relevant to a user query.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AttentionRegion:
    """A region of high attention identified by interpretability analysis."""

    patch_x: int
    patch_y: int
    similarity: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) in pixels


@dataclass
class InterpretabilityResult:
    """Result of interpretability computation for a single image."""

    image_id: str
    similarity_map: np.ndarray  # Shape: (n_patches_x, n_patches_y)
    high_attention_regions: List[AttentionRegion]
    patch_size: int
    image_width: int
    image_height: int


def compute_similarity_map(
    query_embedding: np.ndarray,
    image_embedding: np.ndarray,
) -> np.ndarray:
    """
    Compute similarity between query tokens and image patches.

    Uses late interaction (MaxSim) scoring: for each image patch, compute
    maximum similarity across all query tokens.

    Args:
        query_embedding: Query embedding of shape (n_query_tokens, embedding_dim)
        image_embedding: Image embedding of shape (n_patches, embedding_dim)

    Returns:
        Similarity scores of shape (n_patches,) - max similarity per patch
    """
    # Normalize embeddings
    query_norm = query_embedding / (
        np.linalg.norm(query_embedding, axis=1, keepdims=True) + 1e-8
    )
    image_norm = image_embedding / (
        np.linalg.norm(image_embedding, axis=1, keepdims=True) + 1e-8
    )

    # Compute similarity matrix: (n_query_tokens, n_patches)
    similarity_matrix = np.dot(query_norm, image_norm.T)

    # MaxSim: for each patch, take maximum similarity across query tokens
    max_similarities = np.max(similarity_matrix, axis=0)

    return max_similarities


def reshape_to_grid(
    similarities: np.ndarray,
    n_patches_x: int,
    n_patches_y: int,
) -> np.ndarray:
    """
    Reshape flat similarity scores to 2D grid.

    Args:
        similarities: Flat array of shape (n_patches,)
        n_patches_x: Number of patches in x direction
        n_patches_y: Number of patches in y direction

    Returns:
        2D array of shape (n_patches_y, n_patches_x)
    """
    expected_size = n_patches_x * n_patches_y
    if len(similarities) != expected_size:
        logger.warning(
            f"Similarity array size {len(similarities)} doesn't match "
            f"expected grid size {expected_size} ({n_patches_x}x{n_patches_y})"
        )
        # Try to infer square grid
        side = int(np.sqrt(len(similarities)))
        if side * side == len(similarities):
            n_patches_x = n_patches_y = side
        else:
            raise ValueError(
                f"Cannot reshape {len(similarities)} patches to grid"
            )

    return similarities.reshape(n_patches_y, n_patches_x)


def find_high_attention_patches(
    similarity_grid: np.ndarray,
    threshold: Optional[float] = None,
    top_k: Optional[int] = None,
    min_threshold: float = 0.3,
) -> List[Tuple[int, int, float]]:
    """
    Find patches with high attention scores.

    Args:
        similarity_grid: 2D array of shape (n_patches_y, n_patches_x)
        threshold: Absolute threshold for attention (0-1). If None, uses adaptive.
        top_k: If set, return top k patches regardless of threshold.
        min_threshold: Minimum threshold when using adaptive method.

    Returns:
        List of (patch_x, patch_y, similarity) tuples for high-attention patches
    """
    if top_k is not None:
        # Return top k patches
        flat_indices = np.argsort(similarity_grid.ravel())[::-1][:top_k]
        patches = []
        for idx in flat_indices:
            y, x = np.unravel_index(idx, similarity_grid.shape)
            sim = similarity_grid[y, x]
            if sim >= min_threshold:
                patches.append((int(x), int(y), float(sim)))
        return patches

    # Adaptive threshold: mean + 1 std, but at least min_threshold
    if threshold is None:
        mean_sim = np.mean(similarity_grid)
        std_sim = np.std(similarity_grid)
        threshold = max(mean_sim + std_sim, min_threshold)

    # Find patches above threshold
    patches = []
    high_attention_mask = similarity_grid >= threshold
    for y, x in zip(*np.where(high_attention_mask)):
        patches.append((int(x), int(y), float(similarity_grid[y, x])))

    # Sort by similarity descending
    patches.sort(key=lambda p: p[2], reverse=True)

    return patches


def patches_to_pixel_bboxes(
    patches: List[Tuple[int, int, float]],
    patch_size: int,
    image_width: int,
    image_height: int,
) -> List[AttentionRegion]:
    """
    Convert patch coordinates to pixel bounding boxes.

    Args:
        patches: List of (patch_x, patch_y, similarity) tuples
        patch_size: Size of each patch in pixels
        image_width: Original image width
        image_height: Original image height

    Returns:
        List of AttentionRegion objects with pixel bboxes
    """
    regions = []
    for patch_x, patch_y, similarity in patches:
        x1 = patch_x * patch_size
        y1 = patch_y * patch_size
        x2 = min(x1 + patch_size, image_width)
        y2 = min(y1 + patch_size, image_height)

        regions.append(
            AttentionRegion(
                patch_x=patch_x,
                patch_y=patch_y,
                similarity=similarity,
                bbox=(x1, y1, x2, y2),
            )
        )

    return regions


def merge_adjacent_regions(
    regions: List[AttentionRegion],
    merge_distance: int = 1,
) -> List[Tuple[int, int, int, int]]:
    """
    Merge adjacent high-attention regions into larger bounding boxes.

    Args:
        regions: List of AttentionRegion objects
        merge_distance: Maximum patch distance to consider adjacent

    Returns:
        List of merged bounding boxes (x1, y1, x2, y2)
    """
    if not regions:
        return []

    # Simple greedy merging based on overlap/adjacency
    bboxes = [r.bbox for r in regions]

    merged = []
    used = set()

    for i, bbox1 in enumerate(bboxes):
        if i in used:
            continue

        x1, y1, x2, y2 = bbox1
        used.add(i)

        # Try to merge with other bboxes
        changed = True
        while changed:
            changed = False
            for j, bbox2 in enumerate(bboxes):
                if j in used:
                    continue

                bx1, by1, bx2, by2 = bbox2

                # Check if boxes overlap or are adjacent
                if (
                    x1 <= bx2 + merge_distance
                    and x2 >= bx1 - merge_distance
                    and y1 <= by2 + merge_distance
                    and y2 >= by1 - merge_distance
                ):
                    # Merge
                    x1 = min(x1, bx1)
                    y1 = min(y1, by1)
                    x2 = max(x2, bx2)
                    y2 = max(y2, by2)
                    used.add(j)
                    changed = True

        merged.append((x1, y1, x2, y2))

    return merged


def compute_interpretability(
    query_embedding: np.ndarray,
    image_embedding: np.ndarray,
    image_width: int,
    image_height: int,
    patch_size: int = 32,
    n_patches_x: Optional[int] = None,
    n_patches_y: Optional[int] = None,
    attention_threshold: Optional[float] = None,
    top_k_patches: Optional[int] = None,
    merge_adjacent: bool = True,
) -> Dict[str, Any]:
    """
    Compute interpretability analysis for a query-image pair.

    Args:
        query_embedding: Query embedding of shape (n_query_tokens, embedding_dim)
        image_embedding: Image embedding of shape (n_patches, embedding_dim)
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        patch_size: Size of each patch in pixels (default 32 for ColPali)
        n_patches_x: Number of patches in x direction (auto-computed if None)
        n_patches_y: Number of patches in y direction (auto-computed if None)
        attention_threshold: Threshold for high attention (0-1)
        top_k_patches: If set, use top k patches instead of threshold
        merge_adjacent: Whether to merge adjacent high-attention regions

    Returns:
        Dict containing:
        - similarity_map: 2D numpy array of similarities
        - high_attention_bboxes: List of (x1, y1, x2, y2) pixel bboxes
        - patch_regions: List of AttentionRegion objects
        - stats: Dict with min/max/mean similarity
    """
    # Convert to numpy if needed
    if not isinstance(query_embedding, np.ndarray):
        query_embedding = np.array(query_embedding)
    if not isinstance(image_embedding, np.ndarray):
        image_embedding = np.array(image_embedding)

    # Auto-compute grid dimensions if not provided
    n_patches = len(image_embedding)
    if n_patches_x is None or n_patches_y is None:
        # Assume square grid
        side = int(np.sqrt(n_patches))
        if side * side == n_patches:
            n_patches_x = n_patches_y = side
        else:
            # Try to infer from image dimensions
            n_patches_x = image_width // patch_size
            n_patches_y = image_height // patch_size

    # Compute similarity map
    similarities = compute_similarity_map(query_embedding, image_embedding)

    # Reshape to grid
    try:
        similarity_grid = reshape_to_grid(similarities, n_patches_x, n_patches_y)
    except ValueError as e:
        logger.error(f"Failed to reshape similarity map: {e}")
        return {
            "similarity_map": similarities,
            "high_attention_bboxes": [],
            "patch_regions": [],
            "stats": {
                "min": float(np.min(similarities)),
                "max": float(np.max(similarities)),
                "mean": float(np.mean(similarities)),
            },
        }

    # Find high-attention patches
    high_patches = find_high_attention_patches(
        similarity_grid,
        threshold=attention_threshold,
        top_k=top_k_patches,
    )

    # Convert to pixel bboxes
    patch_regions = patches_to_pixel_bboxes(
        high_patches, patch_size, image_width, image_height
    )

    # Merge adjacent regions if requested
    if merge_adjacent and patch_regions:
        merged_bboxes = merge_adjacent_regions(patch_regions, merge_distance=patch_size)
    else:
        merged_bboxes = [r.bbox for r in patch_regions]

    return {
        "similarity_map": similarity_grid,
        "high_attention_bboxes": merged_bboxes,
        "patch_regions": patch_regions,
        "stats": {
            "min": float(np.min(similarity_grid)),
            "max": float(np.max(similarity_grid)),
            "mean": float(np.mean(similarity_grid)),
            "threshold_used": attention_threshold
            or max(np.mean(similarity_grid) + np.std(similarity_grid), 0.3),
        },
    }


def filter_regions_by_attention(
    ocr_regions: List[Dict[str, Any]],
    attention_bboxes: List[Tuple[int, int, int, int]],
    min_overlap_ratio: float = 0.1,
) -> List[Dict[str, Any]]:
    """
    Filter OCR regions to only those intersecting with attention areas.

    Args:
        ocr_regions: List of OCR region dicts with 'bbox' key [x1, y1, x2, y2]
        attention_bboxes: List of attention bounding boxes (x1, y1, x2, y2)
        min_overlap_ratio: Minimum overlap ratio to consider a match (0-1)

    Returns:
        Filtered list of OCR regions that intersect with attention areas
    """
    if not attention_bboxes:
        logger.warning("No attention bboxes provided, returning all regions")
        return ocr_regions

    filtered = []

    for region in ocr_regions:
        region_bbox = region.get("bbox")
        if not region_bbox or len(region_bbox) < 4:
            continue

        rx1, ry1, rx2, ry2 = region_bbox[:4]

        # Skip invalid bboxes
        if None in (rx1, ry1, rx2, ry2):
            continue

        region_area = max((rx2 - rx1) * (ry2 - ry1), 1)

        # Check intersection with any attention bbox
        for ax1, ay1, ax2, ay2 in attention_bboxes:
            # Compute intersection
            ix1 = max(rx1, ax1)
            iy1 = max(ry1, ay1)
            ix2 = min(rx2, ax2)
            iy2 = min(ry2, ay2)

            if ix1 < ix2 and iy1 < iy2:
                intersection_area = (ix2 - ix1) * (iy2 - iy1)
                overlap_ratio = intersection_area / region_area

                if overlap_ratio >= min_overlap_ratio:
                    filtered.append(region)
                    break  # Already matched, no need to check other attention boxes

    logger.info(
        f"Filtered {len(ocr_regions)} regions to {len(filtered)} "
        f"based on attention overlap (threshold={min_overlap_ratio})"
    )

    return filtered
