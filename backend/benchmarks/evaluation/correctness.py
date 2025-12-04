"""
Correctness evaluation for benchmark answers.

Implements:
- F1 Score: Token-level overlap
- LLM Judge: Semantic correctness via LLM evaluation
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from openai import OpenAI

from benchmarks.metrics import (
    compute_f1_score,
    compute_bbox_iou,
)

logger = logging.getLogger(__name__)


@dataclass
class CorrectnessResult:
    """Result of correctness evaluation."""

    f1_score: float
    bbox_iou: float
    llm_judge_correct: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "f1_score": self.f1_score,
            "bbox_iou": self.bbox_iou,
            "llm_judge_correct": self.llm_judge_correct,
        }


class CorrectnessEvaluator:
    """
    Evaluator for answer correctness.

    Computes:
    - F1 Score: Token-level overlap
    - LLM Judge: Semantic correctness via LLM evaluation
    - BBox IoU: Spatial accuracy
    """

    def __init__(
        self,
        use_llm_judge: bool = False,
        llm_model: str = "gpt-5-nano",
        llm_api_key: str = "",
    ):
        """
        Initialize correctness evaluator.

        Args:
            use_llm_judge: Whether to use LLM for semantic correctness evaluation
            llm_model: Model for LLM judge
            llm_api_key: API key for LLM judge (required if use_llm_judge is True)
        """
        self.use_llm_judge = use_llm_judge
        self._llm_judge = None

        if use_llm_judge:
            if not llm_api_key:
                raise ValueError("llm_api_key is required when use_llm_judge is True")
            self._llm_judge = LLMJudge(model=llm_model, api_key=llm_api_key)

    def evaluate(
        self,
        prediction: str,
        ground_truth: str,
        predicted_bboxes: Optional[List[List[int]]] = None,
        ground_truth_bboxes: Optional[List[List[int]]] = None,
    ) -> CorrectnessResult:
        """
        Evaluate answer correctness.

        Args:
            prediction: Model-generated answer
            ground_truth: Ground truth answer
            predicted_bboxes: Optional predicted bounding boxes
            ground_truth_bboxes: Optional ground truth bounding boxes

        Returns:
            CorrectnessResult with metrics
        """
        # F1 score
        f1_score = compute_f1_score(prediction, ground_truth)

        # Bounding box IoU
        bbox_iou = 0.0
        if predicted_bboxes and ground_truth_bboxes:
            bbox_iou = compute_bbox_iou(predicted_bboxes, ground_truth_bboxes)

        return CorrectnessResult(
            f1_score=f1_score,
            bbox_iou=bbox_iou,
        )

    async def evaluate_async(
        self,
        question: str,
        prediction: str,
        ground_truth: str,
        predicted_bboxes: Optional[List[List[int]]] = None,
        ground_truth_bboxes: Optional[List[List[int]]] = None,
    ) -> CorrectnessResult:
        """
        Evaluate answer correctness with async LLM judge support.

        Args:
            question: Original question (needed for LLM judge context)
            prediction: Model-generated answer
            ground_truth: Ground truth answer
            predicted_bboxes: Optional predicted bounding boxes
            ground_truth_bboxes: Optional ground truth bounding boxes

        Returns:
            CorrectnessResult with all metrics including LLM judge score
        """
        # Get base metrics from sync method
        result = self.evaluate(prediction, ground_truth, predicted_bboxes, ground_truth_bboxes)

        # Add LLM judge result if enabled
        if self.use_llm_judge and self._llm_judge:
            result.llm_judge_correct = await self._llm_judge.judge(question, prediction, ground_truth)

        return result

    def batch_evaluate(
        self,
        predictions: List[str],
        ground_truths: List[str],
        predicted_bboxes_list: Optional[List[List[List[int]]]] = None,
        ground_truth_bboxes_list: Optional[List[List[List[int]]]] = None,
    ) -> List[CorrectnessResult]:
        """
        Evaluate multiple predictions.

        Args:
            predictions: List of model predictions
            ground_truths: List of ground truth answers
            predicted_bboxes_list: Optional list of predicted bboxes per sample
            ground_truth_bboxes_list: Optional list of ground truth bboxes per sample

        Returns:
            List of CorrectnessResult objects
        """
        results = []

        for i in range(len(predictions)):
            pred_bboxes = predicted_bboxes_list[i] if predicted_bboxes_list else None
            gt_bboxes = (
                ground_truth_bboxes_list[i] if ground_truth_bboxes_list else None
            )

            result = self.evaluate(
                predictions[i],
                ground_truths[i],
                pred_bboxes,
                gt_bboxes,
            )
            results.append(result)

        return results

    def aggregate_results(
        self, results: List[CorrectnessResult]
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate results across multiple samples.

        Args:
            results: List of CorrectnessResult objects

        Returns:
            Dictionary with aggregate statistics
        """
        if not results:
            return {}

        # Aggregate float metrics
        float_metrics = {
            "f1_score": [r.f1_score for r in results],
            "bbox_iou": [r.bbox_iou for r in results],
        }

        aggregated = {}
        for name, values in float_metrics.items():
            valid_values = [v for v in values if v > 0]
            if valid_values:
                aggregated[name] = {
                    "mean": float(np.mean(valid_values)),
                    "std": float(np.std(valid_values)),
                    "min": float(np.min(valid_values)),
                    "max": float(np.max(valid_values)),
                    "count": len(valid_values),
                }

        # Aggregate LLM judge (boolean -> accuracy)
        correct_count = sum(1 for r in results if r.llm_judge_correct)
        aggregated["llm_judge"] = {
            "correct": correct_count,
            "total": len(results),
            "accuracy": correct_count / len(results),
        }

        return aggregated


class LLMJudge:
    """
    LLM-based answer evaluation using structured outputs.

    Uses an LLM to judge answer correctness with a simple boolean output.
    """

    def __init__(
        self,
        model: str = "gpt-5-nano",
        api_key: str = "",
    ):
        if not api_key:
            raise ValueError("OpenAI API key is required for LLM judge")

        self.model = model
        self._openai_client = OpenAI(api_key=api_key)

    async def judge(
        self,
        question: str,
        prediction: str,
        ground_truth: str,
    ) -> bool:
        """
        Use LLM to judge answer correctness.

        Args:
            question: Original question
            prediction: Model prediction
            ground_truth: Ground truth answer

        Returns:
            True if correct, False if incorrect
        """
        import asyncio
        import json

        prompt = f"""Judge if the predicted answer is semantically correct compared to the ground truth.

Question: {question}
Ground Truth: {ground_truth}
Predicted: {prediction}

Is the predicted answer correct? Consider semantic equivalence, not exact match."""

        response = await asyncio.to_thread(
            self._openai_client.responses.create,
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "judge_result",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "correct": {"type": "boolean"}
                        },
                        "required": ["correct"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
            reasoning={"effort": "low"},
        )

        result = json.loads(response.output_text)
        is_correct = result["correct"]
        logger.info(f"LLM judge: correct={is_correct}")
        return is_correct
