"""
Evaluation metrics for spatially-grounded document retrieval.

Implements ANLS, IoU, Precision@k, Recall, and token counting metrics.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

import tiktoken

from eval.dataset import BoundingBox, OCRRegion


def normalize_text(text: str) -> str:
    """
    Normalize text for ANLS comparison.

    Applies lowercasing, whitespace normalization, and punctuation handling.
    """
    # Lowercase
    text = text.lower()
    # Normalize whitespace
    text = " ".join(text.split())
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_anls(
    prediction: str,
    ground_truth: Union[str, List[str]],
    threshold: float = 0.5,
) -> float:
    """
    Compute Average Normalized Levenshtein Similarity (ANLS).

    ANLS is the standard metric for DocVQA tasks. It computes:
    ANLS = 1 - NL(pred, gt) if NL < threshold else 0

    where NL = levenshtein_distance / max(len(pred), len(gt))

    Args:
        prediction: Model prediction
        ground_truth: Ground truth answer (or list of acceptable answers)
        threshold: Maximum normalized edit distance to count as a match (default 0.5)

    Returns:
        ANLS score between 0 and 1
    """
    prediction = normalize_text(prediction)

    # Handle multiple acceptable answers
    if isinstance(ground_truth, str):
        ground_truths = [ground_truth]
    else:
        ground_truths = ground_truth

    # Compute ANLS against each ground truth and take maximum
    max_anls = 0.0
    for gt in ground_truths:
        gt_normalized = normalize_text(gt)

        if not prediction and not gt_normalized:
            # Both empty
            anls = 1.0
        elif not prediction or not gt_normalized:
            # One is empty
            anls = 0.0
        else:
            # Compute normalized Levenshtein distance
            edit_distance = levenshtein_distance(prediction, gt_normalized)
            max_len = max(len(prediction), len(gt_normalized))
            normalized_distance = edit_distance / max_len

            # Apply threshold
            if normalized_distance < threshold:
                anls = 1.0 - normalized_distance
            else:
                anls = 0.0

        max_anls = max(max_anls, anls)

    return max_anls


def compute_iou(
    bbox1: Union[BoundingBox, List[float]],
    bbox2: Union[BoundingBox, List[float]],
) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.

    Args:
        bbox1: First bounding box (BoundingBox or [x1, y1, x2, y2])
        bbox2: Second bounding box (BoundingBox or [x1, y1, x2, y2])

    Returns:
        IoU score between 0 and 1
    """
    # Convert to BoundingBox if needed
    if isinstance(bbox1, list):
        bbox1 = BoundingBox.from_list(bbox1)
    if isinstance(bbox2, list):
        bbox2 = BoundingBox.from_list(bbox2)

    # Compute intersection
    inter_x1 = max(bbox1.x1, bbox2.x1)
    inter_y1 = max(bbox1.y1, bbox2.y1)
    inter_x2 = min(bbox1.x2, bbox2.x2)
    inter_y2 = min(bbox1.y2, bbox2.y2)

    inter_width = max(0, inter_x2 - inter_x1)
    inter_height = max(0, inter_y2 - inter_y1)
    intersection = inter_width * inter_height

    # Compute union
    union = bbox1.area + bbox2.area - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def compute_iou_at_1(
    retrieved_regions: List[Union[OCRRegion, Dict[str, Any]]],
    ground_truth_bbox: Union[BoundingBox, List[float]],
) -> float:
    """
    Compute IoU between the top-1 retrieved region and ground truth.

    Args:
        retrieved_regions: List of retrieved regions (sorted by relevance)
        ground_truth_bbox: Ground truth bounding box

    Returns:
        IoU score for the top-1 region (0 if no regions)
    """
    if not retrieved_regions:
        return 0.0

    top_region = retrieved_regions[0]
    if isinstance(top_region, OCRRegion):
        region_bbox = top_region.bbox
    else:
        bbox_data = top_region.get("bbox", [0, 0, 0, 0])
        region_bbox = BoundingBox.from_list(bbox_data) if isinstance(bbox_data, list) else bbox_data

    return compute_iou(region_bbox, ground_truth_bbox)


def compute_iou_at_k(
    retrieved_regions: List[Union[OCRRegion, Dict[str, Any]]],
    ground_truth_bbox: Union[BoundingBox, List[float]],
    k: Optional[int] = None,
) -> float:
    """
    Compute IoU between the union of top-k regions and ground truth.

    Args:
        retrieved_regions: List of retrieved regions (sorted by relevance)
        ground_truth_bbox: Ground truth bounding box
        k: Number of top regions to consider (None = all)

    Returns:
        IoU score for the union of top-k regions
    """
    if not retrieved_regions:
        return 0.0

    # Get top-k regions
    regions = retrieved_regions[:k] if k else retrieved_regions

    # Compute bounding box of union (simple: min/max of all coordinates)
    x1_min = float("inf")
    y1_min = float("inf")
    x2_max = float("-inf")
    y2_max = float("-inf")

    for region in regions:
        if isinstance(region, OCRRegion):
            bbox = region.bbox
        else:
            bbox_data = region.get("bbox", [0, 0, 0, 0])
            bbox = BoundingBox.from_list(bbox_data) if isinstance(bbox_data, list) else bbox_data

        x1_min = min(x1_min, bbox.x1)
        y1_min = min(y1_min, bbox.y1)
        x2_max = max(x2_max, bbox.x2)
        y2_max = max(y2_max, bbox.y2)

    if x1_min == float("inf"):
        return 0.0

    union_bbox = BoundingBox(x1=x1_min, y1=y1_min, x2=x2_max, y2=y2_max)
    return compute_iou(union_bbox, ground_truth_bbox)


def compute_precision_at_k(
    retrieved_regions: List[Union[OCRRegion, Dict[str, Any]]],
    ground_truth_bbox: Union[BoundingBox, List[float]],
    k: int = 5,
    iou_threshold: float = 0.5,
) -> float:
    """
    Compute Precision@k: fraction of top-k regions that overlap with GT.

    A region is considered a "hit" if its IoU with the ground truth bbox
    exceeds the threshold.

    Args:
        retrieved_regions: List of retrieved regions (sorted by relevance)
        ground_truth_bbox: Ground truth bounding box
        k: Number of top regions to evaluate
        iou_threshold: Minimum IoU to consider a match

    Returns:
        Precision@k score between 0 and 1
    """
    if not retrieved_regions:
        return 0.0

    # Get top-k regions
    top_k = retrieved_regions[:k]
    if not top_k:
        return 0.0

    # Count hits
    hits = 0
    for region in top_k:
        if isinstance(region, OCRRegion):
            bbox = region.bbox
        else:
            bbox_data = region.get("bbox", [0, 0, 0, 0])
            bbox = BoundingBox.from_list(bbox_data) if isinstance(bbox_data, list) else bbox_data

        iou = compute_iou(bbox, ground_truth_bbox)
        if iou >= iou_threshold:
            hits += 1

    return hits / len(top_k)


def compute_recall(
    retrieved_regions: List[Union[OCRRegion, Dict[str, Any]]],
    ground_truth_bbox: Union[BoundingBox, List[float]],
) -> float:
    """
    Compute recall: fraction of GT bbox area covered by retrieved regions.

    Args:
        retrieved_regions: List of retrieved regions
        ground_truth_bbox: Ground truth bounding box

    Returns:
        Recall score between 0 and 1
    """
    if isinstance(ground_truth_bbox, list):
        ground_truth_bbox = BoundingBox.from_list(ground_truth_bbox)

    if ground_truth_bbox.area <= 0:
        return 0.0

    if not retrieved_regions:
        return 0.0

    # Compute total intersection area (simplified: sum of individual intersections)
    # Note: This may overcount if regions overlap, but is a reasonable approximation
    total_intersection = 0.0
    for region in retrieved_regions:
        if isinstance(region, OCRRegion):
            bbox = region.bbox
        else:
            bbox_data = region.get("bbox", [0, 0, 0, 0])
            bbox = BoundingBox.from_list(bbox_data) if isinstance(bbox_data, list) else bbox_data

        # Compute intersection with GT
        inter_x1 = max(bbox.x1, ground_truth_bbox.x1)
        inter_y1 = max(bbox.y1, ground_truth_bbox.y1)
        inter_x2 = min(bbox.x2, ground_truth_bbox.x2)
        inter_y2 = min(bbox.y2, ground_truth_bbox.y2)

        inter_width = max(0, inter_x2 - inter_x1)
        inter_height = max(0, inter_y2 - inter_y1)
        total_intersection += inter_width * inter_height

    # Cap at GT area (in case of overlap overcounting)
    recall = min(total_intersection / ground_truth_bbox.area, 1.0)
    return recall


def compute_hit_rate(
    retrieved_regions: List[Union[OCRRegion, Dict[str, Any]]],
    ground_truth_bbox: Union[BoundingBox, List[float]],
    iou_threshold: float = 0.5,
) -> float:
    """
    Compute hit rate: 1 if any retrieved region overlaps GT, else 0.

    Args:
        retrieved_regions: List of retrieved regions
        ground_truth_bbox: Ground truth bounding box
        iou_threshold: Minimum IoU to consider a hit

    Returns:
        1.0 if hit, 0.0 otherwise
    """
    for region in retrieved_regions:
        if isinstance(region, OCRRegion):
            bbox = region.bbox
        else:
            bbox_data = region.get("bbox", [0, 0, 0, 0])
            bbox = BoundingBox.from_list(bbox_data) if isinstance(bbox_data, list) else bbox_data

        iou = compute_iou(bbox, ground_truth_bbox)
        if iou >= iou_threshold:
            return 1.0

    return 0.0


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string.

    Uses tiktoken for accurate token counting compatible with OpenAI models.

    Args:
        text: Text to count tokens for
        model: Model name for tokenizer selection

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def compute_context_efficiency(
    context_tokens: int,
    full_page_tokens: int,
) -> float:
    """
    Compute context efficiency: reduction ratio compared to full page.

    Args:
        context_tokens: Number of tokens in filtered context
        full_page_tokens: Number of tokens in full page

    Returns:
        Efficiency ratio (higher is better, 1.0 means no reduction)
    """
    if full_page_tokens <= 0:
        return 1.0
    return full_page_tokens / max(context_tokens, 1)


class MetricsAggregator:
    """Aggregates metrics across multiple samples."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "anls": [],
            "iou_at_1": [],
            "iou_at_k": [],
            "precision_at_5": [],
            "recall": [],
            "hit_rate": [],
            "context_tokens": [],
            "latency_ms": [],
        }

    def add(
        self,
        anls: float,
        iou_at_1: float,
        iou_at_k: float,
        precision_at_5: float,
        recall: float,
        hit_rate: float,
        context_tokens: int,
        latency_ms: float,
    ) -> None:
        """Add metrics for a single sample."""
        self.metrics["anls"].append(anls)
        self.metrics["iou_at_1"].append(iou_at_1)
        self.metrics["iou_at_k"].append(iou_at_k)
        self.metrics["precision_at_5"].append(precision_at_5)
        self.metrics["recall"].append(recall)
        self.metrics["hit_rate"].append(hit_rate)
        self.metrics["context_tokens"].append(context_tokens)
        self.metrics["latency_ms"].append(latency_ms)

    def aggregate(self) -> Dict[str, float]:
        """Compute aggregate statistics."""
        result = {}
        for key, values in self.metrics.items():
            if not values:
                result[f"{key}_mean"] = 0.0
                result[f"{key}_std"] = 0.0
                continue

            import numpy as np

            arr = np.array(values)
            result[f"{key}_mean"] = float(np.mean(arr))
            result[f"{key}_std"] = float(np.std(arr))

        result["n_samples"] = len(self.metrics["anls"])
        return result

    def to_dict(self) -> Dict[str, List[float]]:
        """Return raw metrics."""
        return self.metrics.copy()
