"""
Patch-to-Region Score Aggregation Methods.

This module provides methods to aggregate patch-level similarity scores
to region-level scores for OCR-extracted regions.

Aggregation methods:
- max: Highest overlapping patch score
- mean: Average of overlapping patch scores
- sum: Sum of overlapping patch scores
- iou_weighted: IoU-weighted sum (canonical method)
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from .utils.coordinates import Box, patches_to_region_iou_weights


class AggregationMethod(str, Enum):
    """Available aggregation methods."""

    MAX = "max"
    MEAN = "mean"
    SUM = "sum"
    IOU_WEIGHTED = "iou_weighted"


def aggregate_patch_scores_max(
    patch_scores: NDArray[np.floating],
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores using maximum value in overlapping region.

    Args:
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Maximum patch score in the overlapping region
    """
    if patch_scores.shape != (n_patches_y, n_patches_x):
        raise ValueError(
            f"patch_scores shape {patch_scores.shape} does not match "
            f"expected ({n_patches_y}, {n_patches_x})"
        )

    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    # Find patch range that overlaps with region
    start_x = max(0, int(region.x1 / patch_width))
    end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
    start_y = max(0, int(region.y1 / patch_height))
    end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

    if start_x >= end_x or start_y >= end_y:
        return 0.0

    region_patches = patch_scores[start_y:end_y, start_x:end_x]
    return float(np.max(region_patches))


def aggregate_patch_scores_mean(
    patch_scores: NDArray[np.floating],
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores using mean value in overlapping region.

    Args:
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Mean patch score in the overlapping region
    """
    if patch_scores.shape != (n_patches_y, n_patches_x):
        raise ValueError(
            f"patch_scores shape {patch_scores.shape} does not match "
            f"expected ({n_patches_y}, {n_patches_x})"
        )

    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    # Find patch range that overlaps with region
    start_x = max(0, int(region.x1 / patch_width))
    end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
    start_y = max(0, int(region.y1 / patch_height))
    end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

    if start_x >= end_x or start_y >= end_y:
        return 0.0

    region_patches = patch_scores[start_y:end_y, start_x:end_x]
    return float(np.mean(region_patches))


def aggregate_patch_scores_sum(
    patch_scores: NDArray[np.floating],
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores using sum in overlapping region.

    Args:
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Sum of patch scores in the overlapping region
    """
    if patch_scores.shape != (n_patches_y, n_patches_x):
        raise ValueError(
            f"patch_scores shape {patch_scores.shape} does not match "
            f"expected ({n_patches_y}, {n_patches_x})"
        )

    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    # Find patch range that overlaps with region
    start_x = max(0, int(region.x1 / patch_width))
    end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
    start_y = max(0, int(region.y1 / patch_height))
    end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

    if start_x >= end_x or start_y >= end_y:
        return 0.0

    region_patches = patch_scores[start_y:end_y, start_x:end_x]
    return float(np.sum(region_patches))


def aggregate_patch_scores_iou_weighted(
    patch_scores: NDArray[np.floating],
    region: Box,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores using IoU-weighted sum (canonical method).

    This is the recommended aggregation method as it accounts for
    partial overlap between patches and regions.

    Formula: sum(score * IoU(patch, region)) for all patches

    Args:
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        region: Normalized region bounding box
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        IoU-weighted sum of patch scores
    """
    if patch_scores.shape != (n_patches_y, n_patches_x):
        raise ValueError(
            f"patch_scores shape {patch_scores.shape} does not match "
            f"expected ({n_patches_y}, {n_patches_x})"
        )

    # Get IoU weights for all patches
    iou_weights = patches_to_region_iou_weights(
        region, n_patches_x, n_patches_y
    )

    # Compute weighted sum
    weighted_scores = patch_scores * iou_weights
    return float(np.sum(weighted_scores))


def aggregate_patch_scores(
    patch_scores: NDArray[np.floating],
    region: Box,
    method: AggregationMethod = AggregationMethod.IOU_WEIGHTED,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores to region score using specified method.

    Args:
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        region: Normalized region bounding box
        method: Aggregation method to use
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Aggregated region score
    """
    aggregators = {
        AggregationMethod.MAX: aggregate_patch_scores_max,
        AggregationMethod.MEAN: aggregate_patch_scores_mean,
        AggregationMethod.SUM: aggregate_patch_scores_sum,
        AggregationMethod.IOU_WEIGHTED: aggregate_patch_scores_iou_weighted,
    }

    aggregator = aggregators.get(method)
    if aggregator is None:
        raise ValueError(f"Unknown aggregation method: {method}")

    return aggregator(patch_scores, region, n_patches_x, n_patches_y)


def aggregate_multi_token_scores(
    token_patch_scores: List[NDArray[np.floating]],
    region: Box,
    method: AggregationMethod = AggregationMethod.IOU_WEIGHTED,
    token_aggregation: str = "max",
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> float:
    """
    Aggregate patch scores across multiple query tokens.

    Args:
        token_patch_scores: List of 2D arrays, one per query token
        region: Normalized region bounding box
        method: Spatial aggregation method for patches -> region
        token_aggregation: How to aggregate across tokens ('max', 'mean', 'sum')
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        Final aggregated region score
    """
    if not token_patch_scores:
        return 0.0

    # Get per-token region scores
    token_scores = [
        aggregate_patch_scores(
            scores, region, method, n_patches_x, n_patches_y
        )
        for scores in token_patch_scores
    ]

    # Aggregate across tokens
    if token_aggregation == "max":
        return max(token_scores)
    elif token_aggregation == "mean":
        return float(np.mean(token_scores))
    elif token_aggregation == "sum":
        return sum(token_scores)
    else:
        raise ValueError(f"Unknown token aggregation: {token_aggregation}")


def compute_region_scores(
    regions: List[Box],
    patch_scores: NDArray[np.floating],
    method: AggregationMethod = AggregationMethod.IOU_WEIGHTED,
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> List[Tuple[int, float]]:
    """
    Compute scores for all regions.

    Args:
        regions: List of normalized region bounding boxes
        patch_scores: 2D array of shape (n_patches_y, n_patches_x)
        method: Aggregation method to use
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        List of (region_index, score) tuples sorted by score descending
    """
    scored_regions = []
    for idx, region in enumerate(regions):
        score = aggregate_patch_scores(
            patch_scores, region, method, n_patches_x, n_patches_y
        )
        scored_regions.append((idx, score))

    # Sort by score descending
    scored_regions.sort(key=lambda x: x[1], reverse=True)
    return scored_regions


def compute_region_scores_multi_token(
    regions: List[Box],
    token_patch_scores: List[NDArray[np.floating]],
    method: AggregationMethod = AggregationMethod.IOU_WEIGHTED,
    token_aggregation: str = "max",
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> List[Tuple[int, float]]:
    """
    Compute scores for all regions with multi-token queries.

    Args:
        regions: List of normalized region bounding boxes
        token_patch_scores: List of 2D arrays, one per query token
        method: Spatial aggregation method for patches -> region
        token_aggregation: How to aggregate across tokens
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        List of (region_index, score) tuples sorted by score descending
    """
    scored_regions = []
    for idx, region in enumerate(regions):
        score = aggregate_multi_token_scores(
            token_patch_scores,
            region,
            method,
            token_aggregation,
            n_patches_x,
            n_patches_y,
        )
        scored_regions.append((idx, score))

    # Sort by score descending
    scored_regions.sort(key=lambda x: x[1], reverse=True)
    return scored_regions
