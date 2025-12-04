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

    def to_dict(self) -> Dict[str, float]:
        return {
            "exact_match": self.exact_match,
            "f1_score": self.f1_score,
            "anls": self.anls,
            "semantic_similarity": self.semantic_similarity,
            "bbox_iou": self.bbox_iou,
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
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        anls_threshold: float = 0.5,
    ):
        """
        Initialize correctness evaluator.

        Args:
            use_semantic_similarity: Whether to compute embedding-based similarity
            embedding_model: Model for semantic similarity
            anls_threshold: Threshold for ANLS scoring
        """
        self.use_semantic_similarity = use_semantic_similarity
        self.embedding_model = embedding_model
        self.anls_threshold = anls_threshold

        self._embedder = None

        if use_semantic_similarity:
            self._initialize_embedder()

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

    def _compute_semantic_similarity(
        self, prediction: str, ground_truth: str
    ) -> float:
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
            pred_bboxes = (
                predicted_bboxes_list[i] if predicted_bboxes_list else None
            )
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
    LLM-based answer evaluation.

    Uses an LLM to judge answer correctness for cases where
    lexical metrics may not capture semantic equivalence.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key
        self._session = None

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
            Score from 0.0 to 1.0
        """
        import requests

        if not self.api_key:
            return 0.0

        prompt = f"""You are an expert evaluator for document question answering.

Given a question and two answers, judge if the predicted answer is correct.

Question: {question}

Ground Truth Answer: {ground_truth}

Predicted Answer: {prediction}

Is the predicted answer correct? Consider semantic equivalence, not just exact match.
Respond with a score from 0 to 100, where:
- 100 = Completely correct
- 75 = Mostly correct with minor differences
- 50 = Partially correct
- 25 = Mostly incorrect
- 0 = Completely incorrect

Score:"""

        try:
            if self._session is None:
                self._session = requests.Session()

            response = self._session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 10,
                },
                timeout=30,
            )

            if response.status_code != 200:
                return 0.0

            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()

            # Parse score
            import re

            match = re.search(r"\d+", answer)
            if match:
                score = int(match.group()) / 100.0
                return min(max(score, 0.0), 1.0)

        except Exception as e:
            logger.warning(f"LLM judge failed: {e}")

        return 0.0
