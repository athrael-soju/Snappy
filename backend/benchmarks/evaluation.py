"""
Evaluation metrics and ground truth matching for bounding box prediction.

This module implements various evaluation strategies and metrics for comparing
predicted bounding boxes against ground truth annotations.

Metrics:
- IoU@threshold: Hit rate at various overlap thresholds
- Mean IoU: Average IoU across predictions
- Precision@K: Fraction of top-K predictions matching GT
- Recall@K: Fraction of GT boxes covered by top-K predictions
- mAP: Mean average precision across IoU thresholds

Matching strategies:
- Any-match: Lenient - any prediction matching any GT
- Set coverage: Precision/recall-style evaluation
- Hungarian: Optimal 1:1 assignment
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from .aggregation import RegionScore
from .utils.coordinates import compute_iou, NormalizedBox

logger = logging.getLogger(__name__)


# Matching strategy types
MatchingStrategy = Literal["any", "coverage", "hungarian"]


@dataclass
class SampleEvaluation:
    """Evaluation results for a single sample."""

    sample_id: str

    # IoU metrics at different thresholds
    iou_at_thresholds: Dict[float, bool] = field(default_factory=dict)

    # Mean and max IoU
    mean_iou: float = 0.0
    max_iou: float = 0.0

    # Coverage metrics
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    # Hungarian matching
    hungarian_mean_iou: float = 0.0
    hungarian_matched: int = 0

    # Raw data
    num_predictions: int = 0
    num_ground_truth: int = 0
    iou_matrix: Optional[List[List[float]]] = None


@dataclass
class BenchmarkResults:
    """Aggregated results across all samples."""

    # Sample-level results
    samples: List[SampleEvaluation] = field(default_factory=list)

    # Aggregated metrics
    mean_iou: float = 0.0
    mean_max_iou: float = 0.0

    # Hit rates at different thresholds
    hit_rate_at_thresholds: Dict[float, float] = field(default_factory=dict)

    # Mean precision/recall/F1
    mean_precision: float = 0.0
    mean_recall: float = 0.0
    mean_f1: float = 0.0

    # Hungarian matching
    mean_hungarian_iou: float = 0.0

    # mAP across thresholds
    mAP: float = 0.0

    # Metadata
    total_samples: int = 0
    config: Dict[str, Any] = field(default_factory=dict)


class BBoxEvaluator:
    """
    Evaluates predicted bounding boxes against ground truth.

    Supports multiple matching strategies and computes various metrics.
    """

    def __init__(
        self,
        iou_thresholds: Optional[List[float]] = None,
        matching_strategies: Optional[List[MatchingStrategy]] = None,
    ):
        """
        Initialize the evaluator.

        Args:
            iou_thresholds: IoU thresholds for hit rate computation
            matching_strategies: Strategies to use for evaluation
        """
        self.iou_thresholds = iou_thresholds or [0.25, 0.5, 0.75]
        self.matching_strategies = matching_strategies or ["any", "coverage", "hungarian"]

    def evaluate_sample(
        self,
        predictions: List[NormalizedBox],
        ground_truth: List[NormalizedBox],
        sample_id: str = "",
    ) -> SampleEvaluation:
        """
        Evaluate predictions against ground truth for a single sample.

        Args:
            predictions: List of predicted bounding boxes (normalized)
            ground_truth: List of ground truth bounding boxes (normalized)
            sample_id: Identifier for the sample

        Returns:
            SampleEvaluation with all computed metrics
        """
        result = SampleEvaluation(
            sample_id=sample_id,
            num_predictions=len(predictions),
            num_ground_truth=len(ground_truth),
        )

        if not predictions or not ground_truth:
            return result

        # Compute IoU matrix
        iou_matrix = self._compute_iou_matrix(predictions, ground_truth)
        result.iou_matrix = iou_matrix.tolist()

        # Compute basic IoU metrics
        result.mean_iou = float(np.mean(iou_matrix))
        result.max_iou = float(np.max(iou_matrix))

        # Compute hit rates at different thresholds
        for thresh in self.iou_thresholds:
            result.iou_at_thresholds[thresh] = self._any_match(iou_matrix, thresh)

        # Compute coverage metrics
        precision, recall, f1 = self._compute_coverage(iou_matrix, threshold=0.5)
        result.precision = precision
        result.recall = recall
        result.f1 = f1

        # Compute Hungarian matching
        hungarian_iou, matched = self._hungarian_matching(iou_matrix)
        result.hungarian_mean_iou = hungarian_iou
        result.hungarian_matched = matched

        return result

    def evaluate_from_region_scores(
        self,
        region_scores: List[RegionScore],
        ground_truth: List[NormalizedBox],
        sample_id: str = "",
    ) -> SampleEvaluation:
        """
        Evaluate using RegionScore objects.

        Args:
            region_scores: List of RegionScore objects with bbox fields
            ground_truth: List of ground truth bounding boxes
            sample_id: Sample identifier

        Returns:
            SampleEvaluation with computed metrics
        """
        predictions = [r.bbox for r in region_scores]
        return self.evaluate_sample(predictions, ground_truth, sample_id)

    def evaluate_batch(
        self,
        batch_predictions: List[List[NormalizedBox]],
        batch_ground_truth: List[List[NormalizedBox]],
        sample_ids: Optional[List[str]] = None,
    ) -> BenchmarkResults:
        """
        Evaluate a batch of samples.

        Args:
            batch_predictions: List of prediction lists per sample
            batch_ground_truth: List of ground truth lists per sample
            sample_ids: Optional sample identifiers

        Returns:
            BenchmarkResults with aggregated metrics
        """
        if len(batch_predictions) != len(batch_ground_truth):
            raise ValueError(
                f"Prediction and ground truth batch sizes don't match: "
                f"{len(batch_predictions)} vs {len(batch_ground_truth)}"
            )

        if sample_ids is None:
            sample_ids = [f"sample_{i}" for i in range(len(batch_predictions))]

        results = BenchmarkResults(total_samples=len(batch_predictions))

        # Evaluate each sample
        for preds, gts, sid in zip(batch_predictions, batch_ground_truth, sample_ids):
            sample_eval = self.evaluate_sample(preds, gts, sid)
            results.samples.append(sample_eval)

        # Aggregate metrics
        self._aggregate_metrics(results)

        return results

    def _compute_iou_matrix(
        self,
        predictions: List[NormalizedBox],
        ground_truth: List[NormalizedBox],
    ) -> np.ndarray:
        """
        Compute IoU matrix between predictions and ground truth.

        Args:
            predictions: List of predicted boxes
            ground_truth: List of ground truth boxes

        Returns:
            IoU matrix of shape (num_predictions, num_ground_truth)
        """
        n_preds = len(predictions)
        n_gt = len(ground_truth)

        iou_matrix = np.zeros((n_preds, n_gt))

        for i, pred in enumerate(predictions):
            for j, gt in enumerate(ground_truth):
                iou_matrix[i, j] = compute_iou(pred, gt)

        return iou_matrix

    def _any_match(self, iou_matrix: np.ndarray, threshold: float) -> bool:
        """Check if any prediction matches any ground truth above threshold."""
        return bool(np.any(iou_matrix >= threshold))

    def _compute_coverage(
        self,
        iou_matrix: np.ndarray,
        threshold: float = 0.5,
    ) -> Tuple[float, float, float]:
        """
        Compute precision, recall, and F1 based on set coverage.

        A ground truth box is "covered" if any prediction has IoU >= threshold.
        A prediction is "valid" if it covers any ground truth box.

        Args:
            iou_matrix: IoU matrix (predictions × ground_truth)
            threshold: IoU threshold for matching

        Returns:
            (precision, recall, f1)
        """
        n_preds, n_gt = iou_matrix.shape

        if n_preds == 0 or n_gt == 0:
            return 0.0, 0.0, 0.0

        # Count covered ground truth boxes
        covered_gt = np.sum(np.any(iou_matrix >= threshold, axis=0))
        recall = covered_gt / n_gt

        # Count valid predictions (those that cover at least one GT)
        valid_preds = np.sum(np.any(iou_matrix >= threshold, axis=1))
        precision = valid_preds / n_preds

        # F1 score
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        return float(precision), float(recall), float(f1)

    def _hungarian_matching(
        self,
        iou_matrix: np.ndarray,
    ) -> Tuple[float, int]:
        """
        Compute optimal 1:1 matching using Hungarian algorithm.

        Args:
            iou_matrix: IoU matrix (predictions × ground_truth)

        Returns:
            (mean_iou_of_matched, num_matched)
        """
        try:
            from scipy.optimize import linear_sum_assignment
        except ImportError:
            logger.warning(
                "scipy not available for Hungarian matching, using greedy"
            )
            return self._greedy_matching(iou_matrix)

        n_preds, n_gt = iou_matrix.shape

        if n_preds == 0 or n_gt == 0:
            return 0.0, 0

        # Hungarian algorithm minimizes cost, so use 1 - IoU
        cost_matrix = 1 - iou_matrix

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # Compute matched IoUs
        matched_ious = [iou_matrix[r, c] for r, c in zip(row_ind, col_ind)]

        if matched_ious:
            mean_iou = float(np.mean(matched_ious))
        else:
            mean_iou = 0.0

        return mean_iou, len(matched_ious)

    def _greedy_matching(
        self,
        iou_matrix: np.ndarray,
    ) -> Tuple[float, int]:
        """
        Greedy matching fallback when scipy is not available.

        Args:
            iou_matrix: IoU matrix

        Returns:
            (mean_iou_of_matched, num_matched)
        """
        n_preds, n_gt = iou_matrix.shape
        matched_ious = []

        used_preds = set()
        used_gt = set()

        # Sort all IoU values descending
        indices = np.argsort(iou_matrix.ravel())[::-1]

        for idx in indices:
            pred_idx = idx // n_gt
            gt_idx = idx % n_gt

            if pred_idx in used_preds or gt_idx in used_gt:
                continue

            iou_val = iou_matrix[pred_idx, gt_idx]
            if iou_val > 0:
                matched_ious.append(iou_val)
                used_preds.add(pred_idx)
                used_gt.add(gt_idx)

            if len(used_preds) == n_preds or len(used_gt) == n_gt:
                break

        if matched_ious:
            return float(np.mean(matched_ious)), len(matched_ious)
        return 0.0, 0

    def _aggregate_metrics(self, results: BenchmarkResults) -> None:
        """Aggregate sample-level metrics into benchmark results."""
        if not results.samples:
            return

        n = len(results.samples)

        # Mean IoU metrics
        results.mean_iou = sum(s.mean_iou for s in results.samples) / n
        results.mean_max_iou = sum(s.max_iou for s in results.samples) / n

        # Hit rates at thresholds
        for thresh in self.iou_thresholds:
            hits = sum(
                1 for s in results.samples if s.iou_at_thresholds.get(thresh, False)
            )
            results.hit_rate_at_thresholds[thresh] = hits / n

        # Mean precision/recall/F1
        results.mean_precision = sum(s.precision for s in results.samples) / n
        results.mean_recall = sum(s.recall for s in results.samples) / n
        results.mean_f1 = sum(s.f1 for s in results.samples) / n

        # Mean Hungarian IoU
        results.mean_hungarian_iou = sum(
            s.hungarian_mean_iou for s in results.samples
        ) / n

        # Compute mAP (mean AP across IoU thresholds)
        results.mAP = sum(results.hit_rate_at_thresholds.values()) / len(
            self.iou_thresholds
        )

        results.config = {
            "iou_thresholds": self.iou_thresholds,
            "matching_strategies": self.matching_strategies,
        }


class StratifiedEvaluator:
    """
    Evaluator that computes metrics stratified by different dimensions.

    Supports stratification by:
    - Category (SPSBB, SPMBB, MPMBB)
    - Region type (Text, Image, Table)
    - Domain (cs, econ, math, etc.)
    """

    def __init__(self, base_evaluator: Optional[BBoxEvaluator] = None):
        """
        Initialize with optional base evaluator.

        Args:
            base_evaluator: Base evaluator to use (creates default if None)
        """
        self.evaluator = base_evaluator or BBoxEvaluator()

    def evaluate_stratified(
        self,
        predictions: List[List[NormalizedBox]],
        ground_truth: List[List[NormalizedBox]],
        sample_metadata: List[Dict[str, Any]],
        stratify_by: str = "category",
    ) -> Dict[str, BenchmarkResults]:
        """
        Evaluate with stratification by a metadata field.

        Args:
            predictions: List of prediction lists per sample
            ground_truth: List of ground truth lists per sample
            sample_metadata: List of metadata dicts with stratification field
            stratify_by: Metadata field to stratify by

        Returns:
            Dictionary mapping stratum values to BenchmarkResults
        """
        # Group samples by stratum
        strata: Dict[str, Tuple[List, List, List]] = {}

        for preds, gts, meta in zip(predictions, ground_truth, sample_metadata):
            stratum = meta.get(stratify_by, "unknown")
            if stratum not in strata:
                strata[stratum] = ([], [], [])

            strata[stratum][0].append(preds)
            strata[stratum][1].append(gts)
            strata[stratum][2].append(meta.get("sample_id", ""))

        # Evaluate each stratum
        results = {}
        for stratum, (preds, gts, ids) in strata.items():
            results[stratum] = self.evaluator.evaluate_batch(preds, gts, ids)

        return results


def compute_precision_at_k(
    predictions: List[NormalizedBox],
    ground_truth: List[NormalizedBox],
    k: int,
    iou_threshold: float = 0.5,
) -> float:
    """
    Compute precision at K.

    Args:
        predictions: Ranked list of predicted boxes
        ground_truth: Ground truth boxes
        k: Number of top predictions to consider
        iou_threshold: IoU threshold for matching

    Returns:
        Precision at K
    """
    if not predictions or not ground_truth or k <= 0:
        return 0.0

    top_k = predictions[:k]
    valid = 0

    for pred in top_k:
        for gt in ground_truth:
            if compute_iou(pred, gt) >= iou_threshold:
                valid += 1
                break

    return valid / k


def compute_recall_at_k(
    predictions: List[NormalizedBox],
    ground_truth: List[NormalizedBox],
    k: int,
    iou_threshold: float = 0.5,
) -> float:
    """
    Compute recall at K.

    Args:
        predictions: Ranked list of predicted boxes
        ground_truth: Ground truth boxes
        k: Number of top predictions to consider
        iou_threshold: IoU threshold for matching

    Returns:
        Recall at K (fraction of GT boxes covered by top-K predictions)
    """
    if not predictions or not ground_truth or k <= 0:
        return 0.0

    top_k = predictions[:k]
    covered = 0

    for gt in ground_truth:
        for pred in top_k:
            if compute_iou(pred, gt) >= iou_threshold:
                covered += 1
                break

    return covered / len(ground_truth)
