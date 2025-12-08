"""
Evaluation Metrics and Matching Strategies.

This module provides metrics and matching strategies for evaluating
predicted bounding boxes against ground truth.

Metrics:
- IoU@threshold: Hit rates at overlap thresholds
- Mean IoU: Average overlap
- Precision@K, Recall@K: Top-K performance
- mAP: Mean average precision

Matching strategies:
- any_match: Any pred-GT pair exceeds threshold (lenient)
- set_coverage: Count GT boxes covered by any prediction
- hungarian: Optimal 1:1 bipartite matching
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from .utils.coordinates import Box, compute_iou, compute_iou_matrix


class MatchingStrategy(str, Enum):
    """Matching strategies for prediction-GT comparison."""

    ANY_MATCH = "any_match"
    SET_COVERAGE = "set_coverage"
    HUNGARIAN = "hungarian"


@dataclass
class EvaluationResult:
    """Results from evaluation on a single sample."""

    sample_id: str
    num_predictions: int
    num_ground_truth: int
    iou_matrix: NDArray[np.float64]
    matched_pairs: List[Tuple[int, int, float]]  # (pred_idx, gt_idx, iou)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_id": self.sample_id,
            "num_predictions": self.num_predictions,
            "num_ground_truth": self.num_ground_truth,
            "matched_pairs": self.matched_pairs,
            "metrics": self.metrics,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across multiple samples."""

    num_samples: int
    total_predictions: int
    total_ground_truth: int
    metrics: Dict[str, float] = field(default_factory=dict)
    per_sample_results: List[EvaluationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "num_samples": self.num_samples,
            "total_predictions": self.total_predictions,
            "total_ground_truth": self.total_ground_truth,
            "metrics": self.metrics,
        }


def match_any(
    iou_matrix: NDArray[np.float64],
    threshold: float,
) -> List[Tuple[int, int, float]]:
    """
    Any-match strategy: Find all pred-GT pairs exceeding threshold.

    This is the most lenient matching strategy. A prediction or GT
    box can be matched to multiple counterparts.

    Args:
        iou_matrix: IoU matrix of shape (n_predictions, n_ground_truth)
        threshold: Minimum IoU threshold

    Returns:
        List of (pred_idx, gt_idx, iou) tuples for matches
    """
    matches = []
    n_pred, n_gt = iou_matrix.shape

    for i in range(n_pred):
        for j in range(n_gt):
            if iou_matrix[i, j] >= threshold:
                matches.append((i, j, float(iou_matrix[i, j])))

    return matches


def match_set_coverage(
    iou_matrix: NDArray[np.float64],
    threshold: float,
) -> List[Tuple[int, int, float]]:
    """
    Set coverage strategy: Each GT box matched to best prediction.

    For each GT box, find the prediction with highest IoU >= threshold.
    Multiple predictions can match the same GT (if they both exceed threshold),
    but we track only the best match per GT for counting coverage.

    Args:
        iou_matrix: IoU matrix of shape (n_predictions, n_ground_truth)
        threshold: Minimum IoU threshold

    Returns:
        List of (pred_idx, gt_idx, iou) tuples for best matches
    """
    matches = []
    n_pred, n_gt = iou_matrix.shape

    if n_pred == 0 or n_gt == 0:
        return matches

    for j in range(n_gt):
        col = iou_matrix[:, j]
        best_pred = np.argmax(col)
        best_iou = col[best_pred]

        if best_iou >= threshold:
            matches.append((int(best_pred), j, float(best_iou)))

    return matches


def match_hungarian(
    iou_matrix: NDArray[np.float64],
    threshold: float,
) -> List[Tuple[int, int, float]]:
    """
    Hungarian matching: Optimal 1:1 bipartite matching.

    Uses the Hungarian algorithm (linear sum assignment) to find
    the optimal 1:1 matching that maximizes total IoU.

    Args:
        iou_matrix: IoU matrix of shape (n_predictions, n_ground_truth)
        threshold: Minimum IoU threshold

    Returns:
        List of (pred_idx, gt_idx, iou) tuples for optimal matches
    """
    from scipy.optimize import linear_sum_assignment

    n_pred, n_gt = iou_matrix.shape

    if n_pred == 0 or n_gt == 0:
        return []

    # Convert to cost matrix (negate IoU for minimization)
    cost_matrix = -iou_matrix

    # Solve assignment problem
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Filter by threshold
    matches = []
    for i, j in zip(row_ind, col_ind):
        iou = iou_matrix[i, j]
        if iou >= threshold:
            matches.append((int(i), int(j), float(iou)))

    return matches


def match_predictions(
    predictions: List[Box],
    ground_truth: List[Box],
    strategy: MatchingStrategy,
    threshold: float = 0.5,
) -> Tuple[NDArray[np.float64], List[Tuple[int, int, float]]]:
    """
    Match predictions to ground truth using specified strategy.

    Args:
        predictions: List of predicted boxes
        ground_truth: List of ground truth boxes
        strategy: Matching strategy to use
        threshold: Minimum IoU threshold

    Returns:
        Tuple of (iou_matrix, matched_pairs)
    """
    if not predictions or not ground_truth:
        return np.zeros((len(predictions), len(ground_truth))), []

    iou_matrix = compute_iou_matrix(predictions, ground_truth)

    matchers = {
        MatchingStrategy.ANY_MATCH: match_any,
        MatchingStrategy.SET_COVERAGE: match_set_coverage,
        MatchingStrategy.HUNGARIAN: match_hungarian,
    }

    matcher = matchers.get(strategy)
    if matcher is None:
        raise ValueError(f"Unknown matching strategy: {strategy}")

    matches = matcher(iou_matrix, threshold)
    return iou_matrix, matches


def compute_iou_at_threshold(
    matched_pairs: List[Tuple[int, int, float]],
    num_ground_truth: int,
    threshold: float,
) -> float:
    """
    Compute hit rate at IoU threshold.

    Args:
        matched_pairs: List of (pred_idx, gt_idx, iou) tuples
        num_ground_truth: Total number of ground truth boxes
        threshold: IoU threshold (for filtering matches)

    Returns:
        Hit rate (fraction of GT boxes with IoU >= threshold)
    """
    if num_ground_truth == 0:
        return 0.0

    # Count unique GT boxes matched at threshold
    matched_gt = set()
    for _, gt_idx, iou in matched_pairs:
        if iou >= threshold:
            matched_gt.add(gt_idx)

    return len(matched_gt) / num_ground_truth


def compute_mean_iou(
    iou_matrix: NDArray[np.float64],
    matched_pairs: List[Tuple[int, int, float]],
) -> float:
    """
    Compute mean IoU across matched pairs.

    Args:
        iou_matrix: Full IoU matrix
        matched_pairs: List of matched (pred_idx, gt_idx, iou) tuples

    Returns:
        Mean IoU of matched pairs (or 0 if no matches)
    """
    if not matched_pairs:
        return 0.0

    ious = [iou for _, _, iou in matched_pairs]
    return float(np.mean(ious))


def compute_precision_at_k(
    predictions: List[Box],
    ground_truth: List[Box],
    k: int,
    threshold: float = 0.5,
) -> float:
    """
    Compute Precision@K.

    Args:
        predictions: List of predicted boxes (should be sorted by score)
        ground_truth: List of ground truth boxes
        k: Number of top predictions to consider
        threshold: IoU threshold for correct prediction

    Returns:
        Precision@K value
    """
    if k <= 0 or not predictions or not ground_truth:
        return 0.0

    top_k = predictions[:k]
    iou_matrix = compute_iou_matrix(top_k, ground_truth)

    # Count predictions that match any GT
    correct = 0
    for i in range(len(top_k)):
        if np.max(iou_matrix[i]) >= threshold:
            correct += 1

    return correct / k


def compute_recall_at_k(
    predictions: List[Box],
    ground_truth: List[Box],
    k: int,
    threshold: float = 0.5,
) -> float:
    """
    Compute Recall@K.

    Args:
        predictions: List of predicted boxes (should be sorted by score)
        ground_truth: List of ground truth boxes
        k: Number of top predictions to consider
        threshold: IoU threshold for correct prediction

    Returns:
        Recall@K value
    """
    if k <= 0 or not predictions or not ground_truth:
        return 0.0

    top_k = predictions[:k]
    iou_matrix = compute_iou_matrix(top_k, ground_truth)

    # Count GT boxes matched by any prediction
    matched_gt = set()
    for j in range(len(ground_truth)):
        if np.max(iou_matrix[:, j]) >= threshold:
            matched_gt.add(j)

    return len(matched_gt) / len(ground_truth)


def compute_average_precision(
    predictions: List[Box],
    scores: List[float],
    ground_truth: List[Box],
    threshold: float = 0.5,
) -> float:
    """
    Compute Average Precision (AP) at IoU threshold.

    Args:
        predictions: List of predicted boxes
        scores: List of prediction scores (same order as predictions)
        ground_truth: List of ground truth boxes
        threshold: IoU threshold for correct prediction

    Returns:
        Average precision value
    """
    if not predictions or not ground_truth:
        return 0.0

    # Sort by scores descending
    sorted_indices = np.argsort(scores)[::-1]
    sorted_preds = [predictions[i] for i in sorted_indices]

    iou_matrix = compute_iou_matrix(sorted_preds, ground_truth)

    # Track which GT boxes have been matched
    matched_gt = set()
    precisions = []
    recalls = []
    tp = 0

    for i, pred_idx in enumerate(range(len(sorted_preds))):
        # Find best matching GT for this prediction
        best_gt = -1
        best_iou = threshold

        for j in range(len(ground_truth)):
            if j not in matched_gt and iou_matrix[pred_idx, j] >= best_iou:
                best_iou = iou_matrix[pred_idx, j]
                best_gt = j

        if best_gt >= 0:
            tp += 1
            matched_gt.add(best_gt)

        precision = tp / (i + 1)
        recall = tp / len(ground_truth)

        precisions.append(precision)
        recalls.append(recall)

    # Compute AP as area under precision-recall curve
    if not precisions:
        return 0.0

    # Use 11-point interpolation
    ap = 0.0
    for r_threshold in np.arange(0, 1.1, 0.1):
        precisions_at_recall = [
            p for p, r in zip(precisions, recalls) if r >= r_threshold
        ]
        if precisions_at_recall:
            ap += max(precisions_at_recall)

    return ap / 11


def evaluate_sample(
    predictions: List[Box],
    ground_truth: List[Box],
    sample_id: str,
    strategy: MatchingStrategy = MatchingStrategy.SET_COVERAGE,
    iou_thresholds: List[float] = [0.25, 0.5, 0.75],
    scores: Optional[List[float]] = None,
) -> EvaluationResult:
    """
    Evaluate predictions against ground truth for a single sample.

    Args:
        predictions: List of predicted boxes
        ground_truth: List of ground truth boxes
        sample_id: Sample identifier
        strategy: Matching strategy
        iou_thresholds: IoU thresholds for hit rate metrics
        scores: Optional prediction scores for AP computation

    Returns:
        EvaluationResult with computed metrics
    """
    # Compute IoU matrix and matches
    iou_matrix, matched_pairs = match_predictions(
        predictions,
        ground_truth,
        strategy,
        threshold=min(iou_thresholds) if iou_thresholds else 0.5,
    )

    metrics = {}

    # IoU@threshold hit rates
    for t in iou_thresholds:
        # Re-match at this threshold for accurate counting
        _, matches_at_t = match_predictions(
            predictions, ground_truth, strategy, threshold=t
        )
        metrics[f"iou@{t}"] = compute_iou_at_threshold(
            matches_at_t, len(ground_truth), t
        )

    # Mean IoU
    metrics["mean_iou"] = compute_mean_iou(iou_matrix, matched_pairs)

    # Precision and Recall at K
    for k in [1, 3, 5, 10]:
        if len(predictions) >= k:
            metrics[f"precision@{k}"] = compute_precision_at_k(
                predictions, ground_truth, k
            )
            metrics[f"recall@{k}"] = compute_recall_at_k(
                predictions, ground_truth, k
            )

    # Average precision
    if scores is not None:
        for t in iou_thresholds:
            metrics[f"ap@{t}"] = compute_average_precision(
                predictions, scores, ground_truth, t
            )

    return EvaluationResult(
        sample_id=sample_id,
        num_predictions=len(predictions),
        num_ground_truth=len(ground_truth),
        iou_matrix=iou_matrix,
        matched_pairs=matched_pairs,
        metrics=metrics,
    )


def aggregate_results(
    results: List[EvaluationResult],
) -> AggregatedMetrics:
    """
    Aggregate evaluation results across multiple samples.

    Args:
        results: List of per-sample evaluation results

    Returns:
        AggregatedMetrics with mean values across samples
    """
    if not results:
        return AggregatedMetrics(
            num_samples=0,
            total_predictions=0,
            total_ground_truth=0,
        )

    # Collect all metrics
    metric_values: Dict[str, List[float]] = {}
    for r in results:
        for name, value in r.metrics.items():
            if name not in metric_values:
                metric_values[name] = []
            metric_values[name].append(value)

    # Compute means
    aggregated_metrics = {}
    for name, values in metric_values.items():
        aggregated_metrics[f"mean_{name}"] = float(np.mean(values))
        aggregated_metrics[f"std_{name}"] = float(np.std(values))

    total_preds = sum(r.num_predictions for r in results)
    total_gt = sum(r.num_ground_truth for r in results)

    return AggregatedMetrics(
        num_samples=len(results),
        total_predictions=total_preds,
        total_ground_truth=total_gt,
        metrics=aggregated_metrics,
        per_sample_results=results,
    )


def evaluate_stratified(
    results_by_category: Dict[str, List[EvaluationResult]],
) -> Dict[str, AggregatedMetrics]:
    """
    Aggregate results by category (complexity, domain, etc.).

    Args:
        results_by_category: Dict mapping category names to result lists

    Returns:
        Dict mapping category names to aggregated metrics
    """
    return {
        category: aggregate_results(results)
        for category, results in results_by_category.items()
    }


def compare_to_baseline(
    method_metrics: AggregatedMetrics,
    baseline_metrics: AggregatedMetrics,
    metric_name: str = "mean_mean_iou",
) -> Dict[str, float]:
    """
    Compare method metrics to baseline.

    Args:
        method_metrics: Metrics from the method being evaluated
        baseline_metrics: Metrics from baseline method
        metric_name: Primary metric for comparison

    Returns:
        Dict with comparison statistics
    """
    method_value = method_metrics.metrics.get(metric_name, 0.0)
    baseline_value = baseline_metrics.metrics.get(metric_name, 0.0)

    absolute_diff = method_value - baseline_value
    relative_diff = (
        absolute_diff / baseline_value if baseline_value > 0 else float("inf")
    )

    return {
        "method_value": method_value,
        "baseline_value": baseline_value,
        "absolute_improvement": absolute_diff,
        "relative_improvement": relative_diff,
        "beats_baseline": method_value > baseline_value,
    }
