"""
Region filtering strategies for spatial grounding evaluation.

Implements multiple strategies for filtering OCR regions based on
relevance scores computed from ColPali patch similarities.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ScoredRegion:
    """A region with its computed relevance score."""

    bbox: List[int]  # [x1, y1, x2, y2]
    score: float
    content: str = ""
    label: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FilteringStrategy(ABC):
    """Abstract base class for region filtering strategies."""

    @abstractmethod
    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        """
        Filter regions based on the strategy.

        Args:
            scored_regions: List of regions with relevance scores

        Returns:
            Filtered list of regions
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name for logging/reporting."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class ThresholdFilter(FilteringStrategy):
    """Filter regions by a fixed score threshold."""

    def __init__(self, threshold: float = 0.3):
        """
        Args:
            threshold: Minimum score to include a region (0.0-1.0)
        """
        self.threshold = threshold

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        return [r for r in scored_regions if r.score >= self.threshold]

    @property
    def name(self) -> str:
        return f"threshold_{self.threshold}"

    def __repr__(self) -> str:
        return f"ThresholdFilter(threshold={self.threshold})"


class TopKFilter(FilteringStrategy):
    """Return the top-k highest-scoring regions."""

    def __init__(self, k: int = 5):
        """
        Args:
            k: Number of top regions to return
        """
        self.k = k

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        sorted_regions = sorted(scored_regions, key=lambda r: r.score, reverse=True)
        return sorted_regions[: self.k]

    @property
    def name(self) -> str:
        return f"top_{self.k}"

    def __repr__(self) -> str:
        return f"TopKFilter(k={self.k})"


class AdaptiveFilter(FilteringStrategy):
    """Filter using statistical properties of the score distribution."""

    def __init__(self, z_threshold: float = 1.0):
        """
        Args:
            z_threshold: Number of standard deviations above mean for cutoff
        """
        self.z_threshold = z_threshold

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        if not scored_regions:
            return []

        scores = np.array([r.score for r in scored_regions])
        mean_score = scores.mean()
        std_score = scores.std()

        threshold = mean_score + self.z_threshold * std_score
        return [r for r in scored_regions if r.score >= threshold]

    @property
    def name(self) -> str:
        return f"adaptive_z{self.z_threshold}"

    def __repr__(self) -> str:
        return f"AdaptiveFilter(z_threshold={self.z_threshold})"


class KneeFilter(FilteringStrategy):
    """
    Use the elbow/knee method to find natural score cutoff.

    Identifies the point of maximum curvature in the sorted score curve.
    """

    def __init__(self, min_regions: int = 1):
        """
        Args:
            min_regions: Minimum number of regions to return
        """
        self.min_regions = min_regions

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        if len(scored_regions) <= self.min_regions:
            return scored_regions

        # Sort by score descending
        sorted_regions = sorted(scored_regions, key=lambda r: r.score, reverse=True)
        sorted_scores = [r.score for r in sorted_regions]
        n = len(sorted_scores)

        # Vector from first to last point
        p1 = np.array([0, sorted_scores[0]])
        p2 = np.array([n - 1, sorted_scores[-1]])

        # Handle case where all scores are equal
        if np.allclose(p1, p2):
            return sorted_regions[: self.min_regions]

        # Find point with maximum perpendicular distance
        max_dist = 0
        knee_idx = 0
        line_vec = p2 - p1
        line_len = np.linalg.norm(line_vec)

        for i, s in enumerate(sorted_scores):
            point = np.array([i, s])
            dist = np.abs(np.cross(line_vec, p1 - point)) / line_len
            if dist > max_dist:
                max_dist = dist
                knee_idx = i

        # Return all regions up to and including the knee point
        knee_idx = max(knee_idx, self.min_regions - 1)
        threshold = sorted_scores[knee_idx]

        return [r for r in scored_regions if r.score >= threshold]

    @property
    def name(self) -> str:
        return f"knee_min{self.min_regions}"

    def __repr__(self) -> str:
        return f"KneeFilter(min_regions={self.min_regions})"


class CombinedFilter(FilteringStrategy):
    """Apply multiple filters and return intersection/union."""

    def __init__(
        self,
        filters: List[FilteringStrategy],
        mode: str = "intersection",
    ):
        """
        Args:
            filters: List of filtering strategies to combine
            mode: 'intersection' (all must pass) or 'union' (any passes)
        """
        self.filters = filters
        self.mode = mode

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        if not self.filters:
            return scored_regions

        if self.mode == "intersection":
            # Start with all regions, intersect with each filter's output
            result_bboxes = {tuple(r.bbox) for r in scored_regions}
            for f in self.filters:
                filtered = f.filter(scored_regions)
                result_bboxes &= {tuple(r.bbox) for r in filtered}
            return [r for r in scored_regions if tuple(r.bbox) in result_bboxes]

        elif self.mode == "union":
            # Union all filter outputs
            result_bboxes = set()
            for f in self.filters:
                filtered = f.filter(scored_regions)
                result_bboxes |= {tuple(r.bbox) for r in filtered}
            return [r for r in scored_regions if tuple(r.bbox) in result_bboxes]

        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    @property
    def name(self) -> str:
        filter_names = "+".join(f.name for f in self.filters)
        return f"combined_{self.mode}_{filter_names}"

    def __repr__(self) -> str:
        return f"CombinedFilter(filters={self.filters}, mode={self.mode})"


class PercentileFilter(FilteringStrategy):
    """Filter regions scoring above a certain percentile."""

    def __init__(self, percentile: float = 75.0):
        """
        Args:
            percentile: Keep regions above this percentile (0-100)
        """
        self.percentile = percentile

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        if not scored_regions:
            return []

        scores = [r.score for r in scored_regions]
        threshold = np.percentile(scores, self.percentile)
        return [r for r in scored_regions if r.score >= threshold]

    @property
    def name(self) -> str:
        return f"percentile_{self.percentile}"

    def __repr__(self) -> str:
        return f"PercentileFilter(percentile={self.percentile})"


class AllRegionsFilter(FilteringStrategy):
    """Return all regions without filtering.

    This strategy is NOT recommended for production use as it defeats the purpose
    of spatial grounding. It's included only for baseline comparison in benchmarks.
    """

    def filter(self, scored_regions: List[ScoredRegion]) -> List[ScoredRegion]:
        return scored_regions

    @property
    def name(self) -> str:
        return "all"

    def __repr__(self) -> str:
        return "AllRegionsFilter()"


# Strategy presets for evaluation
# These strategies filter regions based on ColPali query relevance scores
STRATEGY_PRESETS = {
    # Threshold-based strategies (Snappy default: 0.3)
    "threshold_0.1": ThresholdFilter(threshold=0.1),
    "threshold_0.2": ThresholdFilter(threshold=0.2),
    "threshold_0.3": ThresholdFilter(threshold=0.3),  # Snappy default
    "threshold_0.4": ThresholdFilter(threshold=0.4),
    "threshold_0.5": ThresholdFilter(threshold=0.5),
    "balanced": ThresholdFilter(threshold=0.3),  # Alias for default
}


def get_strategy(name: str = "balanced") -> FilteringStrategy:
    """
    Get a filtering strategy by name.

    Args:
        name: Strategy name (default: "balanced" = threshold 0.3, matching Snappy config)

    Returns:
        FilteringStrategy instance
    """
    if name in STRATEGY_PRESETS:
        return STRATEGY_PRESETS[name]

    # Parse custom threshold format: "threshold_X.Y"
    if name.startswith("threshold_"):
        try:
            threshold = float(name.split("_")[1])
            return ThresholdFilter(threshold=threshold)
        except (IndexError, ValueError):
            pass

    # Parse custom top-k format: "topX"
    if name.startswith("top"):
        try:
            k = int(name[3:])
            return TopKFilter(k=k)
        except ValueError:
            pass

    # Default to balanced strategy (threshold 0.3)
    logger.warning(f"Unknown strategy '{name}', using default 'balanced'")
    return STRATEGY_PRESETS["balanced"]
