"""
Metric helpers for spatial grounding benchmarks.

The functions here are intentionally dependency-light to keep the benchmark
runner easy to execute in constrained environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

Box = Tuple[float, float, float, float]


def compute_iou(box_a: Box, box_b: Box) -> float:
    """Compute IoU between two axis-aligned bounding boxes.

    Args:
        box_a: (x1, y1, x2, y2)
        box_b: (x1, y1, x2, y2)
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    intersection = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return float(intersection / union)


@dataclass
class SampleMetrics:
    """Per-sample evaluation summary."""

    mean_iou: float
    max_ious: List[float]

    @property
    def iou_at_0_5(self) -> float:
        """Binary success at IoU >= 0.5."""
        if not self.max_ious:
            return 0.0
        return float(np.mean([1.0 if i >= 0.5 else 0.0 for i in self.max_ious]))


def evaluate_boxes(pred_boxes: Sequence[Box], gt_boxes: Sequence[Box]) -> SampleMetrics:
    """Evaluate predicted boxes against ground-truth boxes using per-GT max IoU."""
    if not gt_boxes:
        return SampleMetrics(mean_iou=0.0, max_ious=[])

    max_ious: List[float] = []
    for gt in gt_boxes:
        if pred_boxes:
            max_iou = max(compute_iou(pred, gt) for pred in pred_boxes)
        else:
            max_iou = 0.0
        max_ious.append(max_iou)

    return SampleMetrics(mean_iou=float(np.mean(max_ious)), max_ious=max_ious)


def summarize_samples(samples: Iterable[SampleMetrics]) -> dict[str, float]:
    """Aggregate sample metrics into a dataset-level summary."""
    metrics = list(samples)
    if not metrics:
        return {"mean_iou": 0.0, "iou_at_0_5": 0.0, "num_samples": 0}

    mean_iou = float(np.mean([m.mean_iou for m in metrics]))
    iou_at_0_5 = float(np.mean([m.iou_at_0_5 for m in metrics]))
    return {
        "mean_iou": mean_iou,
        "iou_at_0_5": iou_at_0_5,
        "num_samples": len(metrics),
    }
