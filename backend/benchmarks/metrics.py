"""
Evaluation metrics for spatial grounding benchmarks.

Implements IoU-based metrics for comparing predicted bounding boxes
against ground truth annotations from BBox-DocVQA.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IoUMetrics:
    """Container for IoU-based evaluation metrics."""

    mean_iou: float = 0.0
    iou_at_50: float = 0.0  # % predictions with IoU >= 0.5
    iou_at_70: float = 0.0  # % predictions with IoU >= 0.7
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    num_predictions: int = 0
    num_ground_truth: int = 0
    context_reduction: float = 0.0  # % of page area filtered out

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "mean_iou": self.mean_iou,
            "iou@0.5": self.iou_at_50,
            "iou@0.7": self.iou_at_70,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "num_predictions": self.num_predictions,
            "num_ground_truth": self.num_ground_truth,
            "context_reduction": self.context_reduction,
        }


@dataclass
class BenchmarkResults:
    """Aggregated benchmark results across all samples."""

    overall: IoUMetrics = field(default_factory=IoUMetrics)
    by_instance_type: Dict[str, IoUMetrics] = field(default_factory=dict)
    by_subimg_type: Dict[str, IoUMetrics] = field(default_factory=dict)
    by_category: Dict[str, IoUMetrics] = field(default_factory=dict)
    per_sample_ious: List[float] = field(default_factory=list)
    total_samples: int = 0
    failed_samples: int = 0

    def to_dict(self) -> Dict:
        """Convert results to dictionary for serialization."""
        return {
            "overall": self.overall.to_dict(),
            "by_instance_type": {k: v.to_dict() for k, v in self.by_instance_type.items()},
            "by_subimg_type": {k: v.to_dict() for k, v in self.by_subimg_type.items()},
            "by_category": {k: v.to_dict() for k, v in self.by_category.items()},
            "total_samples": self.total_samples,
            "failed_samples": self.failed_samples,
        }


def compute_iou(
    pred_bbox: List[int], gt_bbox: List[int]
) -> float:
    """
    Compute Intersection over Union between two bounding boxes.

    Args:
        pred_bbox: Predicted bbox as [x_min, y_min, x_max, y_max]
        gt_bbox: Ground truth bbox as [x_min, y_min, x_max, y_max]

    Returns:
        IoU score in [0, 1]
    """
    # Intersection coordinates
    xi1 = max(pred_bbox[0], gt_bbox[0])
    yi1 = max(pred_bbox[1], gt_bbox[1])
    xi2 = min(pred_bbox[2], gt_bbox[2])
    yi2 = min(pred_bbox[3], gt_bbox[3])

    # Intersection area
    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    intersection = inter_width * inter_height

    # Union area
    area_pred = (pred_bbox[2] - pred_bbox[0]) * (pred_bbox[3] - pred_bbox[1])
    area_gt = (gt_bbox[2] - gt_bbox[0]) * (gt_bbox[3] - gt_bbox[1])
    union = area_pred + area_gt - intersection

    return intersection / union if union > 0 else 0.0


def compute_intersection_area(bbox1: List[int], bbox2: List[int]) -> float:
    """Compute intersection area between two bounding boxes."""
    xi1 = max(bbox1[0], bbox2[0])
    yi1 = max(bbox1[1], bbox2[1])
    xi2 = min(bbox1[2], bbox2[2])
    yi2 = min(bbox1[3], bbox2[3])

    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    return inter_width * inter_height


def evaluate_multi_region(
    pred_bboxes: List[List[int]],
    gt_bboxes: List[List[int]],
    iou_threshold: float = 0.5,
) -> IoUMetrics:
    """
    Evaluate predicted regions against ground truth using set-based matching.

    Uses greedy matching: each prediction is matched to its best GT bbox
    that hasn't been matched yet.

    Args:
        pred_bboxes: List of predicted bboxes
        gt_bboxes: List of ground truth bboxes
        iou_threshold: Minimum IoU to consider a match

    Returns:
        IoUMetrics with precision, recall, F1, and IoU statistics
    """
    if not gt_bboxes:
        return IoUMetrics(num_predictions=len(pred_bboxes))

    if not pred_bboxes:
        return IoUMetrics(num_ground_truth=len(gt_bboxes))

    # Compute all pairwise IoUs
    iou_matrix = np.zeros((len(pred_bboxes), len(gt_bboxes)))
    for i, pred in enumerate(pred_bboxes):
        for j, gt in enumerate(gt_bboxes):
            iou_matrix[i, j] = compute_iou(pred, gt)

    # Greedy matching
    matched_gt = set()
    matched_pred = set()
    matches: List[Tuple[int, int, float]] = []

    # Sort all (pred_idx, gt_idx, iou) by IoU descending
    all_pairs = [
        (i, j, iou_matrix[i, j])
        for i in range(len(pred_bboxes))
        for j in range(len(gt_bboxes))
    ]
    all_pairs.sort(key=lambda x: x[2], reverse=True)

    for pred_idx, gt_idx, iou in all_pairs:
        if pred_idx in matched_pred or gt_idx in matched_gt:
            continue
        if iou >= iou_threshold:
            matches.append((pred_idx, gt_idx, iou))
            matched_pred.add(pred_idx)
            matched_gt.add(gt_idx)

    # Compute metrics
    true_positives = len(matches)
    precision = true_positives / len(pred_bboxes) if pred_bboxes else 0.0
    recall = true_positives / len(gt_bboxes) if gt_bboxes else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Compute IoU statistics - always compute based on best IoU per prediction
    # (regardless of whether any matched the threshold)
    if pred_bboxes and gt_bboxes:
        all_ious = []
        for i, pred in enumerate(pred_bboxes):
            best_iou = max(iou_matrix[i, :])
            all_ious.append(best_iou)
        mean_iou = float(np.mean(all_ious))
        iou_at_50 = sum(1 for iou in all_ious if iou >= 0.5) / len(all_ious)
        iou_at_70 = sum(1 for iou in all_ious if iou >= 0.7) / len(all_ious)
    else:
        mean_iou = 0.0
        iou_at_50 = 0.0
        iou_at_70 = 0.0

    return IoUMetrics(
        mean_iou=mean_iou,
        iou_at_50=iou_at_50,
        iou_at_70=iou_at_70,
        precision=precision,
        recall=recall,
        f1=f1,
        num_predictions=len(pred_bboxes),
        num_ground_truth=len(gt_bboxes),
    )


def compute_recall_at_k(
    pred_bboxes: List[List[int]],
    gt_bboxes: List[List[int]],
    k: int,
    iou_threshold: float = 0.5,
) -> float:
    """
    Compute recall@k: fraction of GT regions matched by top-k predictions.

    Args:
        pred_bboxes: List of predicted bboxes (assumed sorted by score)
        gt_bboxes: List of ground truth bboxes
        k: Number of top predictions to consider
        iou_threshold: Minimum IoU for a match

    Returns:
        Recall@k score
    """
    if not gt_bboxes:
        return 1.0
    if not pred_bboxes:
        return 0.0

    top_k_preds = pred_bboxes[:k]
    matched_gt = set()

    for pred in top_k_preds:
        for gt_idx, gt in enumerate(gt_bboxes):
            if gt_idx in matched_gt:
                continue
            if compute_iou(pred, gt) >= iou_threshold:
                matched_gt.add(gt_idx)
                break

    return len(matched_gt) / len(gt_bboxes)


def compute_context_reduction(
    pred_bboxes: List[List[int]],
    page_width: int,
    page_height: int,
) -> float:
    """
    Compute context reduction: 1 - (filtered_area / page_area).

    Args:
        pred_bboxes: List of predicted bboxes to keep
        page_width: Page width in pixels
        page_height: Page height in pixels

    Returns:
        Context reduction ratio (0 = no reduction, 1 = all filtered)
    """
    page_area = page_width * page_height
    if page_area == 0:
        return 0.0

    # Sum areas of predicted regions (may overlap, so this is an upper bound)
    total_pred_area = sum(
        (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        for bbox in pred_bboxes
    )

    return 1.0 - min(1.0, total_pred_area / page_area)


def aggregate_metrics(
    all_metrics: List[IoUMetrics],
    weights: Optional[List[float]] = None,
) -> IoUMetrics:
    """
    Aggregate multiple IoUMetrics into a single summary.

    Args:
        all_metrics: List of per-sample metrics
        weights: Optional weights for weighted average

    Returns:
        Aggregated metrics
    """
    if not all_metrics:
        return IoUMetrics()

    if weights is None:
        weights = [1.0] * len(all_metrics)

    total_weight = sum(weights)
    if total_weight == 0:
        return IoUMetrics()

    return IoUMetrics(
        mean_iou=sum(m.mean_iou * w for m, w in zip(all_metrics, weights)) / total_weight,
        iou_at_50=sum(m.iou_at_50 * w for m, w in zip(all_metrics, weights)) / total_weight,
        iou_at_70=sum(m.iou_at_70 * w for m, w in zip(all_metrics, weights)) / total_weight,
        precision=sum(m.precision * w for m, w in zip(all_metrics, weights)) / total_weight,
        recall=sum(m.recall * w for m, w in zip(all_metrics, weights)) / total_weight,
        f1=sum(m.f1 * w for m, w in zip(all_metrics, weights)) / total_weight,
        num_predictions=sum(m.num_predictions for m in all_metrics),
        num_ground_truth=sum(m.num_ground_truth for m in all_metrics),
        context_reduction=sum(m.context_reduction * w for m, w in zip(all_metrics, weights)) / total_weight,
    )


def compute_best_match_iou(
    pred_bboxes: List[List[int]],
    gt_bboxes: List[List[int]],
) -> float:
    """
    Compute the best IoU across all prediction-GT pairs.

    Useful for samples where any overlap is considered a success.

    Args:
        pred_bboxes: List of predicted bboxes
        gt_bboxes: List of ground truth bboxes

    Returns:
        Maximum IoU across all pairs
    """
    if not pred_bboxes or not gt_bboxes:
        return 0.0

    best_iou = 0.0
    for pred in pred_bboxes:
        for gt in gt_bboxes:
            iou = compute_iou(pred, gt)
            best_iou = max(best_iou, iou)

    return best_iou
