"""
Patch-to-region aggregation methods.

This module implements various strategies for aggregating patch-level similarity
scores from ColPali to region-level relevance scores for OCR-extracted regions.

Methods:
- max: Highest-scoring overlapping patch
- mean: Average of overlapping patches
- sum: Sum of overlapping patches
- iou_weighted: Unnormalized weighted sum (canonical method from paper)
- iou_weighted_norm: IoU-weighted mean (normalized by total IoU to remove region size bias)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from .utils.coordinates import (
    get_overlapping_patches,
    normalize_bbox,
)

logger = logging.getLogger(__name__)


# Aggregation method types
AggregationMethod = Literal["max", "mean", "sum", "iou_weighted", "iou_weighted_norm"]


@dataclass
class RegionScore:
    """Score result for a single OCR region."""

    region_id: str
    score: float
    bbox: Tuple[float, float, float, float]  # Normalized (x1, y1, x2, y2)
    content: str = ""
    label: str = ""
    patch_count: int = 0  # Number of overlapping patches
    raw_region: Optional[Dict[str, Any]] = None


class PatchToRegionAggregator:
    """
    Aggregates patch-level similarity scores to OCR region scores.

    Supports multiple aggregation methods and handles coordinate normalization.
    """

    def __init__(
        self,
        grid_x: int = 32,
        grid_y: int = 32,
        default_method: AggregationMethod = "iou_weighted",
    ):
        """
        Initialize the aggregator.

        Args:
            grid_x: Number of patches in x dimension
            grid_y: Number of patches in y dimension
            default_method: Default aggregation method
        """
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.default_method = default_method

    def aggregate(
        self,
        heatmap: np.ndarray,
        regions: List[Dict[str, Any]],
        method: Optional[AggregationMethod] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> List[RegionScore]:
        """
        Aggregate patch scores to region scores.

        Args:
            heatmap: 2D array of patch scores (grid_y × grid_x)
            regions: List of OCR region dictionaries with 'bbox' field
            method: Aggregation method to use
            image_width: Original image width (for pixel → normalized conversion)
            image_height: Original image height (for pixel → normalized conversion)

        Returns:
            List of RegionScore objects sorted by score descending
        """
        # Use actual heatmap dimensions instead of fixed grid
        actual_grid_y, actual_grid_x = heatmap.shape

        method = method or self.default_method
        results = []

        for region in regions:
            score_result = self._score_region(
                heatmap=heatmap,
                region=region,
                method=method,
                image_width=image_width,
                image_height=image_height,
                grid_x=actual_grid_x,
                grid_y=actual_grid_y,
            )
            if score_result:
                results.append(score_result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def aggregate_multi_token(
        self,
        similarity_maps: List[np.ndarray],
        regions: List[Dict[str, Any]],
        method: AggregationMethod = "iou_weighted",
        token_aggregation: Literal["max", "mean", "sum"] = "max",
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> List[RegionScore]:
        """
        Aggregate multiple per-token similarity maps to region scores.

        Uses the correct late-interaction order:
        1. For each token: compute IoU-weighted region score
        2. Aggregate across tokens (max/mean/sum)

        This preserves the per-token independence that is key to late interaction,
        rather than combining token maps first (which loses per-token granularity).

        Formula: rel(Q, R) = AGG_tokens [ Σ_patches IoU(p, R) × sim(token, p) ]

        Args:
            similarity_maps: List of 2D arrays, one per query token
            regions: List of OCR region dictionaries
            method: Patch-to-region aggregation method (applied per-token)
            token_aggregation: How to combine scores across tokens
            image_width: Original image width
            image_height: Original image height

        Returns:
            List of RegionScore objects sorted by score descending
        """
        if not similarity_maps:
            logger.warning("No similarity maps provided")
            return []

        if not regions:
            return []

        # Get grid dimensions from first similarity map
        grid_y, grid_x = similarity_maps[0].shape

        results = []
        for region in regions:
            bbox = region.get("bbox", [])
            if not bbox or len(bbox) < 4:
                continue

            # Normalize bbox to [0, 1] space
            normalized_bbox = normalize_bbox(
                bbox=bbox,
                image_width=image_width,
                image_height=image_height,
            )

            # Get overlapping patches with their IoU values
            overlapping = get_overlapping_patches(
                region_box=normalized_bbox,
                grid_x=grid_x,
                grid_y=grid_y,
                min_overlap=0.0,
            )

            if not overlapping:
                # No overlapping patches - zero score
                results.append(RegionScore(
                    region_id=region.get("id", ""),
                    score=0.0,
                    bbox=normalized_bbox,
                    content=region.get("content", ""),
                    label=region.get("label", ""),
                    patch_count=0,
                    raw_region=region,
                ))
                continue

            # Compute per-token region scores
            token_scores = []
            for token_map in similarity_maps:
                # Extract patch scores and IoU values for this token
                patch_scores = np.array([token_map[py, px] for px, py, _ in overlapping])
                ious = np.array([iou for _, _, iou in overlapping])

                # Apply aggregation method for this token's region score
                if method == "max":
                    token_score = float(np.max(patch_scores))
                elif method == "mean":
                    token_score = float(np.mean(patch_scores))
                elif method == "sum":
                    token_score = float(np.sum(patch_scores))
                elif method == "iou_weighted":
                    # Canonical: unnormalized IoU-weighted sum
                    token_score = float(np.sum(patch_scores * ious))
                elif method == "iou_weighted_norm":
                    # Normalized variant
                    total_iou = np.sum(ious)
                    if total_iou > 0:
                        token_score = float(np.sum(patch_scores * ious) / total_iou)
                    else:
                        token_score = 0.0
                else:
                    raise ValueError(f"Unknown aggregation method: {method}")

                token_scores.append(token_score)

            # Aggregate across tokens
            if token_aggregation == "max":
                final_score = float(np.max(token_scores))
            elif token_aggregation == "mean":
                final_score = float(np.mean(token_scores))
            elif token_aggregation == "sum":
                final_score = float(np.sum(token_scores))
            else:
                raise ValueError(f"Unknown token aggregation: {token_aggregation}")

            results.append(RegionScore(
                region_id=region.get("id", ""),
                score=final_score,
                bbox=normalized_bbox,
                content=region.get("content", ""),
                label=region.get("label", ""),
                patch_count=len(overlapping),
                raw_region=region,
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def _score_region(
        self,
        heatmap: np.ndarray,
        region: Dict[str, Any],
        method: AggregationMethod,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        grid_x: Optional[int] = None,
        grid_y: Optional[int] = None,
    ) -> Optional[RegionScore]:
        """
        Compute relevance score for a single region.

        Args:
            heatmap: 2D array of patch scores
            region: OCR region dictionary
            method: Aggregation method
            image_width: Original image width
            image_height: Original image height
            grid_x: Grid width (defaults to self.grid_x if not provided)
            grid_y: Grid height (defaults to self.grid_y if not provided)

        Returns:
            RegionScore or None if region is invalid
        """
        # Use provided grid dimensions or fall back to instance defaults
        grid_x = grid_x if grid_x is not None else self.grid_x
        grid_y = grid_y if grid_y is not None else self.grid_y

        bbox = region.get("bbox", [])
        if not bbox or len(bbox) < 4:
            return None

        # Normalize bbox to [0, 1] space using shared utility
        normalized_bbox = normalize_bbox(
            bbox=bbox,
            image_width=image_width,
            image_height=image_height,
        )

        # Get overlapping patches with their IoU values
        overlapping = get_overlapping_patches(
            region_box=normalized_bbox,
            grid_x=grid_x,
            grid_y=grid_y,
            min_overlap=0.0,
        )

        if not overlapping:
            return RegionScore(
                region_id=region.get("id", ""),
                score=0.0,
                bbox=normalized_bbox,
                content=region.get("content", ""),
                label=region.get("label", ""),
                patch_count=0,
                raw_region=region,
            )

        # Extract patch scores and IoU values
        patch_scores = []
        ious = []
        for px, py, iou in overlapping:
            patch_scores.append(heatmap[py, px])
            ious.append(iou)

        patch_scores = np.array(patch_scores)
        ious = np.array(ious)

        # Apply aggregation method
        if method == "max":
            score = float(np.max(patch_scores))
        elif method == "mean":
            score = float(np.mean(patch_scores))
        elif method == "sum":
            score = float(np.sum(patch_scores))
        elif method == "iou_weighted":
            # Canonical method from paper: unnormalized weighted sum
            # rel(q,r) = Σⱼ IoU(region, patch_j) · score_patch(j)
            score = float(np.sum(patch_scores * ious))
        elif method == "iou_weighted_norm":
            # Normalized variant: weighted mean to remove region size bias
            # rel(q,r) = Σⱼ IoU(...) · score(j) / Σⱼ IoU(...)
            total_iou = np.sum(ious)
            if total_iou > 0:
                score = float(np.sum(patch_scores * ious) / total_iou)
            else:
                score = 0.0
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

        return RegionScore(
            region_id=region.get("id", ""),
            score=score,
            bbox=normalized_bbox,
            content=region.get("content", ""),
            label=region.get("label", ""),
            patch_count=len(overlapping),
            raw_region=region,
        )


def compute_score_confidence(scores: List[float]) -> Dict[str, float]:
    """
    Compute confidence metrics from a list of region scores.

    Returns multiple metrics that can indicate whether the model is confident
    about which regions are relevant.

    Args:
        scores: List of region scores (should be sorted descending)

    Returns:
        Dictionary with confidence metrics:
        - coefficient_of_variation: std/mean - higher = more spread = more confident
        - top1_gap: Gap between top score and mean of rest
        - top3_gap: Gap between mean of top-3 and mean of rest
        - normalized_entropy: Entropy of score distribution (0=certain, 1=uniform)
    """
    if not scores or len(scores) < 2:
        return {
            "coefficient_of_variation": 0.0,
            "top1_gap": 0.0,
            "top3_gap": 0.0,
            "normalized_entropy": 1.0,
        }

    scores_arr = np.array(scores)

    # Coefficient of variation (higher = more discriminative)
    mean_score = np.mean(scores_arr)
    std_score = np.std(scores_arr)
    cv = std_score / mean_score if mean_score > 0 else 0.0

    # Top-1 gap: how much does the top score stand out?
    top1 = scores_arr[0]
    rest_mean = np.mean(scores_arr[1:]) if len(scores_arr) > 1 else 0.0
    top1_gap = (top1 - rest_mean) / top1 if top1 > 0 else 0.0

    # Top-3 gap: how much do top-3 stand out from rest?
    k = min(3, len(scores_arr))
    top_k_mean = np.mean(scores_arr[:k])
    rest_k_mean = np.mean(scores_arr[k:]) if len(scores_arr) > k else 0.0
    top3_gap = (top_k_mean - rest_k_mean) / top_k_mean if top_k_mean > 0 else 0.0

    # Normalized entropy (0 = one region dominates, 1 = uniform distribution)
    # Shift scores to be positive for probability calculation
    min_score = np.min(scores_arr)
    shifted = scores_arr - min_score + 1e-10
    probs = shifted / np.sum(shifted)
    entropy = -np.sum(probs * np.log(probs + 1e-10))
    max_entropy = np.log(len(scores_arr))
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 1.0

    return {
        "coefficient_of_variation": float(cv),
        "top1_gap": float(top1_gap),
        "top3_gap": float(top3_gap),
        "normalized_entropy": float(normalized_entropy),
    }


def select_with_confidence_fallback(
    scored_regions: List[RegionScore],
    selection_fn: callable,
    confidence_threshold: float = 0.3,
    confidence_metric: str = "top1_gap",
) -> Tuple[List[RegionScore], Dict[str, Any]]:
    """
    Apply selection with confidence-based fallback.

    If confidence is below threshold, returns all regions instead of
    applying the selection function.

    Args:
        scored_regions: List of RegionScore objects (sorted by score descending)
        selection_fn: Function that takes scored_regions and returns filtered list
        confidence_threshold: Minimum confidence to apply selection
        confidence_metric: Which metric to use ("top1_gap", "top3_gap", "coefficient_of_variation")

    Returns:
        Tuple of (selected_regions, metadata_dict)
        metadata_dict contains:
        - confidence_metrics: All computed metrics
        - confident: Whether confidence threshold was met
        - fallback_used: Whether we returned all regions
    """
    if not scored_regions:
        return [], {"confidence_metrics": {}, "confident": False, "fallback_used": True}

    scores = [r.score for r in scored_regions]
    confidence_metrics = compute_score_confidence(scores)

    # Get the specified confidence value
    confidence_value = confidence_metrics.get(confidence_metric, 0.0)

    # For entropy, lower is better (invert the logic)
    if confidence_metric == "normalized_entropy":
        is_confident = confidence_value < (1.0 - confidence_threshold)
    else:
        is_confident = confidence_value >= confidence_threshold

    metadata = {
        "confidence_metrics": confidence_metrics,
        "confidence_metric_used": confidence_metric,
        "confidence_value": confidence_value,
        "confidence_threshold": confidence_threshold,
        "confident": is_confident,
        "fallback_used": not is_confident,
    }

    if is_confident:
        # Apply normal selection
        selected = selection_fn(scored_regions)
        metadata["selection_applied"] = True
        return selected, metadata
    else:
        # Low confidence - return all regions
        logger.info(
            f"Low confidence ({confidence_metric}={confidence_value:.3f} < {confidence_threshold}), "
            f"returning all {len(scored_regions)} regions"
        )
        metadata["selection_applied"] = False
        return scored_regions, metadata
