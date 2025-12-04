"""
Main benchmark runner.

Orchestrates the entire benchmarking process:
1. Load dataset
2. Initialize strategies
3. Run retrieval and RAG evaluation
4. Collect metrics
5. Generate reports
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Type

from benchmarks.config import BenchmarkConfig, RetrievalStrategy
from benchmarks.dataset import BBoxDocVQADataset, BenchmarkSample
from benchmarks.evaluation.correctness import CorrectnessEvaluator
from benchmarks.evaluation.rag_evaluator import RAGEvaluator
from benchmarks.metrics import (
    CorrectnessMetrics,
    LatencyMetrics,
    MetricsCollector,
    RetrievalMetrics,
    SampleResult,
    TokenMetrics,
)
from benchmarks.reports.generator import ReportGenerator
from benchmarks.strategies.base import BaseRetrievalStrategy
from benchmarks.strategies.colpali_only import ColPaliOnlyStrategy
from benchmarks.strategies.ocr_only import OCROnlyStrategy
from benchmarks.strategies.snappy_full import SnappyFullStrategy

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Main benchmark runner for comparing document retrieval strategies.
    """

    STRATEGY_MAP: Dict[RetrievalStrategy, Type[BaseRetrievalStrategy]] = {
        RetrievalStrategy.SNAPPY_FULL: SnappyFullStrategy,
        RetrievalStrategy.COLPALI_ONLY: ColPaliOnlyStrategy,
        RetrievalStrategy.OCR_ONLY: OCROnlyStrategy,
    }

    def __init__(self, config: BenchmarkConfig):
        """
        Initialize benchmark runner.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        config.validate()

        self._dataset: Optional[BBoxDocVQADataset] = None
        self._strategies: Dict[str, BaseRetrievalStrategy] = {}
        self._rag_evaluator: Optional[RAGEvaluator] = None
        self._correctness_evaluator: Optional[CorrectnessEvaluator] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._report_generator: Optional[ReportGenerator] = None

        self._logger = logging.getLogger(__name__)

    async def setup(self) -> None:
        """Set up all components for benchmarking."""
        self._logger.info("Setting up benchmark runner...")

        # Load dataset
        self._dataset = BBoxDocVQADataset(
            dataset_name=self.config.dataset_name,
            cache_dir=self.config.cache_dir,
        )
        self._dataset.load(
            split=self.config.dataset_split,
            max_samples=self.config.max_samples,
            categories=self.config.categories,
        )

        stats = self._dataset.get_statistics()
        self._logger.info(f"Dataset loaded: {stats}")

        # Initialize strategies
        for strategy_type in self.config.strategies:
            strategy_class = self.STRATEGY_MAP.get(strategy_type)
            if strategy_class:
                strategy = strategy_class(
                    colpali_url=self.config.colpali_url,
                    qdrant_url=self.config.qdrant_url,
                    duckdb_url=self.config.duckdb_url,
                    minio_url=self.config.minio_url,
                    region_relevance_threshold=self.config.region_relevance_threshold,
                    region_top_k=self.config.region_top_k,
                    region_score_aggregation=self.config.region_score_aggregation,
                    image_cache_dir=self.config.cache_dir,
                )
                await strategy.initialize()
                self._strategies[strategy.name] = strategy
                self._logger.info(f"Initialized strategy: {strategy.name}")

        # Initialize evaluators
        self._rag_evaluator = RAGEvaluator(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            api_key=self.config.llm_api_key,
            anthropic_api_key=self.config.anthropic_api_key,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        )

        self._correctness_evaluator = CorrectnessEvaluator(
            use_semantic_similarity=False,  # Skip for speed
        )

        # Initialize collectors and reporters
        self._metrics_collector = MetricsCollector()
        self._report_generator = ReportGenerator(output_dir=self.config.output_dir)

        self._logger.info("Benchmark runner setup complete")

    async def run(self) -> Dict[str, Any]:
        """
        Run the full benchmark.

        Returns:
            Dictionary with benchmark results
        """
        if not self._dataset or not self._strategies:
            await self.setup()

        self._logger.info(
            f"Starting benchmark with {len(self._dataset)} samples "
            f"and {len(self._strategies)} strategies"
        )

        total_start = time.perf_counter()

        # Run each strategy
        for strategy_name, strategy in self._strategies.items():
            self._logger.info(f"Running strategy: {strategy_name}")
            await self._run_strategy(strategy)

        total_time = time.perf_counter() - total_start
        self._logger.info(f"Benchmark completed in {total_time:.1f}s")

        # Generate reports
        results = {
            "comparison": self._metrics_collector.compare_strategies(),
            "total_time_seconds": total_time,
        }

        if self.config.generate_report:
            report_paths = self._report_generator.generate_full_report(
                self._metrics_collector,
                self._get_config_dict(),
            )
            results["report_paths"] = report_paths

        return results

    async def _run_strategy(self, strategy: BaseRetrievalStrategy) -> None:
        """
        Run benchmark for a single strategy.

        Args:
            strategy: Strategy to benchmark
        """
        samples = list(self._dataset)

        # Process in batches
        for i in range(0, len(samples), self.config.batch_size):
            batch = samples[i : i + self.config.batch_size]

            # Process samples concurrently within batch
            tasks = [
                self._process_sample(strategy, sample)
                for sample in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self._logger.error(f"Sample processing failed: {result}")
                elif result:
                    self._metrics_collector.add_result(result)

            # Log progress
            processed = min(i + self.config.batch_size, len(samples))
            self._logger.info(
                f"Strategy {strategy.name}: {processed}/{len(samples)} samples processed"
            )

    async def _process_sample(
        self,
        strategy: BaseRetrievalStrategy,
        sample: BenchmarkSample,
    ) -> Optional[SampleResult]:
        """
        Process a single benchmark sample.

        Args:
            strategy: Retrieval strategy to use
            sample: Benchmark sample

        Returns:
            SampleResult or None on failure
        """
        result = SampleResult(
            sample_id=sample.sample_id,
            query=sample.query,
            ground_truth=sample.answer,
            predicted_answer="",
            strategy=strategy.name,
        )

        try:
            # Step 1: Retrieve documents
            self._metrics_collector.start_timer("retrieval")
            retrieval_result = await strategy.retrieve(
                query=sample.query,
                top_k=self.config.top_k,
            )
            retrieval_time = self._metrics_collector.stop_timer("retrieval")

            if retrieval_result.error:
                result.error = f"Retrieval error: {retrieval_result.error}"
                return result

            # Record retrieval metrics
            result.latency.retrieval_ms = retrieval_result.retrieval_time_ms
            result.latency.embedding_ms = retrieval_result.embedding_time_ms
            result.latency.region_filtering_ms = retrieval_result.region_filtering_time_ms

            # Compute retrieval quality metrics
            result.retrieval = self._compute_retrieval_metrics(
                retrieved_pages=retrieval_result.retrieved_pages,
                relevant_pages=sample.evidence_pages,
                retrieved_bboxes=retrieval_result.retrieved_bboxes,
                relevant_bboxes=sample.bboxes,
            )

            # Step 2: Generate answer using RAG
            self._metrics_collector.start_timer("rag")
            rag_response = await self._rag_evaluator.generate_answer(
                query=sample.query,
                context=retrieval_result.context_text,
            )
            rag_time = self._metrics_collector.stop_timer("rag")

            if rag_response.error:
                result.error = f"RAG error: {rag_response.error}"
                return result

            result.predicted_answer = rag_response.answer
            result.latency.llm_inference_ms = rag_response.latency_ms

            # Record token usage
            result.tokens = TokenMetrics(
                input_tokens=rag_response.input_tokens,
                output_tokens=rag_response.output_tokens,
                total_tokens=rag_response.input_tokens + rag_response.output_tokens,
            )

            # Step 3: Evaluate correctness
            correctness_result = self._correctness_evaluator.evaluate(
                prediction=rag_response.answer,
                ground_truth=sample.answer,
                predicted_bboxes=retrieval_result.retrieved_bboxes,
                ground_truth_bboxes=sample.bboxes,
            )

            result.correctness = CorrectnessMetrics(
                exact_match=correctness_result.exact_match,
                f1_score=correctness_result.f1_score,
                anls=correctness_result.anls,
                semantic_similarity=correctness_result.semantic_similarity,
            )

            # Calculate total latency
            result.latency.total_ms = (
                result.latency.retrieval_ms
                + result.latency.llm_inference_ms
                + result.latency.region_filtering_ms
            )

            # Store context for debugging
            result.retrieved_context = retrieval_result.context_text

        except asyncio.TimeoutError:
            result.error = f"Timeout after {self.config.timeout}s"
        except Exception as e:
            result.error = str(e)
            self._logger.error(f"Sample processing error: {e}", exc_info=True)

        return result

    def _compute_retrieval_metrics(
        self,
        retrieved_pages: List[int],
        relevant_pages: List[int],
        retrieved_bboxes: List[List[int]],
        relevant_bboxes: List[List[int]],
    ) -> RetrievalMetrics:
        """Compute retrieval quality metrics."""
        from benchmarks.metrics import compute_bbox_iou

        metrics = RetrievalMetrics(
            retrieved_pages=retrieved_pages,
            relevant_pages=relevant_pages,
        )

        # Hit: at least one relevant page retrieved
        relevant_set = set(relevant_pages)
        retrieved_set = set(retrieved_pages)
        metrics.hit = bool(relevant_set & retrieved_set)

        # Reciprocal rank
        for rank, page in enumerate(retrieved_pages, 1):
            if page in relevant_set:
                metrics.reciprocal_rank = 1.0 / rank
                break

        # Precision@k
        if retrieved_pages:
            relevant_in_retrieved = len(relevant_set & retrieved_set)
            metrics.precision_at_k = relevant_in_retrieved / len(retrieved_pages)

        # Recall@k
        if relevant_pages:
            relevant_in_retrieved = len(relevant_set & retrieved_set)
            metrics.recall_at_k = relevant_in_retrieved / len(relevant_pages)

        # Bounding box IoU
        if retrieved_bboxes and relevant_bboxes:
            metrics.bbox_iou = compute_bbox_iou(retrieved_bboxes, relevant_bboxes)

        return metrics

    def _get_config_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for reporting."""
        return {
            "dataset_name": self.config.dataset_name,
            "max_samples": self.config.max_samples,
            "categories": self.config.categories,
            "strategies": [s.value for s in self.config.strategies],
            "top_k": self.config.top_k,
            "llm_provider": self.config.llm_provider.value,
            "llm_model": self.config.llm_model,
            "region_relevance_threshold": self.config.region_relevance_threshold,
            "region_top_k": self.config.region_top_k,
            "region_score_aggregation": self.config.region_score_aggregation,
        }

    async def cleanup(self) -> None:
        """Clean up all resources."""
        for strategy in self._strategies.values():
            await strategy.cleanup()

        self._strategies.clear()
        self._logger.info("Benchmark runner cleaned up")

    def get_comparison_table(self, latex: bool = False) -> str:
        """
        Get comparison table for results.

        Args:
            latex: If True, output LaTeX format

        Returns:
            Formatted comparison table
        """
        if not self._report_generator or not self._metrics_collector:
            return "No results available. Run benchmark first."

        return self._report_generator.generate_comparison_table(
            self._metrics_collector, latex=latex
        )


async def run_benchmark(
    config: Optional[BenchmarkConfig] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to run a benchmark.

    Args:
        config: Benchmark configuration (or create from kwargs)
        **kwargs: Config overrides

    Returns:
        Benchmark results
    """
    if config is None:
        config = BenchmarkConfig(**kwargs)

    runner = BenchmarkRunner(config)

    try:
        results = await runner.run()
        return results
    finally:
        await runner.cleanup()
