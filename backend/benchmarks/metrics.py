"""
Metrics collection and calculation for benchmarking.

Tracks:
- Correctness: Answer accuracy metrics (F1, LLM Judge)
- Latency: Response time measurements
- Tokens: Input/output token counts for LLM calls
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class LatencyMetrics:
    """Latency measurements for a single sample (in seconds)."""

    retrieval_s: float = 0.0  # Time to retrieve documents
    llm_inference_s: float = 0.0  # Time for LLM to generate answer
    total_s: float = 0.0  # Total end-to-end time
    region_filtering_s: float = 0.0  # Time for region relevance filtering
    embedding_s: float = 0.0  # Time for query embedding


@dataclass
class TokenMetrics:
    """Token usage for a single sample."""

    input_tokens: int = 0  # Tokens in LLM prompt
    output_tokens: int = 0  # Tokens in LLM response
    total_tokens: int = 0  # Total tokens used
    context_tokens: int = 0  # Tokens from retrieved context


@dataclass
class CorrectnessMetrics:
    """Answer correctness metrics for a single sample."""

    f1_score: float = 0.0  # Token-level F1 score
    llm_judge_correct: bool = False  # LLM-based semantic correctness


@dataclass
class SampleResult:
    """Complete result for a single benchmark sample."""

    sample_id: str
    query: str
    ground_truth: str
    predicted_answer: str
    strategy: str

    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    tokens: TokenMetrics = field(default_factory=TokenMetrics)
    correctness: CorrectnessMetrics = field(default_factory=CorrectnessMetrics)

    # Additional metadata
    error: Optional[str] = None
    retrieved_context: Optional[str] = None
    retrieved_regions: Optional[List[Dict[str, Any]]] = None  # Filtered regions with scores
    raw_response: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None  # Local path to sample image


class MetricsCollector:
    """Collects and aggregates metrics across benchmark runs."""

    def __init__(self):
        self.results: Dict[str, List[SampleResult]] = defaultdict(list)
        self._timers: Dict[str, float] = {}

    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self._timers[name] = time.perf_counter()

    def stop_timer(self, name: str) -> float:
        """Stop a named timer and return elapsed seconds."""
        if name not in self._timers:
            return 0.0
        elapsed = time.perf_counter() - self._timers[name]
        del self._timers[name]
        return elapsed

    def add_result(self, result: SampleResult) -> None:
        """Add a sample result."""
        self.results[result.strategy].append(result)

    def get_strategy_results(self, strategy: str) -> List[SampleResult]:
        """Get all results for a strategy."""
        return self.results.get(strategy, [])

    def compute_aggregate_metrics(self, strategy: str) -> Dict[str, Any]:
        """Compute aggregate metrics for a strategy."""
        results = self.results.get(strategy, [])
        if not results:
            return {}

        # Filter successful results
        successful = [r for r in results if r.error is None]
        if not successful:
            return {"error_rate": 1.0, "total_samples": len(results)}

        # Latency aggregates
        latencies = {
            "retrieval_s": [r.latency.retrieval_s for r in successful],
            "llm_inference_s": [r.latency.llm_inference_s for r in successful],
            "total_s": [r.latency.total_s for r in successful],
            "region_filtering_s": [r.latency.region_filtering_s for r in successful],
        }

        latency_stats = {}
        for name, values in latencies.items():
            if values:
                latency_stats[name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "p50": float(np.percentile(values, 50)),
                    "p95": float(np.percentile(values, 95)),
                    "p99": float(np.percentile(values, 99)),
                }

        # Token aggregates
        token_stats = {
            "input_tokens": {
                "mean": float(np.mean([r.tokens.input_tokens for r in successful])),
                "total": sum(r.tokens.input_tokens for r in successful),
            },
            "output_tokens": {
                "mean": float(np.mean([r.tokens.output_tokens for r in successful])),
                "total": sum(r.tokens.output_tokens for r in successful),
            },
            "total_tokens": {
                "mean": float(np.mean([r.tokens.total_tokens for r in successful])),
                "total": sum(r.tokens.total_tokens for r in successful),
            },
        }

        # Correctness aggregates
        correct_count = sum(1 for r in successful if r.correctness.llm_judge_correct)
        correctness_stats = {
            "f1_score": float(np.mean([r.correctness.f1_score for r in successful])),
            "llm_judge_correct": correct_count,
            "llm_judge_accuracy": correct_count / len(successful),
        }

        return {
            "strategy": strategy,
            "total_samples": len(results),
            "successful_samples": len(successful),
            "error_rate": (len(results) - len(successful)) / len(results),
            "latency": latency_stats,
            "tokens": token_stats,
            "correctness": correctness_stats,
        }

    def compare_strategies(self) -> Dict[str, Any]:
        """Compare all strategies and compute relative performance."""
        comparison = {}
        strategies = list(self.results.keys())

        for strategy in strategies:
            comparison[strategy] = self.compute_aggregate_metrics(strategy)

        # Compute relative improvements (using first strategy as baseline)
        if len(strategies) >= 2:
            baseline = comparison[strategies[0]]
            for strategy in strategies[1:]:
                current = comparison[strategy]
                if current and baseline:
                    relative = {}

                    # Latency improvement (lower is better)
                    if "latency" in baseline and "latency" in current:
                        for metric in ["total_s", "retrieval_s", "llm_inference_s"]:
                            if (
                                metric in baseline["latency"]
                                and metric in current["latency"]
                            ):
                                baseline_val = baseline["latency"][metric]["mean"]
                                current_val = current["latency"][metric]["mean"]
                                if baseline_val > 0:
                                    relative[f"{metric}_speedup"] = (
                                        baseline_val / current_val
                                    )

                    # Correctness improvement (higher is better)
                    if "correctness" in baseline and "correctness" in current:
                        for metric in ["f1_score", "llm_judge_accuracy"]:
                            baseline_val = baseline["correctness"].get(metric, 0)
                            current_val = current["correctness"].get(metric, 0)
                            if baseline_val > 0:
                                relative[f"{metric}_improvement"] = (
                                    current_val / baseline_val
                                )

                    comparison[strategy]["relative_to_baseline"] = relative

        return comparison


def compute_f1_score(prediction: str, ground_truth: str) -> float:
    """Compute token-level F1 score."""
    pred_tokens = set(_normalize_answer(prediction).split())
    gt_tokens = set(_normalize_answer(ground_truth).split())

    if not pred_tokens or not gt_tokens:
        return 0.0

    common = pred_tokens & gt_tokens
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)

    return 2 * precision * recall / (precision + recall)


def _normalize_bbox(bbox: Any) -> Optional[List[int]]:
    """
    Normalize a bounding box to [x1, y1, x2, y2] format.

    Handles various input formats:
    - [x1, y1, x2, y2] -> [x1, y1, x2, y2]
    - [[x1, y1, x2, y2]] -> [x1, y1, x2, y2]
    - Invalid formats -> None
    """
    if not bbox:
        return None

    # Unwrap extra nesting if present
    while isinstance(bbox, list) and len(bbox) == 1 and isinstance(bbox[0], list):
        bbox = bbox[0]

    # Validate format: should be [x1, y1, x2, y2] with numeric values
    if isinstance(bbox, list) and len(bbox) >= 4:
        try:
            return [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]
        except (TypeError, ValueError):
            return None

    return None


def _normalize_bbox_list(bboxes: List[Any]) -> List[List[int]]:
    """Normalize a list of bounding boxes, filtering out invalid ones."""
    normalized = []
    for bbox in bboxes:
        norm = _normalize_bbox(bbox)
        if norm:
            normalized.append(norm)
    return normalized


def compute_bbox_iou(
    predicted_bboxes: List[List[int]], ground_truth_bboxes: List[List[int]]
) -> float:
    """
    Compute Intersection over Union between predicted and ground truth bboxes.

    Args:
        predicted_bboxes: List of [x1, y1, x2, y2] predictions
        ground_truth_bboxes: List of [x1, y1, x2, y2] ground truths

    Returns:
        Average IoU across all ground truth boxes
    """
    if not predicted_bboxes or not ground_truth_bboxes:
        return 0.0

    # Normalize bbox formats to handle inconsistent nesting
    pred_boxes = _normalize_bbox_list(predicted_bboxes)
    gt_boxes = _normalize_bbox_list(ground_truth_bboxes)

    if not pred_boxes or not gt_boxes:
        return 0.0

    def single_iou(box1: List[int], box2: List[int]) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    # For each ground truth box, find best matching prediction
    ious = []
    for gt_box in gt_boxes:
        best_iou = max(single_iou(pred_box, gt_box) for pred_box in pred_boxes)
        ious.append(best_iou)

    return float(np.mean(ious)) if ious else 0.0


def _normalize_answer(text: str) -> str:
    """Normalize answer text for comparison."""
    import re
    import string

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove articles
    text = re.sub(r"\b(a|an|the)\b", " ", text)

    # Remove extra whitespace
    text = " ".join(text.split())

    return text.strip()
