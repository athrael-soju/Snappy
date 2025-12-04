"""
Correctness evaluation for benchmark answers.

Implements multiple metrics:
- Exact Match (EM): Normalized string comparison
- F1 Score: Token-level overlap
- ANLS: Average Normalized Levenshtein Similarity (DocVQA standard)
- Semantic Similarity: Embedding-based similarity
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from openai import OpenAI

from benchmarks.metrics import (
    compute_anls,
    compute_exact_match,
    compute_f1_score,
    compute_bbox_iou,
)

logger = logging.getLogger(__name__)


@dataclass
class CorrectnessResult:
    """Result of correctness evaluation."""

    exact_match: float
    f1_score: float
    anls: float
    semantic_similarity: float
    bbox_iou: float
    llm_judge_score: float = 0.0  # LLM-based semantic correctness

    def to_dict(self) -> Dict[str, float]:
        return {
            "exact_match": self.exact_match,
            "f1_score": self.f1_score,
            "anls": self.anls,
            "semantic_similarity": self.semantic_similarity,
            "bbox_iou": self.bbox_iou,
            "llm_judge_score": self.llm_judge_score,
        }


class CorrectnessEvaluator:
    """
    Evaluator for answer correctness.

    Computes multiple metrics to assess answer quality:
    - Lexical metrics (EM, F1)
    - Edit distance metrics (ANLS)
    - Semantic metrics (embedding similarity)
    - Spatial metrics (bounding box IoU)
    """

    def __init__(
        self,
        use_semantic_similarity: bool = False,
        use_llm_judge: bool = False,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        anls_threshold: float = 0.5,
        llm_model: str = "gpt-5-nano",
        llm_api_key: Optional[str] = None,
    ):
        """
        Initialize correctness evaluator.

        Args:
            use_semantic_similarity: Whether to compute embedding-based similarity
            use_llm_judge: Whether to use LLM for semantic correctness evaluation
            embedding_model: Model for semantic similarity
            anls_threshold: Threshold for ANLS scoring
            llm_model: Model for LLM judge
            llm_api_key: API key for LLM judge
        """
        self.use_semantic_similarity = use_semantic_similarity
        self.use_llm_judge = use_llm_judge
        self.embedding_model = embedding_model
        self.anls_threshold = anls_threshold

        self._embedder = None
        self._llm_judge = None

        if use_semantic_similarity:
            self._initialize_embedder()

        if use_llm_judge:
            self._llm_judge = LLMJudge(model=llm_model, api_key=llm_api_key)

    def _initialize_embedder(self) -> None:
        """Initialize sentence transformer for semantic similarity."""
        try:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(self.embedding_model)
            logger.info(f"Loaded embedding model: {self.embedding_model}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Semantic similarity will be disabled."
            )
            self.use_semantic_similarity = False

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
            CorrectnessResult with all metrics
        """
        # Lexical metrics
        exact_match = compute_exact_match(prediction, ground_truth)
        f1_score = compute_f1_score(prediction, ground_truth)

        # Edit distance metric
        anls = compute_anls(prediction, ground_truth, self.anls_threshold)

        # Semantic similarity
        semantic_sim = 0.0
        if self.use_semantic_similarity and self._embedder:
            semantic_sim = self._compute_semantic_similarity(prediction, ground_truth)

        # Bounding box IoU
        bbox_iou = 0.0
        if predicted_bboxes and ground_truth_bboxes:
            bbox_iou = compute_bbox_iou(predicted_bboxes, ground_truth_bboxes)

        return CorrectnessResult(
            exact_match=exact_match,
            f1_score=f1_score,
            anls=anls,
            semantic_similarity=semantic_sim,
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

        # Add LLM judge score if enabled
        if self.use_llm_judge and self._llm_judge:
            llm_score = await self._llm_judge.judge(question, prediction, ground_truth)
            result.llm_judge_score = llm_score

        return result

    def _compute_semantic_similarity(self, prediction: str, ground_truth: str) -> float:
        """Compute cosine similarity between embeddings."""
        if not self._embedder:
            return 0.0

        try:
            embeddings = self._embedder.encode(
                [prediction, ground_truth],
                convert_to_numpy=True,
            )

            # Cosine similarity
            pred_emb = embeddings[0]
            gt_emb = embeddings[1]

            similarity = np.dot(pred_emb, gt_emb) / (
                np.linalg.norm(pred_emb) * np.linalg.norm(gt_emb) + 1e-8
            )

            return float(similarity)

        except Exception as e:
            logger.warning(f"Semantic similarity computation failed: {e}")
            return 0.0

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

        metrics = {
            "exact_match": [r.exact_match for r in results],
            "f1_score": [r.f1_score for r in results],
            "anls": [r.anls for r in results],
            "semantic_similarity": [r.semantic_similarity for r in results],
            "bbox_iou": [r.bbox_iou for r in results],
        }

        aggregated = {}
        for name, values in metrics.items():
            valid_values = [v for v in values if v > 0 or name in ["exact_match"]]
            if valid_values:
                aggregated[name] = {
                    "mean": float(np.mean(valid_values)),
                    "std": float(np.std(valid_values)),
                    "min": float(np.min(valid_values)),
                    "max": float(np.max(valid_values)),
                    "count": len(valid_values),
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
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key
        self._openai_client = OpenAI(api_key=api_key) if api_key else None

    async def judge(
        self,
        question: str,
        prediction: str,
        ground_truth: str,
    ) -> float:
        """
        Use LLM to judge answer correctness.

        Args:
            question: Original question
            prediction: Model prediction
            ground_truth: Ground truth answer

        Returns:
            1.0 if correct, 0.0 if incorrect
        """
        if not self._openai_client:
            logger.warning("LLM judge: no OpenAI client (missing API key?)")
            return 0.0

        prompt = f"""Judge if the predicted answer is semantically correct compared to the ground truth.

Question: {question}
Ground Truth: {ground_truth}
Predicted: {prediction}

Is the predicted answer correct? Consider semantic equivalence, not exact match."""

        try:
            import asyncio

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

            import json
            result = json.loads(response.output_text)
            is_correct = result.get("correct", False)
            logger.info(f"LLM judge: correct={is_correct}")
            return 1.0 if is_correct else 0.0

        except Exception as e:
            logger.warning(f"LLM judge failed: {e}", exc_info=True)

        return 0.0
