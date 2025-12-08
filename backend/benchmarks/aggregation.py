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
        if heatmap.shape != (self.grid_y, self.grid_x):
            logger.warning(
                f"Heatmap shape {heatmap.shape} doesn't match grid "
                f"({self.grid_y}, {self.grid_x})"
            )

        method = method or self.default_method
        results = []

        for region in regions:
            score_result = self._score_region(
                heatmap=heatmap,
                region=region,
                method=method,
                image_width=image_width,
                image_height=image_height,
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

        Args:
            similarity_maps: List of 2D arrays, one per query token
            regions: List of OCR region dictionaries
            method: Patch-to-region aggregation method
            token_aggregation: How to combine scores across tokens
            image_width: Original image width
            image_height: Original image height

        Returns:
            List of RegionScore objects sorted by score descending
        """
        if not similarity_maps:
            logger.warning("No similarity maps provided")
            return []

        # First, aggregate token maps to single heatmap
        stacked = np.stack(similarity_maps, axis=0)

        if token_aggregation == "max":
            heatmap = np.max(stacked, axis=0)
        elif token_aggregation == "mean":
            heatmap = np.mean(stacked, axis=0)
        elif token_aggregation == "sum":
            heatmap = np.sum(stacked, axis=0)
        else:
            raise ValueError(f"Unknown token aggregation: {token_aggregation}")

        return self.aggregate(
            heatmap=heatmap,
            regions=regions,
            method=method,
            image_width=image_width,
            image_height=image_height,
        )

    def _score_region(
        self,
        heatmap: np.ndarray,
        region: Dict[str, Any],
        method: AggregationMethod,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> Optional[RegionScore]:
        """
        Compute relevance score for a single region.

        Args:
            heatmap: 2D array of patch scores
            region: OCR region dictionary
            method: Aggregation method
            image_width: Original image width
            image_height: Original image height

        Returns:
            RegionScore or None if region is invalid
        """
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
            grid_x=self.grid_x,
            grid_y=self.grid_y,
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
