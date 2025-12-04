"""
Metrics collection and calculation for benchmarking.

Tracks:
- Correctness: Answer accuracy metrics (exact match, F1, ANLS)
- Latency: Response time measurements
- Tokens: Input/output token counts for LLM calls
- Retrieval: Hit rate, MRR, precision@k
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Latency measurements for a single sample."""

    retrieval_ms: float = 0.0  # Time to retrieve documents
    llm_inference_ms: float = 0.0  # Time for LLM to generate answer
    total_ms: float = 0.0  # Total end-to-end time
    region_filtering_ms: float = 0.0  # Time for region relevance filtering
    embedding_ms: float = 0.0  # Time for query embedding


@dataclass
class TokenMetrics:
    """Token usage for a single sample."""

    input_tokens: int = 0  # Tokens in LLM prompt
    output_tokens: int = 0  # Tokens in LLM response
    total_tokens: int = 0  # Total tokens used
    context_tokens: int = 0  # Tokens from retrieved context


@dataclass
class RetrievalMetrics:
    """Retrieval quality metrics for a single sample."""

    hit: bool = False  # Did we retrieve at least one relevant doc?
    reciprocal_rank: float = 0.0  # 1/rank of first relevant result
    precision_at_k: float = 0.0  # Precision at k
    recall_at_k: float = 0.0  # Recall at k
    retrieved_pages: List[int] = field(default_factory=list)
    relevant_pages: List[int] = field(default_factory=list)
    bbox_iou: float = 0.0  # IoU between retrieved and ground truth bbox


@dataclass
class CorrectnessMetrics:
    """Answer correctness metrics for a single sample."""

    exact_match: float = 0.0  # Binary exact match (normalized)
    f1_score: float = 0.0  # Token-level F1 score
    anls: float = 0.0  # Average Normalized Levenshtein Similarity
    semantic_similarity: float = 0.0  # Embedding-based similarity
    llm_judge_score: float = 0.0  # LLM-based semantic correctness


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
    retrieval: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    correctness: CorrectnessMetrics = field(default_factory=CorrectnessMetrics)

    # Additional metadata
    error: Optional[str] = None
    retrieved_context: Optional[str] = None
    retrieved_regions: Optional[List[Dict[str, Any]]] = None  # Filtered regions with scores
    raw_response: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """Collects and aggregates metrics across benchmark runs."""

    def __init__(self):
        self.results: Dict[str, List[SampleResult]] = defaultdict(list)
        self._timers: Dict[str, float] = {}

    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self._timers[name] = time.perf_counter()

    def stop_timer(self, name: str) -> float:
        """Stop a named timer and return elapsed milliseconds."""
        if name not in self._timers:
            return 0.0
        elapsed = (time.perf_counter() - self._timers[name]) * 1000
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
            "retrieval_ms": [r.latency.retrieval_ms for r in successful],
            "llm_inference_ms": [r.latency.llm_inference_ms for r in successful],
            "total_ms": [r.latency.total_ms for r in successful],
            "region_filtering_ms": [r.latency.region_filtering_ms for r in successful],
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

        # Retrieval aggregates
        retrieval_stats = {
            "hit_rate": float(np.mean([r.retrieval.hit for r in successful])),
            "mrr": float(
                np.mean([r.retrieval.reciprocal_rank for r in successful])
            ),
            "precision_at_k": float(
                np.mean([r.retrieval.precision_at_k for r in successful])
            ),
            "recall_at_k": float(
                np.mean([r.retrieval.recall_at_k for r in successful])
            ),
            "mean_bbox_iou": float(
                np.mean([r.retrieval.bbox_iou for r in successful])
            ),
        }

        # Correctness aggregates
        correctness_stats = {
            "exact_match": float(
                np.mean([r.correctness.exact_match for r in successful])
            ),
            "f1_score": float(np.mean([r.correctness.f1_score for r in successful])),
            "anls": float(np.mean([r.correctness.anls for r in successful])),
            "semantic_similarity": float(
                np.mean([r.correctness.semantic_similarity for r in successful])
            ),
            "llm_judge_score": float(
                np.mean([r.correctness.llm_judge_score for r in successful])
            ),
        }

        return {
            "strategy": strategy,
            "total_samples": len(results),
            "successful_samples": len(successful),
            "error_rate": (len(results) - len(successful)) / len(results),
            "latency": latency_stats,
            "tokens": token_stats,
            "retrieval": retrieval_stats,
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
                        for metric in ["total_ms", "retrieval_ms", "llm_inference_ms"]:
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
                        for metric in ["exact_match", "f1_score", "anls", "llm_judge_score"]:
                            baseline_val = baseline["correctness"].get(metric, 0)
                            current_val = current["correctness"].get(metric, 0)
                            if baseline_val > 0:
                                relative[f"{metric}_improvement"] = (
                                    current_val / baseline_val
                                )

                    comparison[strategy]["relative_to_baseline"] = relative

        return comparison


def compute_exact_match(prediction: str, ground_truth: str) -> float:
    """Compute normalized exact match score."""
    # Normalize both strings
    pred_norm = _normalize_answer(prediction)
    gt_norm = _normalize_answer(ground_truth)

    return 1.0 if pred_norm == gt_norm else 0.0


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


def compute_anls(prediction: str, ground_truth: str, threshold: float = 0.5) -> float:
    """
    Compute Average Normalized Levenshtein Similarity (ANLS).

    ANLS is commonly used for document VQA evaluation.
    """

    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    pred_norm = _normalize_answer(prediction)
    gt_norm = _normalize_answer(ground_truth)

    if not gt_norm:
        return 1.0 if not pred_norm else 0.0

    distance = levenshtein_distance(pred_norm, gt_norm)
    max_len = max(len(pred_norm), len(gt_norm))

    if max_len == 0:
        return 1.0

    nls = 1 - distance / max_len

    return nls if nls >= threshold else 0.0


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
