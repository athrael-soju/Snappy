"""
Retrieval evaluation metrics for benchmarking.

Evaluates retrieval quality by comparing retrieved regions against ground truth bboxes.
This isolates retrieval performance from LLM reasoning ability.

Metrics:
- IoU (Intersection over Union): Overlap between retrieved and ground truth regions
- Hit Rate: % of ground truth bboxes with at least one overlapping retrieval
- Precision: % of retrieved regions that overlap with ground truth
- Recall: % of ground truth area covered by retrieved regions
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Retrieval quality metrics for a single sample."""

    # Per-sample metrics
    mean_max_iou: float = 0.0  # Average of max IoU for each ground truth bbox
    hit_rate: float = 0.0  # % of GT bboxes with IoU > threshold
    precision: float = 0.0  # % of retrieved regions overlapping any GT bbox
    recall: float = 0.0  # % of GT bboxes covered by any retrieval

    # Counts
    num_gt_bboxes: int = 0
    num_retrieved_regions: int = 0
    num_hits: int = 0  # GT bboxes with at least one match

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_max_iou": self.mean_max_iou,
            "hit_rate": self.hit_rate,
            "precision": self.precision,
            "recall": self.recall,
            "num_gt_bboxes": self.num_gt_bboxes,
            "num_retrieved_regions": self.num_retrieved_regions,
            "num_hits": self.num_hits,
        }


def compute_iou(bbox1: List[int], bbox2: List[int]) -> float:
    """
    Compute Intersection over Union between two bboxes.

    Args:
        bbox1: [x1, y1, x2, y2] format
        bbox2: [x1, y1, x2, y2] format

    Returns:
        IoU value between 0 and 1
    """
    # Unpack coordinates
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # Compute intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    # Check for no intersection
    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Compute union
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def _flatten_bboxes(bboxes: List) -> List[List[int]]:
    """
    Flatten nested bbox structure to list of [x1, y1, x2, y2].

    Dataset format can be:
    - [[[x1, y1, x2, y2]]] - single bbox, single page
    - [[[bbox1], [bbox2]]] - multiple bboxes, single page
    - [[[bbox1]], [[bbox2]]] - bboxes across multiple pages

    Returns:
        Flat list of [x1, y1, x2, y2] bboxes
    """
    flat = []
    for item in bboxes:
        if isinstance(item, list):
            if len(item) == 4 and all(isinstance(x, (int, float)) for x in item):
                # This is a bbox [x1, y1, x2, y2]
                flat.append(item)
            else:
                # Nested list, recurse
                flat.extend(_flatten_bboxes(item))
    return flat


def compute_retrieval_metrics(
    retrieved_regions: List[Dict[str, Any]],
    ground_truth_bboxes: List,
    iou_threshold: float = 0.1,
) -> RetrievalMetrics:
    """
    Compute retrieval quality metrics comparing retrieved regions to ground truth.

    Args:
        retrieved_regions: List of region dicts with 'bbox' key ([x1, y1, x2, y2])
        ground_truth_bboxes: Ground truth bboxes (possibly nested, will be flattened)
        iou_threshold: IoU threshold for considering a region as a "hit"

    Returns:
        RetrievalMetrics with computed values
    """
    metrics = RetrievalMetrics()

    # Flatten nested bbox structure
    flat_gt_bboxes = _flatten_bboxes(ground_truth_bboxes) if ground_truth_bboxes else []

    # Log ground truth bboxes
    logger.info(f"Ground truth bboxes ({len(flat_gt_bboxes)}):")
    for i, bbox in enumerate(flat_gt_bboxes):
        logger.info(f"  GT[{i}]: {bbox}")

    # Handle edge cases
    if not flat_gt_bboxes:
        # No ground truth - can't evaluate
        metrics.num_retrieved_regions = len(retrieved_regions) if retrieved_regions else 0
        logger.warning("No ground truth bboxes to compare against")
        return metrics

    metrics.num_gt_bboxes = len(flat_gt_bboxes)
    metrics.num_retrieved_regions = len(retrieved_regions) if retrieved_regions else 0

    if not retrieved_regions:
        # No retrievals - all metrics are 0
        logger.warning("No retrieved regions to compare")
        return metrics

    # Extract bboxes from retrieved regions
    retrieved_bboxes = []
    logger.info(f"Retrieved regions ({len(retrieved_regions)}):")
    for idx, region in enumerate(retrieved_regions):
        bbox = region.get("bbox")
        label = region.get("label", "unknown")
        if bbox and len(bbox) == 4:
            retrieved_bboxes.append(bbox)
            logger.info(f"  RET[{idx}] [{label}]: {bbox}")
        else:
            logger.info(f"  RET[{idx}] [{label}]: invalid bbox={bbox}")

    if not retrieved_bboxes:
        logger.warning("No valid bboxes in retrieved regions")
        return metrics

    # Compute IoU matrix: [num_gt x num_retrieved]
    iou_matrix = np.zeros((len(flat_gt_bboxes), len(retrieved_bboxes)))
    for i, gt_bbox in enumerate(flat_gt_bboxes):
        for j, ret_bbox in enumerate(retrieved_bboxes):
            iou_matrix[i, j] = compute_iou(gt_bbox, ret_bbox)

    # Log IoU comparisons
    logger.info("IoU matrix (GT rows x Retrieved cols):")
    for i, gt_bbox in enumerate(flat_gt_bboxes):
        best_j = int(np.argmax(iou_matrix[i]))
        best_iou = iou_matrix[i, best_j]
        logger.info(f"  GT[{i}] best match: RET[{best_j}] IoU={best_iou:.3f}")

    # Mean Max IoU: For each GT bbox, find the max IoU with any retrieved region
    max_ious_per_gt = iou_matrix.max(axis=1)
    metrics.mean_max_iou = float(np.mean(max_ious_per_gt))

    # Hit Rate: % of GT bboxes with at least one retrieval above threshold
    hits = max_ious_per_gt >= iou_threshold
    metrics.num_hits = int(np.sum(hits))
    metrics.hit_rate = metrics.num_hits / len(flat_gt_bboxes)

    # Recall: Same as hit rate in this context (% of GT bboxes covered)
    metrics.recall = metrics.hit_rate

    # Precision: % of retrieved regions that overlap with any GT bbox
    max_ious_per_retrieved = iou_matrix.max(axis=0)
    retrieved_hits = max_ious_per_retrieved >= iou_threshold
    metrics.precision = float(np.mean(retrieved_hits))

    # Log summary
    logger.info(
        f"Retrieval metrics: mean_max_iou={metrics.mean_max_iou:.3f}, "
        f"hit_rate={metrics.hit_rate:.2%}, precision={metrics.precision:.2%}"
    )

    return metrics


def aggregate_retrieval_metrics(
    metrics_list: List[RetrievalMetrics],
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate retrieval metrics across multiple samples.

    Args:
        metrics_list: List of RetrievalMetrics from individual samples

    Returns:
        Dictionary with aggregated statistics
    """
    if not metrics_list:
        return {}

    # Filter to samples with ground truth
    valid_metrics = [m for m in metrics_list if m.num_gt_bboxes > 0]
    if not valid_metrics:
        return {}

    def aggregate_values(values: List[float]) -> Dict[str, float]:
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
        }

    return {
        "mean_max_iou": aggregate_values([m.mean_max_iou for m in valid_metrics]),
        "hit_rate": aggregate_values([m.hit_rate for m in valid_metrics]),
        "precision": aggregate_values([m.precision for m in valid_metrics]),
        "recall": aggregate_values([m.recall for m in valid_metrics]),
        "totals": {
            "samples_with_gt": len(valid_metrics),
            "total_gt_bboxes": sum(m.num_gt_bboxes for m in valid_metrics),
            "total_retrieved": sum(m.num_retrieved_regions for m in valid_metrics),
            "total_hits": sum(m.num_hits for m in valid_metrics),
        },
    }
