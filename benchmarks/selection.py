"""
Region Selection Strategies.

This module provides methods to select relevant regions from scored candidates.

Selection methods:
- top_k: Fixed K top-scoring regions
- threshold: Regions above score threshold
- percentile: Top X% of scores
- otsu: Automatic threshold using Otsu's method
- elbow: Knee point detection in sorted curve
- gap: Largest gap between consecutive scores
- relative: Regions >= fraction of max score
"""

from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


class SelectionMethod(str, Enum):
    """Available selection methods."""

    TOP_K = "top_k"
    THRESHOLD = "threshold"
    PERCENTILE = "percentile"
    OTSU = "otsu"
    ELBOW = "elbow"
    GAP = "gap"
    RELATIVE = "relative"


def select_top_k(
    scored_regions: List[Tuple[int, float]],
    k: int,
) -> List[Tuple[int, float]]:
    """
    Select top K scoring regions.

    Args:
        scored_regions: List of (region_index, score) tuples, should be pre-sorted
        k: Number of regions to select

    Returns:
        Top K regions as (index, score) tuples
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    # Ensure sorted by score descending
    sorted_regions = sorted(scored_regions, key=lambda x: x[1], reverse=True)
    return sorted_regions[:k]


def select_by_threshold(
    scored_regions: List[Tuple[int, float]],
    threshold: float,
) -> List[Tuple[int, float]]:
    """
    Select regions with scores above threshold.

    Args:
        scored_regions: List of (region_index, score) tuples
        threshold: Minimum score threshold

    Returns:
        Regions with score >= threshold
    """
    return [
        (idx, score) for idx, score in scored_regions if score >= threshold
    ]


def select_by_percentile(
    scored_regions: List[Tuple[int, float]],
    percentile: float,
) -> List[Tuple[int, float]]:
    """
    Select regions in top X percentile of scores.

    Args:
        scored_regions: List of (region_index, score) tuples
        percentile: Percentile threshold (0-100)

    Returns:
        Regions with scores in top percentile
    """
    if not 0 <= percentile <= 100:
        raise ValueError(f"percentile must be in [0, 100], got {percentile}")

    if not scored_regions:
        return []

    scores = np.array([score for _, score in scored_regions])
    threshold = np.percentile(scores, 100 - percentile)

    return [
        (idx, score) for idx, score in scored_regions if score >= threshold
    ]


def select_by_otsu(
    scored_regions: List[Tuple[int, float]],
    n_bins: int = 256,
) -> List[Tuple[int, float]]:
    """
    Select regions using Otsu's automatic thresholding.

    Otsu's method finds the threshold that minimizes intra-class variance,
    effectively separating foreground (relevant) from background (irrelevant).

    Args:
        scored_regions: List of (region_index, score) tuples
        n_bins: Number of histogram bins

    Returns:
        Regions above Otsu threshold
    """
    if not scored_regions:
        return []

    scores = np.array([score for _, score in scored_regions])

    if len(scores) < 2:
        return list(scored_regions)

    # Handle edge case where all scores are the same
    if np.all(scores == scores[0]):
        return list(scored_regions)

    # Normalize scores to [0, 1]
    min_score = np.min(scores)
    max_score = np.max(scores)
    if max_score == min_score:
        return list(scored_regions)

    normalized = (scores - min_score) / (max_score - min_score)

    # Compute histogram
    hist, bin_edges = np.histogram(normalized, bins=n_bins, range=(0, 1))
    hist = hist.astype(float)
    total = hist.sum()

    if total == 0:
        return list(scored_regions)

    # Compute Otsu threshold
    best_threshold = 0.0
    best_variance = 0.0

    sum_total = np.sum(np.arange(n_bins) * hist)
    sum_bg = 0.0
    weight_bg = 0.0

    for t in range(n_bins):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue

        weight_fg = total - weight_bg
        if weight_fg == 0:
            break

        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg

        # Between-class variance
        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

        if variance > best_variance:
            best_variance = variance
            best_threshold = (t + 1) / n_bins

    # Convert back to original scale
    threshold = min_score + best_threshold * (max_score - min_score)

    return [
        (idx, score) for idx, score in scored_regions if score >= threshold
    ]


def select_by_elbow(
    scored_regions: List[Tuple[int, float]],
    sensitivity: float = 1.0,
) -> List[Tuple[int, float]]:
    """
    Select regions using elbow/knee point detection.

    Finds the point of maximum curvature in the sorted score curve.

    Args:
        scored_regions: List of (region_index, score) tuples
        sensitivity: Controls how sensitive the knee detection is (higher = more sensitive)

    Returns:
        Regions up to and including the elbow point
    """
    if not scored_regions:
        return []

    # Sort by score descending
    sorted_regions = sorted(scored_regions, key=lambda x: x[1], reverse=True)
    scores = np.array([score for _, score in sorted_regions])

    if len(scores) < 3:
        return list(sorted_regions)

    # Normalize scores and indices to [0, 1]
    n = len(scores)
    x = np.arange(n) / (n - 1)
    y = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)

    # Line from first to last point
    line_vec = np.array([x[-1] - x[0], y[-1] - y[0]])
    line_len = np.linalg.norm(line_vec)

    if line_len < 1e-10:
        return list(sorted_regions)

    line_unit = line_vec / line_len

    # Calculate perpendicular distance from each point to the line
    distances = []
    for i in range(n):
        point_vec = np.array([x[i] - x[0], y[i] - y[0]])
        proj_length = np.dot(point_vec, line_unit)
        proj_vec = proj_length * line_unit
        perp_vec = point_vec - proj_vec
        distances.append(np.linalg.norm(perp_vec) * sensitivity)

    # Find the knee point (maximum distance)
    knee_idx = np.argmax(distances)

    # Return regions up to and including knee point
    return sorted_regions[: knee_idx + 1]


def select_by_gap(
    scored_regions: List[Tuple[int, float]],
    min_regions: int = 1,
) -> List[Tuple[int, float]]:
    """
    Select regions using largest gap detection.

    Finds the largest gap between consecutive sorted scores
    and selects all regions above that gap.

    Args:
        scored_regions: List of (region_index, score) tuples
        min_regions: Minimum number of regions to return

    Returns:
        Regions above the largest gap
    """
    if not scored_regions:
        return []

    # Sort by score descending
    sorted_regions = sorted(scored_regions, key=lambda x: x[1], reverse=True)
    scores = np.array([score for _, score in sorted_regions])

    if len(scores) < 2:
        return list(sorted_regions)

    # Calculate gaps between consecutive scores
    gaps = np.abs(np.diff(scores))

    if len(gaps) == 0:
        return list(sorted_regions)

    # Find largest gap
    largest_gap_idx = np.argmax(gaps)

    # Select regions before the gap (higher scores)
    cut_point = max(min_regions, largest_gap_idx + 1)

    return sorted_regions[:cut_point]


def select_by_relative(
    scored_regions: List[Tuple[int, float]],
    fraction: float,
) -> List[Tuple[int, float]]:
    """
    Select regions with scores >= fraction of max score.

    Args:
        scored_regions: List of (region_index, score) tuples
        fraction: Fraction of max score (0-1)

    Returns:
        Regions with score >= fraction * max_score
    """
    if not 0 <= fraction <= 1:
        raise ValueError(f"fraction must be in [0, 1], got {fraction}")

    if not scored_regions:
        return []

    max_score = max(score for _, score in scored_regions)
    threshold = fraction * max_score

    return [
        (idx, score) for idx, score in scored_regions if score >= threshold
    ]


def select_regions(
    scored_regions: List[Tuple[int, float]],
    method: SelectionMethod,
    **kwargs,
) -> List[Tuple[int, float]]:
    """
    Select regions using specified method.

    Args:
        scored_regions: List of (region_index, score) tuples
        method: Selection method to use
        **kwargs: Method-specific parameters:
            - top_k: k (int)
            - threshold: threshold (float)
            - percentile: percentile (float)
            - otsu: n_bins (int, optional)
            - elbow: sensitivity (float, optional)
            - gap: min_regions (int, optional)
            - relative: fraction (float)

    Returns:
        Selected regions as (index, score) tuples
    """
    selectors = {
        SelectionMethod.TOP_K: lambda sr: select_top_k(sr, kwargs.get("k", 5)),
        SelectionMethod.THRESHOLD: lambda sr: select_by_threshold(
            sr, kwargs.get("threshold", 0.5)
        ),
        SelectionMethod.PERCENTILE: lambda sr: select_by_percentile(
            sr, kwargs.get("percentile", 90)
        ),
        SelectionMethod.OTSU: lambda sr: select_by_otsu(
            sr, kwargs.get("n_bins", 256)
        ),
        SelectionMethod.ELBOW: lambda sr: select_by_elbow(
            sr, kwargs.get("sensitivity", 1.0)
        ),
        SelectionMethod.GAP: lambda sr: select_by_gap(
            sr, kwargs.get("min_regions", 1)
        ),
        SelectionMethod.RELATIVE: lambda sr: select_by_relative(
            sr, kwargs.get("fraction", 0.5)
        ),
    }

    selector = selectors.get(method)
    if selector is None:
        raise ValueError(f"Unknown selection method: {method}")

    return selector(scored_regions)


def select_regions_ensemble(
    scored_regions: List[Tuple[int, float]],
    methods: List[Tuple[SelectionMethod, dict]],
    voting: str = "intersection",
) -> List[Tuple[int, float]]:
    """
    Select regions using ensemble of methods.

    Args:
        scored_regions: List of (region_index, score) tuples
        methods: List of (method, kwargs) tuples
        voting: How to combine results:
            - 'intersection': regions selected by all methods
            - 'union': regions selected by any method
            - 'majority': regions selected by >50% of methods

    Returns:
        Selected regions as (index, score) tuples
    """
    if not methods:
        raise ValueError("At least one method must be provided")

    # Get selections from each method
    all_selections = []
    for method, kwargs in methods:
        selected = select_regions(scored_regions, method, **kwargs)
        selected_indices = {idx for idx, _ in selected}
        all_selections.append(selected_indices)

    # Combine based on voting strategy
    if voting == "intersection":
        final_indices = set.intersection(*all_selections) if all_selections else set()
    elif voting == "union":
        final_indices = set.union(*all_selections) if all_selections else set()
    elif voting == "majority":
        n_methods = len(methods)
        index_counts: dict = {}
        for indices in all_selections:
            for idx in indices:
                index_counts[idx] = index_counts.get(idx, 0) + 1
        final_indices = {
            idx for idx, count in index_counts.items() if count > n_methods / 2
        }
    else:
        raise ValueError(f"Unknown voting strategy: {voting}")

    # Return regions with original scores, sorted
    result = [(idx, score) for idx, score in scored_regions if idx in final_indices]
    result.sort(key=lambda x: x[1], reverse=True)
    return result
