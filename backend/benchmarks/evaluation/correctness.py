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

from benchmarks.llm import LLMClient
from benchmarks.metrics import compute_f1_score

logger = logging.getLogger(__name__)


@dataclass
class CorrectnessResult:
    """Result of correctness evaluation."""

    f1_score: float
    llm_judge_correct: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "f1_score": self.f1_score,
            "llm_judge_correct": self.llm_judge_correct,
        }


class CorrectnessEvaluator:
    """
    Evaluator for answer correctness.

    Computes:
    - F1 Score: Token-level overlap
    - LLM Judge: Semantic correctness via LLM evaluation
    """

    def __init__(
        self,
        use_llm_judge: bool = False,
        llm_model: str = "gpt-5-mini",
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
    ) -> CorrectnessResult:
        """
        Evaluate answer correctness.

        Args:
            prediction: Model-generated answer
            ground_truth: Ground truth answer

        Returns:
            CorrectnessResult with metrics
        """
        f1_score = compute_f1_score(prediction, ground_truth)
        return CorrectnessResult(f1_score=f1_score)

    async def evaluate_async(
        self,
        question: str,
        prediction: str,
        ground_truth: str,
    ) -> CorrectnessResult:
        """
        Evaluate answer correctness with async LLM judge support.

        Args:
            question: Original question (needed for LLM judge context)
            prediction: Model-generated answer
            ground_truth: Ground truth answer

        Returns:
            CorrectnessResult with all metrics including LLM judge score
        """
        # Get base metrics from sync method
        result = self.evaluate(prediction, ground_truth)

        # Add LLM judge result if enabled
        if self.use_llm_judge and self._llm_judge:
            result.llm_judge_correct = await self._llm_judge.judge(question, prediction, ground_truth)

        return result

    def batch_evaluate(
        self,
        predictions: List[str],
        ground_truths: List[str],
    ) -> List[CorrectnessResult]:
        """
        Evaluate multiple predictions.

        Args:
            predictions: List of model predictions
            ground_truths: List of ground truth answers

        Returns:
            List of CorrectnessResult objects
        """
        return [
            self.evaluate(pred, gt)
            for pred, gt in zip(predictions, ground_truths)
        ]

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

        # Aggregate F1 scores
        f1_values = [r.f1_score for r in results if r.f1_score > 0]
        aggregated = {}
        if f1_values:
            aggregated["f1_score"] = {
                "mean": float(np.mean(f1_values)),
                "std": float(np.std(f1_values)),
                "min": float(np.min(f1_values)),
                "max": float(np.max(f1_values)),
                "count": len(f1_values),
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

    # JSON schema for structured output
    JUDGE_SCHEMA = {
        "type": "object",
        "properties": {"correct": {"type": "boolean"}},
        "required": ["correct"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        model: str = "gpt-5-mini",
        api_key: str = "",
    ):
        if not api_key:
            raise ValueError("OpenAI API key is required for LLM judge")

        self.model = model
        self._llm_client = LLMClient(api_key=api_key, model=model)

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
        prompt = f"""Judge if the predicted answer is semantically correct compared to the ground truth.

Question: {question}
Ground Truth: {ground_truth}
Predicted: {prediction}

Is the predicted answer correct? Consider semantic equivalence, not exact match."""

        result = await self._llm_client.generate_structured(
            prompt=prompt,
            schema=self.JUDGE_SCHEMA,
            schema_name="judge_result",
            reasoning_effort="low",
        )

        is_correct = result["correct"]
        logger.info(f"LLM judge: correct={is_correct}")
        return is_correct
