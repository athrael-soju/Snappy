"""
Main benchmark runner for evaluation.

Orchestrates the evaluation loop across all samples and conditions,
collecting metrics and generating results.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from eval.conditions import (
    CONDITION_BUILDERS,
    ContextBuilder,
    HybridContextBuilder,
    OCROnlyBM25ContextBuilder,
    OCROnlyDenseContextBuilder,
    PageOnlyContextBuilder,
)
from eval.dataset import BBoxDocVQADataset, Sample
from eval.metrics import (
    MetricsAggregator,
    compute_anls,
    compute_hit_rate,
    compute_iou_at_1,
    compute_iou_at_k,
    compute_precision_at_k,
    compute_recall,
    count_tokens,
)
from eval.scoring import RegionScorer

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""

    # Dataset settings
    dataset_path: Path = Path("data/bbox-docvqa")
    n_samples: Optional[int] = None  # None = all samples
    sample_seed: int = 42

    # Scoring settings
    colpali_url: str = "http://localhost:8001"
    aggregations: List[str] = field(default_factory=lambda: ["max", "mean", "sum"])
    thresholds: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    top_k: int = 5

    # LLM settings
    llm_model: str = "gpt-4o-mini"
    openai_api_key: Optional[str] = None

    # Conditions to evaluate
    conditions: List[str] = field(
        default_factory=lambda: ["hybrid", "page_only", "ocr_bm25"]
    )

    # Output settings
    output_dir: Path = Path("eval/results")
    save_per_sample: bool = True

    def __post_init__(self):
        self.dataset_path = Path(self.dataset_path)
        self.output_dir = Path(self.output_dir)


@dataclass
class SampleResult:
    """Results for a single sample evaluation."""

    sample_id: str
    condition: str
    aggregation: Optional[str]
    threshold: Optional[float]

    # Metrics
    anls: float
    iou_at_1: float
    iou_at_k: float
    precision_at_5: float
    recall: float
    hit_rate: float
    context_tokens: int
    latency_ms: float

    # Additional info
    prediction: str = ""
    ground_truth: str = ""
    n_retrieved_regions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "condition": self.condition,
            "aggregation": self.aggregation,
            "threshold": self.threshold,
            "anls": self.anls,
            "iou_at_1": self.iou_at_1,
            "iou_at_k": self.iou_at_k,
            "precision_at_5": self.precision_at_5,
            "recall": self.recall,
            "hit_rate": self.hit_rate,
            "context_tokens": self.context_tokens,
            "latency_ms": self.latency_ms,
            "prediction": self.prediction,
            "ground_truth": self.ground_truth,
            "n_retrieved_regions": self.n_retrieved_regions,
        }


class LLMClient:
    """Client for querying LLMs."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai package required for LLM queries")

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def query(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Query the LLM with a question and context.

        Args:
            question: The question to answer
            context: Retrieved context to use
            system_prompt: Optional system prompt

        Returns:
            Model's answer
        """
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Answer concisely and accurately. If the answer is not in the context, say 'I cannot find the answer in the provided context.'"
            )

        user_message = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=256,
            temperature=0,
        )

        return response.choices[0].message.content.strip()


class Benchmark:
    """
    Main benchmark runner.

    Evaluates the patch-to-region relevance propagation method
    across multiple conditions and parameter settings.
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.scorer = RegionScorer(colpali_url=config.colpali_url)
        self.llm = LLMClient(model=config.llm_model, api_key=config.openai_api_key)
        self.dataset: Optional[BBoxDocVQADataset] = None
        self.samples: List[Sample] = []

    def load_dataset(self) -> None:
        """Load the evaluation dataset."""
        logger.info(f"Loading dataset from {self.config.dataset_path}")
        self.dataset = BBoxDocVQADataset(self.config.dataset_path)
        self.dataset.load()

        if self.config.n_samples:
            self.samples = self.dataset.sample(
                self.config.n_samples, seed=self.config.sample_seed
            )
            logger.info(f"Sampled {len(self.samples)} samples")
        else:
            self.samples = list(self.dataset)
            logger.info(f"Using all {len(self.samples)} samples")

    async def evaluate_sample_hybrid(
        self,
        sample: Sample,
        aggregation: str,
        threshold: float,
    ) -> SampleResult:
        """Evaluate a single sample with hybrid condition."""
        start_time = time.time()

        # Get scored regions from ColPali
        try:
            scored_regions = await self.scorer.score_sample(
                sample,
                threshold=threshold,
                top_k=self.config.top_k,
                aggregation=aggregation,
            )
        except Exception as e:
            logger.error(f"Failed to score sample {sample.sample_id}: {e}")
            scored_regions = []

        # Build context
        builder = HybridContextBuilder(top_k=self.config.top_k)
        context = builder.build_context(sample, sample.question, scored_regions)
        retrieved_regions = builder.get_retrieved_regions(
            sample, sample.question, scored_regions
        )

        # Query LLM
        try:
            prediction = self.llm.query(sample.question, context)
        except Exception as e:
            logger.error(f"LLM query failed for sample {sample.sample_id}: {e}")
            prediction = ""

        latency_ms = (time.time() - start_time) * 1000

        # Compute metrics
        anls = compute_anls(prediction, sample.answer)
        iou_1 = compute_iou_at_1(retrieved_regions, sample.ground_truth_bbox)
        iou_k = compute_iou_at_k(
            retrieved_regions, sample.ground_truth_bbox, k=self.config.top_k
        )
        precision = compute_precision_at_k(
            retrieved_regions, sample.ground_truth_bbox, k=5
        )
        recall = compute_recall(retrieved_regions, sample.ground_truth_bbox)
        hit = compute_hit_rate(retrieved_regions, sample.ground_truth_bbox)
        tokens = count_tokens(context)

        return SampleResult(
            sample_id=sample.sample_id,
            condition="hybrid",
            aggregation=aggregation,
            threshold=threshold,
            anls=anls,
            iou_at_1=iou_1,
            iou_at_k=iou_k,
            precision_at_5=precision,
            recall=recall,
            hit_rate=hit,
            context_tokens=tokens,
            latency_ms=latency_ms,
            prediction=prediction,
            ground_truth=sample.answer,
            n_retrieved_regions=len(retrieved_regions),
        )

    def evaluate_sample_baseline(
        self,
        sample: Sample,
        condition: str,
    ) -> SampleResult:
        """Evaluate a single sample with a baseline condition."""
        start_time = time.time()

        # Get appropriate builder
        if condition == "page_only":
            builder = PageOnlyContextBuilder()
        elif condition == "ocr_bm25":
            builder = OCROnlyBM25ContextBuilder(top_k=self.config.top_k)
        elif condition == "ocr_dense":
            builder = OCROnlyDenseContextBuilder(
                top_k=self.config.top_k,
                openai_api_key=self.config.openai_api_key,
            )
        else:
            raise ValueError(f"Unknown condition: {condition}")

        # Build context
        context = builder.build_context(sample, sample.question)
        retrieved_regions = builder.get_retrieved_regions(sample, sample.question)

        # Query LLM
        try:
            prediction = self.llm.query(sample.question, context)
        except Exception as e:
            logger.error(f"LLM query failed for sample {sample.sample_id}: {e}")
            prediction = ""

        latency_ms = (time.time() - start_time) * 1000

        # Compute metrics
        anls = compute_anls(prediction, sample.answer)
        tokens = count_tokens(context)

        # Spatial metrics (not applicable for page_only)
        if condition == "page_only":
            iou_1, iou_k, precision, recall, hit = 0.0, 0.0, 0.0, 0.0, 0.0
        else:
            iou_1 = compute_iou_at_1(retrieved_regions, sample.ground_truth_bbox)
            iou_k = compute_iou_at_k(
                retrieved_regions, sample.ground_truth_bbox, k=self.config.top_k
            )
            precision = compute_precision_at_k(
                retrieved_regions, sample.ground_truth_bbox, k=5
            )
            recall = compute_recall(retrieved_regions, sample.ground_truth_bbox)
            hit = compute_hit_rate(retrieved_regions, sample.ground_truth_bbox)

        return SampleResult(
            sample_id=sample.sample_id,
            condition=condition,
            aggregation=None,
            threshold=None,
            anls=anls,
            iou_at_1=iou_1,
            iou_at_k=iou_k,
            precision_at_5=precision,
            recall=recall,
            hit_rate=hit,
            context_tokens=tokens,
            latency_ms=latency_ms,
            prediction=prediction,
            ground_truth=sample.answer,
            n_retrieved_regions=len(retrieved_regions),
        )

    async def run(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full benchmark.

        Args:
            progress_callback: Optional callback(current, total, message)

        Returns:
            Dictionary with aggregated results
        """
        if not self.samples:
            self.load_dataset()

        all_results: List[SampleResult] = []
        total_evaluations = self._count_total_evaluations()
        current = 0

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Run hybrid conditions
        if "hybrid" in self.config.conditions:
            for aggregation in self.config.aggregations:
                for threshold in self.config.thresholds:
                    for sample in self.samples:
                        current += 1
                        if progress_callback:
                            progress_callback(
                                current,
                                total_evaluations,
                                f"Hybrid ({aggregation}, t={threshold}): {sample.sample_id}",
                            )

                        result = await self.evaluate_sample_hybrid(
                            sample, aggregation, threshold
                        )
                        all_results.append(result)

        # Run baseline conditions
        for condition in self.config.conditions:
            if condition == "hybrid":
                continue

            for sample in self.samples:
                current += 1
                if progress_callback:
                    progress_callback(
                        current,
                        total_evaluations,
                        f"{condition}: {sample.sample_id}",
                    )

                result = self.evaluate_sample_baseline(sample, condition)
                all_results.append(result)

        # Close scorer session
        await self.scorer.close()

        # Aggregate results
        aggregated = self._aggregate_results(all_results)

        # Save results
        self._save_results(all_results, aggregated)

        return aggregated

    def _count_total_evaluations(self) -> int:
        """Count total number of evaluations to run."""
        count = 0
        n_samples = len(self.samples)

        if "hybrid" in self.config.conditions:
            count += (
                n_samples
                * len(self.config.aggregations)
                * len(self.config.thresholds)
            )

        # Baseline conditions
        count += n_samples * (len(self.config.conditions) - (1 if "hybrid" in self.config.conditions else 0))

        return count

    def _aggregate_results(
        self, results: List[SampleResult]
    ) -> Dict[str, Any]:
        """Aggregate results by condition."""
        import numpy as np

        aggregated = {}

        # Group by condition key
        groups: Dict[str, List[SampleResult]] = {}
        for result in results:
            if result.condition == "hybrid":
                key = f"hybrid_{result.aggregation}_t{result.threshold}"
            else:
                key = result.condition
            groups.setdefault(key, []).append(result)

        # Compute statistics for each group
        for key, group_results in groups.items():
            metrics = {
                "anls": [r.anls for r in group_results],
                "iou_at_1": [r.iou_at_1 for r in group_results],
                "iou_at_k": [r.iou_at_k for r in group_results],
                "precision_at_5": [r.precision_at_5 for r in group_results],
                "recall": [r.recall for r in group_results],
                "hit_rate": [r.hit_rate for r in group_results],
                "context_tokens": [r.context_tokens for r in group_results],
                "latency_ms": [r.latency_ms for r in group_results],
            }

            aggregated[key] = {
                "n_samples": len(group_results),
            }

            for metric_name, values in metrics.items():
                arr = np.array(values)
                aggregated[key][f"{metric_name}_mean"] = float(np.mean(arr))
                aggregated[key][f"{metric_name}_std"] = float(np.std(arr))
                aggregated[key][f"{metric_name}_median"] = float(np.median(arr))

        return aggregated

    def _save_results(
        self,
        results: List[SampleResult],
        aggregated: Dict[str, Any],
    ) -> None:
        """Save results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save aggregated results
        agg_path = self.config.output_dir / f"aggregated_{timestamp}.json"
        with open(agg_path, "w") as f:
            json.dump(aggregated, f, indent=2)
        logger.info(f"Saved aggregated results to {agg_path}")

        # Save per-sample results
        if self.config.save_per_sample:
            samples_path = self.config.output_dir / f"samples_{timestamp}.json"
            with open(samples_path, "w") as f:
                json.dump([r.to_dict() for r in results], f, indent=2)
            logger.info(f"Saved per-sample results to {samples_path}")

        # Save as CSV for easy analysis
        csv_path = self.config.output_dir / f"results_{timestamp}.csv"
        self._save_csv(results, csv_path)
        logger.info(f"Saved CSV results to {csv_path}")

    def _save_csv(self, results: List[SampleResult], path: Path) -> None:
        """Save results as CSV."""
        import csv

        fieldnames = [
            "sample_id",
            "condition",
            "aggregation",
            "threshold",
            "anls",
            "iou_at_1",
            "iou_at_k",
            "precision_at_5",
            "recall",
            "hit_rate",
            "context_tokens",
            "latency_ms",
            "n_retrieved_regions",
        ]

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for result in results:
                writer.writerow(result.to_dict())


async def run_benchmark(
    config: Optional[BenchmarkConfig] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to run a benchmark.

    Args:
        config: Benchmark configuration (or pass kwargs)
        **kwargs: Override config values

    Returns:
        Aggregated results
    """
    if config is None:
        config = BenchmarkConfig(**kwargs)
    else:
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    benchmark = Benchmark(config)

    def progress(current: int, total: int, message: str) -> None:
        pct = current / total * 100
        logger.info(f"[{pct:.1f}%] {message}")

    return await benchmark.run(progress_callback=progress)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run evaluation benchmark")
    parser.add_argument(
        "--dataset",
        type=Path,
        default="data/bbox-docvqa",
        help="Path to dataset",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=None,
        help="Number of samples to evaluate (default: all)",
    )
    parser.add_argument(
        "--colpali-url",
        type=str,
        default="http://localhost:8001",
        help="ColPali service URL",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model for answer generation",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="eval/results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["hybrid", "page_only", "ocr_bm25"],
        help="Conditions to evaluate",
    )
    parser.add_argument(
        "--aggregations",
        nargs="+",
        default=["max", "mean", "sum"],
        help="Aggregation methods for hybrid condition",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top regions to retrieve",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = BenchmarkConfig(
        dataset_path=args.dataset,
        n_samples=args.n_samples,
        colpali_url=args.colpali_url,
        llm_model=args.llm_model,
        output_dir=args.output_dir,
        conditions=args.conditions,
        aggregations=args.aggregations,
        top_k=args.top_k,
    )

    results = asyncio.run(run_benchmark(config))

    # Print summary table
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    headers = ["Condition", "ANLS", "IoU@1", "IoU@k", "P@5", "Recall", "Tokens"]
    row_format = "{:<30} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}"

    print(row_format.format(*headers))
    print("-" * 80)

    for key, metrics in sorted(results.items()):
        print(
            row_format.format(
                key,
                f"{metrics['anls_mean']:.3f}",
                f"{metrics['iou_at_1_mean']:.3f}",
                f"{metrics['iou_at_k_mean']:.3f}",
                f"{metrics['precision_at_5_mean']:.3f}",
                f"{metrics['recall_mean']:.3f}",
                f"{metrics['context_tokens_mean']:.0f}",
            )
        )


if __name__ == "__main__":
    main()
