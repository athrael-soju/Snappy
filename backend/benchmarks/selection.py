"""
Region selection strategies for filtering relevant OCR regions.

This module implements various strategies for selecting the most relevant
regions from scored OCR regions.

Methods:
- top_k: Fixed number of top-scoring regions
- threshold: Regions above absolute score threshold
- percentile: Top X% of scores
- otsu: Automatic threshold via Otsu's method
- elbow: Knee point in sorted score curve
- gap: Largest gap between consecutive scores
- relative: Regions ≥ fraction of max score
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from .aggregation import RegionScore, compute_score_confidence

logger = logging.getLogger(__name__)


# Selection method types
SelectionMethod = Literal[
    "top_k", "threshold", "percentile", "otsu", "elbow", "gap", "relative",
    "confidence_gated"
]


@dataclass
class SelectionResult:
    """Result of region selection."""

    selected_regions: List[RegionScore]
    method: str
    threshold_used: Optional[float] = None
    params: Optional[Dict[str, Any]] = None
    confidence_metrics: Optional[Dict[str, float]] = None
    fallback_used: bool = False


class RegionSelector:
    """
    Selects relevant regions from scored OCR regions.

    Supports multiple selection strategies for different use cases.
    """

    def __init__(self, default_method: SelectionMethod = "top_k"):
        """
        Initialize the selector.

        Args:
            default_method: Default selection method
        """
        self.default_method = default_method

    def select(
        self,
        region_scores: List[RegionScore],
        method: Optional[SelectionMethod] = None,
        k: int = 5,
        threshold: float = 0.0,
        percentile: float = 90.0,
        relative_threshold: float = 0.5,
        confidence_threshold: float = 0.3,
        confidence_metric: str = "top1_gap",
        fallback_method: str = "otsu",
    ) -> SelectionResult:
        """
        Select regions using the specified method.

        Args:
            region_scores: List of RegionScore objects (assumed sorted desc)
            method: Selection method to use
            k: Number of regions for top_k method (use k=0 to select all)
            threshold: Absolute threshold for threshold method
            percentile: Percentile for percentile method (e.g., 90 = top 10%)
            relative_threshold: Fraction of max score for relative method
            confidence_threshold: Minimum confidence to apply selection (for confidence_gated)
            confidence_metric: Metric for confidence ("top1_gap", "coefficient_of_variation")
            fallback_method: Method to use when confident (for confidence_gated)

        Returns:
            SelectionResult with selected regions
        """
        method = method or self.default_method

        if not region_scores:
            return SelectionResult(
                selected_regions=[],
                method=method,
                threshold_used=None,
                params={},
            )

        # Dispatch to appropriate method
        if method == "top_k":
            return self._select_top_k(region_scores, k)
        elif method == "threshold":
            return self._select_threshold(region_scores, threshold)
        elif method == "percentile":
            return self._select_percentile(region_scores, percentile)
        elif method == "otsu":
            return self._select_otsu(region_scores)
        elif method == "elbow":
            return self._select_elbow(region_scores)
        elif method == "gap":
            return self._select_gap(region_scores)
        elif method == "relative":
            return self._select_relative(region_scores, relative_threshold)
        elif method == "confidence_gated":
            return self._select_confidence_gated(
                region_scores,
                confidence_threshold=confidence_threshold,
                confidence_metric=confidence_metric,
                fallback_method=fallback_method,
                k=k,
                threshold=threshold,
                percentile=percentile,
                relative_threshold=relative_threshold,
            )
        else:
            raise ValueError(f"Unknown selection method: {method}")

    def _select_top_k(
        self, region_scores: List[RegionScore], k: int
    ) -> SelectionResult:
        """Select top k regions by score. Use k=0 to select all regions."""
        if k <= 0:
            # k=0 means select all regions (no limit)
            selected = region_scores
            threshold = selected[-1].score if selected else 0.0
            return SelectionResult(
                selected_regions=selected,
                method="top_k",
                threshold_used=threshold,
                params={"k": 0, "count": len(selected)},
            )

        selected = region_scores[:k]
        threshold = selected[-1].score if selected else 0.0

        return SelectionResult(
            selected_regions=selected,
            method="top_k",
            threshold_used=threshold,
            params={"k": k},
        )

    def _select_threshold(
        self, region_scores: List[RegionScore], threshold: float
    ) -> SelectionResult:
        """Select regions above absolute threshold."""
        selected = [r for r in region_scores if r.score >= threshold]

        return SelectionResult(
            selected_regions=selected,
            method="threshold",
            threshold_used=threshold,
            params={"threshold": threshold},
        )

    def _select_percentile(
        self, region_scores: List[RegionScore], percentile: float
    ) -> SelectionResult:
        """Select top X% of regions by score."""
        scores = np.array([r.score for r in region_scores])
        threshold = np.percentile(scores, percentile)
        selected = [r for r in region_scores if r.score >= threshold]

        return SelectionResult(
            selected_regions=selected,
            method="percentile",
            threshold_used=float(threshold),
            params={"percentile": percentile},
        )

    def _select_otsu(self, region_scores: List[RegionScore]) -> SelectionResult:
        """
        Select regions using Otsu's automatic thresholding.

        Otsu's method finds the threshold that minimizes intra-class variance,
        effectively separating scores into two groups.
        """
        scores = np.array([r.score for r in region_scores])

        if len(scores) < 2:
            return SelectionResult(
                selected_regions=region_scores,
                method="otsu",
                threshold_used=0.0,
                params={},
            )

        # Normalize scores to [0, 1] for Otsu's method
        score_min, score_max = scores.min(), scores.max()
        if score_max - score_min < 1e-8:
            # All scores are the same
            return SelectionResult(
                selected_regions=region_scores,
                method="otsu",
                threshold_used=float(score_min),
                params={},
            )

        normalized = (scores - score_min) / (score_max - score_min)

        # Compute Otsu's threshold
        threshold_norm = self._otsu_threshold(normalized)

        # Convert back to original scale
        threshold = threshold_norm * (score_max - score_min) + score_min
        selected = [r for r in region_scores if r.score >= threshold]

        return SelectionResult(
            selected_regions=selected,
            method="otsu",
            threshold_used=float(threshold),
            params={"normalized_threshold": float(threshold_norm)},
        )

    def _otsu_threshold(self, values: np.ndarray) -> float:
        """
        Compute Otsu's threshold for 1D values in [0, 1].

        Args:
            values: Array of values in [0, 1]

        Returns:
            Optimal threshold value
        """
        # Create histogram
        n_bins = min(256, len(values))
        hist, bin_edges = np.histogram(values, bins=n_bins, range=(0, 1))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # Compute class probabilities and means
        total = hist.sum()
        if total == 0:
            return 0.5

        # Cumulative sums
        weight_bg = np.cumsum(hist)
        weight_fg = total - weight_bg

        # Cumulative means
        mean_bg_cumsum = np.cumsum(hist * bin_centers)

        # Avoid division by zero
        weight_bg = np.where(weight_bg == 0, 1, weight_bg)
        weight_fg = np.where(weight_fg == 0, 1, weight_fg)

        mean_bg = mean_bg_cumsum / weight_bg
        mean_fg = (mean_bg_cumsum[-1] - mean_bg_cumsum) / weight_fg

        # Between-class variance
        variance_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

        # Find threshold that maximizes between-class variance
        idx = np.argmax(variance_between)
        threshold = bin_centers[idx]

        return float(threshold)

    def _select_elbow(self, region_scores: List[RegionScore]) -> SelectionResult:
        """
        Select regions using elbow/knee point detection.

        Finds the point of maximum curvature in the sorted score curve.
        """
        if len(region_scores) < 3:
            return SelectionResult(
                selected_regions=region_scores,
                method="elbow",
                threshold_used=region_scores[-1].score if region_scores else 0.0,
                params={"elbow_index": len(region_scores) - 1},
            )

        scores = np.array([r.score for r in region_scores])
        n = len(scores)

        # Normalize x and y to [0, 1] for curvature calculation
        x = np.arange(n) / (n - 1)
        y_min, y_max = scores.min(), scores.max()
        if y_max - y_min < 1e-8:
            # All scores same, return all
            return SelectionResult(
                selected_regions=region_scores,
                method="elbow",
                threshold_used=float(scores[-1]),
                params={"elbow_index": n - 1},
            )

        y = (scores - y_min) / (y_max - y_min)

        # Compute perpendicular distance from each point to line from first to last
        # Line from (0, y[0]) to (1, y[-1])
        line_vec = np.array([1, y[-1] - y[0]])
        line_vec = line_vec / np.linalg.norm(line_vec)

        distances = []
        for i in range(n):
            point_vec = np.array([x[i], y[i] - y[0]])
            # Perpendicular distance
            dist = np.abs(np.cross(line_vec, point_vec))
            distances.append(dist)

        elbow_idx = int(np.argmax(distances))

        # Select all regions up to and including elbow point
        selected = region_scores[: elbow_idx + 1]
        threshold = region_scores[elbow_idx].score

        return SelectionResult(
            selected_regions=selected,
            method="elbow",
            threshold_used=float(threshold),
            params={"elbow_index": elbow_idx},
        )

    def _select_gap(self, region_scores: List[RegionScore]) -> SelectionResult:
        """
        Select regions based on largest gap between consecutive scores.

        Useful when there's a natural break in the score distribution.
        """
        if len(region_scores) < 2:
            return SelectionResult(
                selected_regions=region_scores,
                method="gap",
                threshold_used=region_scores[0].score if region_scores else 0.0,
                params={"gap_index": 0, "gap_size": 0.0},
            )

        scores = np.array([r.score for r in region_scores])

        # Compute gaps between consecutive scores
        gaps = scores[:-1] - scores[1:]

        # Find largest gap
        gap_idx = int(np.argmax(gaps))
        gap_size = float(gaps[gap_idx])

        # Select regions before the gap
        selected = region_scores[: gap_idx + 1]
        threshold = selected[-1].score if selected else 0.0

        return SelectionResult(
            selected_regions=selected,
            method="gap",
            threshold_used=float(threshold),
            params={"gap_index": gap_idx, "gap_size": gap_size},
        )

    def _select_relative(
        self, region_scores: List[RegionScore], relative_threshold: float
    ) -> SelectionResult:
        """Select regions with score ≥ fraction of maximum score."""
        if not region_scores:
            return SelectionResult(
                selected_regions=[],
                method="relative",
                threshold_used=0.0,
                params={"relative_threshold": relative_threshold},
            )

        max_score = region_scores[0].score
        threshold = max_score * relative_threshold
        selected = [r for r in region_scores if r.score >= threshold]

        return SelectionResult(
            selected_regions=selected,
            method="relative",
            threshold_used=float(threshold),
            params={"relative_threshold": relative_threshold, "max_score": max_score},
        )

    def _select_confidence_gated(
        self,
        region_scores: List[RegionScore],
        confidence_threshold: float = 0.3,
        confidence_metric: str = "top1_gap",
        fallback_method: str = "otsu",
        k: int = 5,
        threshold: float = 0.0,
        percentile: float = 90.0,
        relative_threshold: float = 0.5,
    ) -> SelectionResult:
        """
        Select regions with confidence-based fallback.

        When the model is confident (high score separation), applies the
        fallback_method for selection. When uncertain (uniform scores),
        returns all regions.

        Args:
            region_scores: List of RegionScore objects (sorted desc)
            confidence_threshold: Minimum confidence to apply selection
            confidence_metric: Which metric to use for confidence
            fallback_method: Selection method to use when confident
            k, threshold, percentile, relative_threshold: Params for fallback method

        Returns:
            SelectionResult with confidence metadata
        """
        scores = [r.score for r in region_scores]
        confidence_metrics = compute_score_confidence(scores)

        # Get the confidence value
        confidence_value = confidence_metrics.get(confidence_metric, 0.0)

        # For entropy, lower is more confident (invert logic)
        if confidence_metric == "normalized_entropy":
            is_confident = confidence_value < (1.0 - confidence_threshold)
        else:
            is_confident = confidence_value >= confidence_threshold

        params = {
            "confidence_threshold": confidence_threshold,
            "confidence_metric": confidence_metric,
            "confidence_value": confidence_value,
            "fallback_method": fallback_method,
            "is_confident": is_confident,
        }

        if is_confident:
            # Apply the fallback selection method
            if fallback_method == "top_k":
                result = self._select_top_k(region_scores, k)
            elif fallback_method == "threshold":
                result = self._select_threshold(region_scores, threshold)
            elif fallback_method == "percentile":
                result = self._select_percentile(region_scores, percentile)
            elif fallback_method == "otsu":
                result = self._select_otsu(region_scores)
            elif fallback_method == "elbow":
                result = self._select_elbow(region_scores)
            elif fallback_method == "gap":
                result = self._select_gap(region_scores)
            elif fallback_method == "relative":
                result = self._select_relative(region_scores, relative_threshold)
            else:
                result = self._select_otsu(region_scores)

            return SelectionResult(
                selected_regions=result.selected_regions,
                method="confidence_gated",
                threshold_used=result.threshold_used,
                params={**params, "inner_params": result.params},
                confidence_metrics=confidence_metrics,
                fallback_used=False,
            )
        else:
            # Low confidence - return all regions
            logger.info(
                f"Low confidence ({confidence_metric}={confidence_value:.3f} < {confidence_threshold}), "
                f"returning all {len(region_scores)} regions"
            )
            return SelectionResult(
                selected_regions=region_scores,
                method="confidence_gated",
                threshold_used=region_scores[-1].score if region_scores else 0.0,
                params=params,
                confidence_metrics=confidence_metrics,
                fallback_used=True,
            )
