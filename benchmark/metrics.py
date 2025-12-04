"""
Metrics computation for benchmark evaluation.

Metrics include:
- Correctness: Answer accuracy compared to ground truth
- Region overlap: IoU between predicted and ground truth bounding boxes
- Speed: Response latency (ms)
- Token usage: Input and output token counts
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TimingMetrics:
    """Timing metrics for a single operation."""

    ocr_time_ms: float = 0.0
    embedding_time_ms: float = 0.0
    interpretability_time_ms: float = 0.0
    region_filtering_time_ms: float = 0.0
    llm_time_ms: float = 0.0
    total_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "ocr_time_ms": self.ocr_time_ms,
            "embedding_time_ms": self.embedding_time_ms,
            "interpretability_time_ms": self.interpretability_time_ms,
            "region_filtering_time_ms": self.region_filtering_time_ms,
            "llm_time_ms": self.llm_time_ms,
            "total_time_ms": self.total_time_ms,
        }


@dataclass
class TokenMetrics:
    """Token usage metrics."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class RegionMetrics:
    """Region overlap metrics."""

    # IoU-based metrics
    mean_iou: float = 0.0
    max_iou: float = 0.0
    iou_at_threshold: Dict[float, float] = field(default_factory=dict)  # Precision at IoU thresholds

    # Overlap metrics
    precision: float = 0.0  # Fraction of predicted regions that overlap GT
    recall: float = 0.0  # Fraction of GT regions that are covered
    f1: float = 0.0

    # Counts
    num_predicted_regions: int = 0
    num_ground_truth_regions: int = 0
    num_matched_regions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_iou": self.mean_iou,
            "max_iou": self.max_iou,
            "iou_at_threshold": self.iou_at_threshold,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "num_predicted_regions": self.num_predicted_regions,
            "num_ground_truth_regions": self.num_ground_truth_regions,
            "num_matched_regions": self.num_matched_regions,
        }


@dataclass
class AnswerMetrics:
    """Answer quality metrics."""

    exact_match: bool = False
    contains_answer: bool = False
    # Normalized metrics (case-insensitive, whitespace-normalized)
    normalized_exact_match: bool = False
    normalized_contains: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exact_match": self.exact_match,
            "contains_answer": self.contains_answer,
            "normalized_exact_match": self.normalized_exact_match,
            "normalized_contains": self.normalized_contains,
        }


@dataclass
class SampleResult:
    """Result for a single benchmark sample."""

    sample_id: int
    strategy: str
    query: str
    ground_truth_answer: str
    predicted_answer: str
    predicted_regions: List[Dict[str, Any]]
    ground_truth_bboxes: List[List[int]]

    timing: TimingMetrics = field(default_factory=TimingMetrics)
    tokens: TokenMetrics = field(default_factory=TokenMetrics)
    region_metrics: RegionMetrics = field(default_factory=RegionMetrics)
    answer_metrics: AnswerMetrics = field(default_factory=AnswerMetrics)

    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "strategy": self.strategy,
            "query": self.query,
            "ground_truth_answer": self.ground_truth_answer,
            "predicted_answer": self.predicted_answer,
            "num_predicted_regions": len(self.predicted_regions),
            "num_ground_truth_bboxes": len(self.ground_truth_bboxes),
            "timing": self.timing.to_dict(),
            "tokens": self.tokens.to_dict(),
            "region_metrics": self.region_metrics.to_dict(),
            "answer_metrics": self.answer_metrics.to_dict(),
            "error": self.error,
        }


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time: float = 0
        self.elapsed_ms: float = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000


def compute_iou(box1: List[int], box2: List[int]) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.

    Args:
        box1: [x1, y1, x2, y2] coordinates
        box2: [x1, y1, x2, y2] coordinates

    Returns:
        IoU score between 0 and 1
    """
    if len(box1) < 4 or len(box2) < 4:
        return 0.0

    # Get coordinates
    x1_1, y1_1, x2_1, y2_1 = box1[:4]
    x1_2, y1_2, x2_2, y2_2 = box2[:4]

    # Compute intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Compute areas
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    if area1 <= 0 or area2 <= 0:
        return 0.0

    # Compute union
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def compute_region_overlap_metrics(
    predicted_regions: List[Dict[str, Any]],
    ground_truth_bboxes: List[List[int]],
    iou_thresholds: List[float] = [0.25, 0.5, 0.75],
) -> RegionMetrics:
    """
    Compute region overlap metrics between predicted regions and ground truth.

    Args:
        predicted_regions: List of predicted region dicts with 'bbox' field
        ground_truth_bboxes: List of ground truth bounding boxes [x1, y1, x2, y2]
        iou_thresholds: IoU thresholds for computing precision at threshold

    Returns:
        RegionMetrics with overlap statistics
    """
    metrics = RegionMetrics()
    metrics.num_predicted_regions = len(predicted_regions)
    metrics.num_ground_truth_regions = len(ground_truth_bboxes)

    if not predicted_regions or not ground_truth_bboxes:
        return metrics

    # Extract predicted bboxes
    pred_bboxes = []
    for region in predicted_regions:
        bbox = region.get("bbox", [])
        if bbox and len(bbox) >= 4:
            # Handle both [x1, y1, x2, y2] and {x1, y1, x2, y2} formats
            if isinstance(bbox, dict):
                pred_bboxes.append([bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]])
            else:
                pred_bboxes.append(bbox[:4])

    if not pred_bboxes:
        return metrics

    # Compute IoU matrix
    iou_matrix = np.zeros((len(pred_bboxes), len(ground_truth_bboxes)))
    for i, pred_bbox in enumerate(pred_bboxes):
        for j, gt_bbox in enumerate(ground_truth_bboxes):
            iou_matrix[i, j] = compute_iou(pred_bbox, gt_bbox)

    # Compute metrics
    if iou_matrix.size > 0:
        metrics.mean_iou = float(np.mean(np.max(iou_matrix, axis=1)))
        metrics.max_iou = float(np.max(iou_matrix))

        # Compute precision at different IoU thresholds
        for threshold in iou_thresholds:
            matches_at_threshold = np.any(iou_matrix >= threshold, axis=1)
            metrics.iou_at_threshold[threshold] = float(np.mean(matches_at_threshold))

        # Compute precision/recall using greedy matching
        matched_pred = set()
        matched_gt = set()

        # Sort by IoU and match greedily
        for i in range(len(pred_bboxes)):
            for j in range(len(ground_truth_bboxes)):
                if iou_matrix[i, j] >= 0.5 and i not in matched_pred and j not in matched_gt:
                    matched_pred.add(i)
                    matched_gt.add(j)

        metrics.num_matched_regions = len(matched_pred)
        metrics.precision = len(matched_pred) / len(pred_bboxes) if pred_bboxes else 0.0
        metrics.recall = len(matched_gt) / len(ground_truth_bboxes) if ground_truth_bboxes else 0.0

        if metrics.precision + metrics.recall > 0:
            metrics.f1 = 2 * metrics.precision * metrics.recall / (metrics.precision + metrics.recall)

    return metrics


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Lowercase, remove extra whitespace
    return " ".join(text.lower().split())


def compute_answer_metrics(
    predicted_answer: str,
    ground_truth_answer: str,
) -> AnswerMetrics:
    """
    Compute answer quality metrics.

    Args:
        predicted_answer: Model's predicted answer
        ground_truth_answer: Ground truth answer

    Returns:
        AnswerMetrics with comparison results
    """
    metrics = AnswerMetrics()

    if not predicted_answer or not ground_truth_answer:
        return metrics

    # Exact match
    metrics.exact_match = predicted_answer == ground_truth_answer

    # Contains answer
    metrics.contains_answer = ground_truth_answer in predicted_answer

    # Normalized comparisons
    norm_pred = normalize_text(predicted_answer)
    norm_gt = normalize_text(ground_truth_answer)

    metrics.normalized_exact_match = norm_pred == norm_gt
    metrics.normalized_contains = norm_gt in norm_pred

    return metrics


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across all samples for a strategy."""

    strategy: str
    num_samples: int
    num_errors: int

    # Timing aggregates
    mean_total_time_ms: float
    mean_ocr_time_ms: float
    mean_embedding_time_ms: float
    mean_interpretability_time_ms: float
    mean_region_filtering_time_ms: float
    mean_llm_time_ms: float

    # Token aggregates
    mean_input_tokens: float
    mean_output_tokens: float
    total_input_tokens: int
    total_output_tokens: int

    # Region overlap aggregates
    mean_region_iou: float
    mean_region_precision: float
    mean_region_recall: float
    mean_region_f1: float
    iou_at_thresholds: Dict[float, float]

    # Answer quality aggregates
    exact_match_rate: float
    contains_answer_rate: float
    normalized_exact_match_rate: float
    normalized_contains_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "num_samples": self.num_samples,
            "num_errors": self.num_errors,
            "timing": {
                "mean_total_time_ms": self.mean_total_time_ms,
                "mean_ocr_time_ms": self.mean_ocr_time_ms,
                "mean_embedding_time_ms": self.mean_embedding_time_ms,
                "mean_interpretability_time_ms": self.mean_interpretability_time_ms,
                "mean_region_filtering_time_ms": self.mean_region_filtering_time_ms,
                "mean_llm_time_ms": self.mean_llm_time_ms,
            },
            "tokens": {
                "mean_input_tokens": self.mean_input_tokens,
                "mean_output_tokens": self.mean_output_tokens,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
            },
            "region_overlap": {
                "mean_iou": self.mean_region_iou,
                "mean_precision": self.mean_region_precision,
                "mean_recall": self.mean_region_recall,
                "mean_f1": self.mean_region_f1,
                "iou_at_thresholds": self.iou_at_thresholds,
            },
            "answer_quality": {
                "exact_match_rate": self.exact_match_rate,
                "contains_answer_rate": self.contains_answer_rate,
                "normalized_exact_match_rate": self.normalized_exact_match_rate,
                "normalized_contains_rate": self.normalized_contains_rate,
            },
        }


def aggregate_results(results: List[SampleResult], strategy: str) -> AggregatedMetrics:
    """
    Aggregate results from multiple samples into summary metrics.

    Args:
        results: List of SampleResult objects
        strategy: Name of the strategy

    Returns:
        AggregatedMetrics with summary statistics
    """
    if not results:
        return AggregatedMetrics(
            strategy=strategy,
            num_samples=0,
            num_errors=0,
            mean_total_time_ms=0,
            mean_ocr_time_ms=0,
            mean_embedding_time_ms=0,
            mean_interpretability_time_ms=0,
            mean_region_filtering_time_ms=0,
            mean_llm_time_ms=0,
            mean_input_tokens=0,
            mean_output_tokens=0,
            total_input_tokens=0,
            total_output_tokens=0,
            mean_region_iou=0,
            mean_region_precision=0,
            mean_region_recall=0,
            mean_region_f1=0,
            iou_at_thresholds={},
            exact_match_rate=0,
            contains_answer_rate=0,
            normalized_exact_match_rate=0,
            normalized_contains_rate=0,
        )

    num_samples = len(results)
    num_errors = sum(1 for r in results if r.error)
    valid_results = [r for r in results if not r.error]
    n_valid = len(valid_results) or 1  # Avoid division by zero

    # Timing aggregates
    mean_total_time = sum(r.timing.total_time_ms for r in valid_results) / n_valid
    mean_ocr_time = sum(r.timing.ocr_time_ms for r in valid_results) / n_valid
    mean_embedding_time = sum(r.timing.embedding_time_ms for r in valid_results) / n_valid
    mean_interp_time = sum(r.timing.interpretability_time_ms for r in valid_results) / n_valid
    mean_region_time = sum(r.timing.region_filtering_time_ms for r in valid_results) / n_valid
    mean_llm_time = sum(r.timing.llm_time_ms for r in valid_results) / n_valid

    # Token aggregates
    total_input = sum(r.tokens.input_tokens for r in valid_results)
    total_output = sum(r.tokens.output_tokens for r in valid_results)
    mean_input = total_input / n_valid
    mean_output = total_output / n_valid

    # Region overlap aggregates
    mean_iou = sum(r.region_metrics.mean_iou for r in valid_results) / n_valid
    mean_precision = sum(r.region_metrics.precision for r in valid_results) / n_valid
    mean_recall = sum(r.region_metrics.recall for r in valid_results) / n_valid
    mean_f1 = sum(r.region_metrics.f1 for r in valid_results) / n_valid

    # Aggregate IoU at thresholds
    iou_thresholds: Dict[float, List[float]] = {}
    for r in valid_results:
        for threshold, value in r.region_metrics.iou_at_threshold.items():
            if threshold not in iou_thresholds:
                iou_thresholds[threshold] = []
            iou_thresholds[threshold].append(value)

    iou_at_thresholds = {t: sum(v) / len(v) for t, v in iou_thresholds.items()}

    # Answer quality aggregates
    exact_match = sum(1 for r in valid_results if r.answer_metrics.exact_match) / n_valid
    contains = sum(1 for r in valid_results if r.answer_metrics.contains_answer) / n_valid
    norm_exact = sum(1 for r in valid_results if r.answer_metrics.normalized_exact_match) / n_valid
    norm_contains = sum(1 for r in valid_results if r.answer_metrics.normalized_contains) / n_valid

    return AggregatedMetrics(
        strategy=strategy,
        num_samples=num_samples,
        num_errors=num_errors,
        mean_total_time_ms=mean_total_time,
        mean_ocr_time_ms=mean_ocr_time,
        mean_embedding_time_ms=mean_embedding_time,
        mean_interpretability_time_ms=mean_interp_time,
        mean_region_filtering_time_ms=mean_region_time,
        mean_llm_time_ms=mean_llm_time,
        mean_input_tokens=mean_input,
        mean_output_tokens=mean_output,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        mean_region_iou=mean_iou,
        mean_region_precision=mean_precision,
        mean_region_recall=mean_recall,
        mean_region_f1=mean_f1,
        iou_at_thresholds=iou_at_thresholds,
        exact_match_rate=exact_match,
        contains_answer_rate=contains,
        normalized_exact_match_rate=norm_exact,
        normalized_contains_rate=norm_contains,
    )
