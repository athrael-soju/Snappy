"""
Region merging strategies for combining adjacent/overlapping OCR regions.

This module implements various strategies for merging nearby regions to handle
cases where answers span multiple OCR regions.

Methods:
- overlap: Merge regions with overlapping bounding boxes
- proximity: Merge regions within distance threshold
- connected: Union-find based connected component merging

Constraints:
- score_ratio_threshold: Only merge regions with similar scores
- max_area: Prevent giant merged regions by capping area
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from .aggregation import RegionScore
from .utils.coordinates import NormalizedBox, compute_iou

logger = logging.getLogger(__name__)


def _box_area(bbox: NormalizedBox) -> float:
    """Compute area of a normalized bounding box."""
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def _merged_box_area(regions: List[RegionScore]) -> float:
    """Compute area of the merged bounding box for a list of regions."""
    if not regions:
        return 0.0
    x1 = min(r.bbox[0] for r in regions)
    y1 = min(r.bbox[1] for r in regions)
    x2 = max(r.bbox[2] for r in regions)
    y2 = max(r.bbox[3] for r in regions)
    return (x2 - x1) * (y2 - y1)


# Merging method types
MergingMethod = Literal["overlap", "proximity", "connected", "none"]


@dataclass
class MergedRegion:
    """A merged region combining multiple original regions."""

    region_id: str
    score: float
    bbox: NormalizedBox
    content: str
    source_regions: List[RegionScore]
    merge_count: int

    @classmethod
    def from_single(cls, region: RegionScore) -> "MergedRegion":
        """Create a MergedRegion from a single RegionScore."""
        return cls(
            region_id=region.region_id,
            score=region.score,
            bbox=region.bbox,
            content=region.content,
            source_regions=[region],
            merge_count=1,
        )

    @classmethod
    def merge(
        cls,
        regions: List[RegionScore],
        score_method: Literal["max", "mean", "sum"] = "max",
    ) -> "MergedRegion":
        """Merge multiple regions into one."""
        if not regions:
            raise ValueError("Cannot merge empty region list")

        if len(regions) == 1:
            return cls.from_single(regions[0])

        # Compute merged bounding box (union)
        x1 = min(r.bbox[0] for r in regions)
        y1 = min(r.bbox[1] for r in regions)
        x2 = max(r.bbox[2] for r in regions)
        y2 = max(r.bbox[3] for r in regions)
        merged_bbox = (x1, y1, x2, y2)

        # Compute merged score
        scores = [r.score for r in regions]
        if score_method == "max":
            merged_score = max(scores)
        elif score_method == "mean":
            merged_score = sum(scores) / len(scores)
        elif score_method == "sum":
            merged_score = sum(scores)
        else:
            merged_score = max(scores)

        # Combine content
        merged_content = " ".join(r.content for r in regions if r.content)

        # Create merged ID
        merged_id = f"merged_{regions[0].region_id}"

        return cls(
            region_id=merged_id,
            score=merged_score,
            bbox=merged_bbox,
            content=merged_content,
            source_regions=regions,
            merge_count=len(regions),
        )

    def to_region_score(self) -> RegionScore:
        """Convert back to RegionScore for compatibility."""
        return RegionScore(
            region_id=self.region_id,
            score=self.score,
            bbox=self.bbox,
            content=self.content,
            label="merged",
            patch_count=sum(r.patch_count for r in self.source_regions),
            raw_region={
                "merged_from": [r.region_id for r in self.source_regions],
                # Store source bboxes and labels for accurate token calculation
                # (we send individual crops, not one union crop)
                "source_bboxes": [r.bbox for r in self.source_regions],
                "source_labels": [r.label for r in self.source_regions],
                "source_contents": [r.content for r in self.source_regions],
            },
        )


@dataclass
class MergingResult:
    """Result of region merging."""

    merged_regions: List[MergedRegion]
    method: str
    original_count: int
    merged_count: int
    params: Optional[Dict[str, Any]] = None


class RegionMerger:
    """
    Merges nearby regions to handle fragmented answers.

    Supports multiple merging strategies based on spatial relationships.
    """

    def __init__(self, default_method: MergingMethod = "proximity"):
        """
        Initialize the merger.

        Args:
            default_method: Default merging method
        """
        self.default_method = default_method

    def merge(
        self,
        regions: List[RegionScore],
        method: Optional[MergingMethod] = None,
        overlap_threshold: float = 0.0,
        distance_threshold: float = 0.05,
        score_method: Literal["max", "mean", "sum"] = "max",
        score_ratio_threshold: float = 0.0,
        max_area: float = 1.0,
    ) -> MergingResult:
        """
        Merge regions using the specified method.

        Args:
            regions: List of RegionScore objects
            method: Merging method to use
            overlap_threshold: Minimum IoU for overlap-based merging
            distance_threshold: Maximum distance for proximity-based merging
            score_method: How to combine scores of merged regions
            score_ratio_threshold: Only merge if min_score/max_score >= threshold (0=disabled)
            max_area: Maximum area of merged region in normalized [0,1] space (1.0=no limit)

        Returns:
            MergingResult with merged regions
        """
        method = method or self.default_method

        if not regions or method == "none":
            return MergingResult(
                merged_regions=[MergedRegion.from_single(r) for r in regions],
                method=method or "none",
                original_count=len(regions),
                merged_count=len(regions),
                params={},
            )

        if method == "overlap":
            return self._merge_overlap(
                regions, overlap_threshold, score_method,
                score_ratio_threshold, max_area
            )
        elif method == "proximity":
            return self._merge_proximity(
                regions, distance_threshold, score_method,
                score_ratio_threshold, max_area
            )
        elif method == "connected":
            return self._merge_connected(
                regions, overlap_threshold, distance_threshold, score_method,
                score_ratio_threshold, max_area
            )
        else:
            raise ValueError(f"Unknown merging method: {method}")

    def _should_merge(
        self,
        regions: List[RegionScore],
        i: int,
        j: int,
        score_ratio_threshold: float,
    ) -> bool:
        """Check if two regions should be merged based on score similarity."""
        if score_ratio_threshold <= 0:
            return True
        score_i, score_j = regions[i].score, regions[j].score
        if score_i == 0 or score_j == 0:
            return True
        ratio = min(score_i, score_j) / max(score_i, score_j)
        return ratio >= score_ratio_threshold

    def _would_exceed_max_area(
        self,
        regions: List[RegionScore],
        group_indices: List[int],
        new_idx: int,
        max_area: float,
    ) -> bool:
        """Check if adding new_idx to group would exceed max_area."""
        if max_area >= 1.0:
            return False
        group_regions = [regions[i] for i in group_indices] + [regions[new_idx]]
        return _merged_box_area(group_regions) > max_area

    def _merge_overlap(
        self,
        regions: List[RegionScore],
        overlap_threshold: float,
        score_method: str,
        score_ratio_threshold: float,
        max_area: float,
    ) -> MergingResult:
        """
        Merge regions that have overlapping bounding boxes.

        Uses union-find for transitive merging with score and area constraints.
        """
        n = len(regions)
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def get_group(x: int) -> List[int]:
            root = find(x)
            return [i for i in range(n) if find(i) == root]

        def union(x: int, y: int) -> bool:
            px, py = find(x), find(y)
            if px != py:
                # Check area constraint before merging
                group_x = get_group(x)
                group_y = get_group(y)
                combined = [regions[i] for i in group_x + group_y]
                if max_area < 1.0 and _merged_box_area(combined) > max_area:
                    return False
                parent[px] = py
                return True
            return False

        # Find overlapping pairs
        for i in range(n):
            for j in range(i + 1, n):
                iou = compute_iou(regions[i].bbox, regions[j].bbox)
                if iou > overlap_threshold:
                    if self._should_merge(regions, i, j, score_ratio_threshold):
                        union(i, j)

        # Group by component
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        # Create merged regions
        merged = []
        for indices in groups.values():
            group_regions = [regions[i] for i in indices]
            merged.append(MergedRegion.merge(group_regions, score_method))

        # Sort by score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        return MergingResult(
            merged_regions=merged,
            method="overlap",
            original_count=n,
            merged_count=len(merged),
            params={
                "overlap_threshold": overlap_threshold,
                "score_method": score_method,
                "score_ratio_threshold": score_ratio_threshold,
                "max_area": max_area,
            },
        )

    def _merge_proximity(
        self,
        regions: List[RegionScore],
        distance_threshold: float,
        score_method: str,
        score_ratio_threshold: float,
        max_area: float,
    ) -> MergingResult:
        """
        Merge regions within distance threshold.

        Distance is measured between closest edges of bounding boxes.
        Respects score similarity and max area constraints.
        """
        n = len(regions)
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def get_group(x: int) -> List[int]:
            root = find(x)
            return [i for i in range(n) if find(i) == root]

        def union(x: int, y: int) -> bool:
            px, py = find(x), find(y)
            if px != py:
                # Check area constraint before merging
                group_x = get_group(x)
                group_y = get_group(y)
                combined = [regions[i] for i in group_x + group_y]
                if max_area < 1.0 and _merged_box_area(combined) > max_area:
                    return False
                parent[px] = py
                return True
            return False

        # Find close pairs
        for i in range(n):
            for j in range(i + 1, n):
                dist = self._box_distance(regions[i].bbox, regions[j].bbox)
                if dist <= distance_threshold:
                    if self._should_merge(regions, i, j, score_ratio_threshold):
                        union(i, j)

        # Group by component
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        # Create merged regions
        merged = []
        for indices in groups.values():
            group_regions = [regions[i] for i in indices]
            merged.append(MergedRegion.merge(group_regions, score_method))

        # Sort by score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        return MergingResult(
            merged_regions=merged,
            method="proximity",
            original_count=n,
            merged_count=len(merged),
            params={
                "distance_threshold": distance_threshold,
                "score_method": score_method,
                "score_ratio_threshold": score_ratio_threshold,
                "max_area": max_area,
            },
        )

    def _merge_connected(
        self,
        regions: List[RegionScore],
        overlap_threshold: float,
        distance_threshold: float,
        score_method: str,
        score_ratio_threshold: float,
        max_area: float,
    ) -> MergingResult:
        """
        Merge regions using combined overlap and proximity criteria.

        Regions are merged if they either overlap OR are within distance threshold.
        Respects score similarity and max area constraints.
        """
        n = len(regions)
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def get_group(x: int) -> List[int]:
            root = find(x)
            return [i for i in range(n) if find(i) == root]

        def union(x: int, y: int) -> bool:
            px, py = find(x), find(y)
            if px != py:
                # Check area constraint before merging
                group_x = get_group(x)
                group_y = get_group(y)
                combined = [regions[i] for i in group_x + group_y]
                if max_area < 1.0 and _merged_box_area(combined) > max_area:
                    return False
                parent[px] = py
                return True
            return False

        # Find connected pairs (overlap OR proximity)
        for i in range(n):
            for j in range(i + 1, n):
                iou = compute_iou(regions[i].bbox, regions[j].bbox)
                dist = self._box_distance(regions[i].bbox, regions[j].bbox)

                if iou > overlap_threshold or dist <= distance_threshold:
                    if self._should_merge(regions, i, j, score_ratio_threshold):
                        union(i, j)

        # Group by component
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        # Create merged regions
        merged = []
        for indices in groups.values():
            group_regions = [regions[i] for i in indices]
            merged.append(MergedRegion.merge(group_regions, score_method))

        # Sort by score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        return MergingResult(
            merged_regions=merged,
            method="connected",
            original_count=n,
            merged_count=len(merged),
            params={
                "overlap_threshold": overlap_threshold,
                "distance_threshold": distance_threshold,
                "score_method": score_method,
                "score_ratio_threshold": score_ratio_threshold,
                "max_area": max_area,
            },
        )

    def _box_distance(self, box1: NormalizedBox, box2: NormalizedBox) -> float:
        """
        Compute minimum distance between two boxes.

        Returns 0 if boxes overlap, otherwise returns the minimum edge-to-edge distance.
        """
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Compute horizontal distance
        if x2_1 < x1_2:
            dx = x1_2 - x2_1  # box1 is to the left of box2
        elif x2_2 < x1_1:
            dx = x1_1 - x2_2  # box2 is to the left of box1
        else:
            dx = 0  # boxes overlap horizontally

        # Compute vertical distance
        if y2_1 < y1_2:
            dy = y1_2 - y2_1  # box1 is above box2
        elif y2_2 < y1_1:
            dy = y1_1 - y2_2  # box2 is above box1
        else:
            dy = 0  # boxes overlap vertically

        # If either distance is 0, boxes are adjacent or overlapping
        if dx == 0 and dy == 0:
            return 0.0

        # Return Euclidean distance for corner-to-corner case
        return float(np.sqrt(dx**2 + dy**2))


def merge_and_convert(
    regions: List[RegionScore],
    method: MergingMethod = "proximity",
    fallback_area_threshold: float = 0.0,
    **kwargs,
) -> List[RegionScore]:
    """
    Convenience function to merge regions and convert back to RegionScore list.

    Args:
        regions: List of RegionScore objects
        method: Merging method
        fallback_area_threshold: If top merged region exceeds this area fraction,
            return all original regions instead (0=disabled). Example: 0.5 means
            if merged result covers >50% of page, fall back to original regions.
        **kwargs: Additional arguments for RegionMerger.merge()

    Returns:
        List of RegionScore objects (merged, or original if fallback triggered)
    """
    if not regions:
        return []

    merger = RegionMerger()
    result = merger.merge(regions, method=method, **kwargs)
    merged = [mr.to_region_score() for mr in result.merged_regions]

    # Check if we should fall back to original regions
    if fallback_area_threshold > 0 and merged:
        top_region = merged[0]  # Already sorted by score desc
        top_area = _box_area(top_region.bbox)

        if top_area > fallback_area_threshold:
            logger.info(
                f"Merge fallback triggered: top region area {top_area:.2%} > "
                f"threshold {fallback_area_threshold:.0%}. Returning {len(regions)} original regions."
            )
            return regions

    return merged
