"""
Benchmark runner for evaluating document retrieval strategies.

This module orchestrates the benchmark execution:
1. Loads the BBox_DocVQA_Bench dataset
2. Runs each strategy on each sample
3. Computes metrics (correctness, speed, tokens)
4. Generates comparison reports

Usage:
    python -m benchmark.runner --help
    python -m benchmark.runner --strategies all --max-samples 100
    python -m benchmark.runner --strategies spatial_grounding --output-dir ./results
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import BenchmarkConfig, load_config
from .dataset import BBoxDocVQADataset, BenchmarkSample, download_dataset
from .metrics import (
    AggregatedMetrics,
    SampleResult,
    aggregate_results,
    compute_answer_metrics,
    compute_region_overlap_metrics,
)
from .strategies import (
    BaseStrategy,
    ColPaliOnlyStrategy,
    OCROnlyStrategy,
    SpatialGroundingStrategy,
)

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Main benchmark runner that orchestrates evaluation.
    """

    STRATEGY_CLASSES = {
        "ocr_only": OCROnlyStrategy,
        "colpali_only": ColPaliOnlyStrategy,
        "spatial_grounding": SpatialGroundingStrategy,
    }

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.strategies: Dict[str, BaseStrategy] = {}
        self.results: Dict[str, List[SampleResult]] = {}

    def initialize_strategies(self, strategy_names: List[str]) -> None:
        """Initialize the requested strategies."""
        for name in strategy_names:
            if name not in self.STRATEGY_CLASSES:
                raise ValueError(f"Unknown strategy: {name}")
            self.strategies[name] = self.STRATEGY_CLASSES[name](self.config)
            logger.info(f"Initialized strategy: {name}")

    def load_dataset(self) -> BBoxDocVQADataset:
        """Load the benchmark dataset."""
        # Check if dataset exists, download if not
        dataset_dir = Path(self.config.dataset_cache_dir) / "BBox_DocVQA_Bench"

        if not dataset_dir.exists():
            logger.info("Dataset not found, downloading...")
            dataset_dir = download_dataset(
                self.config.dataset_cache_dir,
                self.config.dataset_name,
            )

        dataset = BBoxDocVQADataset(str(dataset_dir))
        dataset.load()

        stats = dataset.get_statistics()
        logger.info(f"Dataset loaded: {stats['total_samples']} samples")
        logger.info(f"Categories: {stats['categories']}")
        logger.info(f"Type distribution: {stats['type_distribution']}")

        return dataset

    def run_sample(
        self,
        strategy: BaseStrategy,
        sample: BenchmarkSample,
        dataset_dir: Path,
    ) -> SampleResult:
        """Run a single sample through a strategy."""
        # Load the image (use first page)
        image = sample.get_image(0, dataset_dir)
        if image is None:
            return SampleResult(
                sample_id=sample.sample_id,
                strategy=strategy.name,
                query=sample.query,
                ground_truth_answer=sample.answer,
                predicted_answer="",
                predicted_regions=[],
                ground_truth_bboxes=[],
                error="Failed to load image",
            )

        # Get ground truth bboxes for first page
        gt_bboxes = sample.ground_truth_bboxes[0] if sample.ground_truth_bboxes else []

        # Run the strategy
        strategy_result = strategy.process(sample, image)

        # Create sample result
        result = SampleResult(
            sample_id=sample.sample_id,
            strategy=strategy.name,
            query=sample.query,
            ground_truth_answer=sample.answer,
            predicted_answer=strategy_result.llm_response,
            predicted_regions=strategy_result.regions,
            ground_truth_bboxes=gt_bboxes,
            timing=strategy_result.timing,
            tokens=strategy_result.tokens,
            error=strategy_result.error,
        )

        # Compute metrics
        if not result.error:
            result.region_metrics = compute_region_overlap_metrics(
                strategy_result.regions,
                gt_bboxes,
            )
            result.answer_metrics = compute_answer_metrics(
                strategy_result.llm_response,
                sample.answer,
            )

        return result

    def run(self, dataset: BBoxDocVQADataset) -> Dict[str, AggregatedMetrics]:
        """
        Run the benchmark on all samples.

        Returns:
            Dictionary mapping strategy name to aggregated metrics
        """
        dataset_dir = Path(self.config.dataset_cache_dir) / "BBox_DocVQA_Bench"

        # Limit samples if configured
        samples = list(dataset)
        if self.config.max_samples:
            samples = samples[:self.config.max_samples]

        logger.info(f"Running benchmark on {len(samples)} samples")

        # Initialize results storage
        for strategy_name in self.strategies:
            self.results[strategy_name] = []

        # Process each sample
        for idx, sample in enumerate(samples):
            if self.config.verbose:
                logger.info(f"Processing sample {idx + 1}/{len(samples)}: {sample.query[:50]}...")

            for strategy_name, strategy in self.strategies.items():
                try:
                    result = self.run_sample(strategy, sample, dataset_dir)
                    self.results[strategy_name].append(result)

                    if self.config.verbose and not result.error:
                        logger.info(
                            f"  {strategy_name}: "
                            f"IoU={result.region_metrics.mean_iou:.3f}, "
                            f"time={result.timing.total_time_ms:.0f}ms, "
                            f"tokens={result.tokens.total_tokens}"
                        )
                except Exception as e:
                    logger.error(f"Error processing sample {sample.sample_id} with {strategy_name}: {e}")
                    self.results[strategy_name].append(
                        SampleResult(
                            sample_id=sample.sample_id,
                            strategy=strategy_name,
                            query=sample.query,
                            ground_truth_answer=sample.answer,
                            predicted_answer="",
                            predicted_regions=[],
                            ground_truth_bboxes=[],
                            error=str(e),
                        )
                    )

        # Aggregate results
        aggregated = {}
        for strategy_name, results in self.results.items():
            aggregated[strategy_name] = aggregate_results(results, strategy_name)

        return aggregated

    def save_results(
        self,
        aggregated: Dict[str, AggregatedMetrics],
        output_dir: Optional[str] = None,
    ) -> Path:
        """Save benchmark results to disk."""
        output_path = Path(output_dir or self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save aggregated metrics
        aggregated_file = output_path / f"aggregated_metrics_{timestamp}.json"
        with open(aggregated_file, "w") as f:
            json.dump(
                {name: metrics.to_dict() for name, metrics in aggregated.items()},
                f,
                indent=2,
            )
        logger.info(f"Saved aggregated metrics to {aggregated_file}")

        # Save detailed results
        for strategy_name, results in self.results.items():
            detailed_file = output_path / f"detailed_{strategy_name}_{timestamp}.json"
            with open(detailed_file, "w") as f:
                json.dump([r.to_dict() for r in results], f, indent=2)
            logger.info(f"Saved detailed results to {detailed_file}")

        # Generate comparison report
        report_file = output_path / f"comparison_report_{timestamp}.md"
        self._generate_report(aggregated, report_file)
        logger.info(f"Saved comparison report to {report_file}")

        return output_path

    def _generate_report(
        self,
        aggregated: Dict[str, AggregatedMetrics],
        output_file: Path,
    ) -> None:
        """Generate a markdown comparison report."""
        lines = [
            "# Benchmark Comparison Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            "| Strategy | Samples | Errors | Mean IoU | Precision | Recall | F1 | Mean Time (ms) | Mean Tokens |",
            "|----------|---------|--------|----------|-----------|--------|-----|----------------|-------------|",
        ]

        for name, metrics in aggregated.items():
            lines.append(
                f"| {name} | {metrics.num_samples} | {metrics.num_errors} | "
                f"{metrics.mean_region_iou:.3f} | {metrics.mean_region_precision:.3f} | "
                f"{metrics.mean_region_recall:.3f} | {metrics.mean_region_f1:.3f} | "
                f"{metrics.mean_total_time_ms:.1f} | {metrics.mean_input_tokens + metrics.mean_output_tokens:.0f} |"
            )

        lines.extend([
            "",
            "## Timing Breakdown",
            "",
            "| Strategy | OCR (ms) | Embedding (ms) | Interpretability (ms) | Region Filtering (ms) | LLM (ms) | Total (ms) |",
            "|----------|----------|----------------|----------------------|----------------------|----------|------------|",
        ])

        for name, metrics in aggregated.items():
            lines.append(
                f"| {name} | {metrics.mean_ocr_time_ms:.1f} | {metrics.mean_embedding_time_ms:.1f} | "
                f"{metrics.mean_interpretability_time_ms:.1f} | {metrics.mean_region_filtering_time_ms:.1f} | "
                f"{metrics.mean_llm_time_ms:.1f} | {metrics.mean_total_time_ms:.1f} |"
            )

        lines.extend([
            "",
            "## Token Usage",
            "",
            "| Strategy | Mean Input | Mean Output | Total Input | Total Output |",
            "|----------|------------|-------------|-------------|--------------|",
        ])

        for name, metrics in aggregated.items():
            lines.append(
                f"| {name} | {metrics.mean_input_tokens:.0f} | {metrics.mean_output_tokens:.0f} | "
                f"{metrics.total_input_tokens} | {metrics.total_output_tokens} |"
            )

        lines.extend([
            "",
            "## Answer Quality",
            "",
            "| Strategy | Exact Match | Contains Answer | Normalized Exact | Normalized Contains |",
            "|----------|-------------|-----------------|------------------|---------------------|",
        ])

        for name, metrics in aggregated.items():
            lines.append(
                f"| {name} | {metrics.exact_match_rate:.1%} | {metrics.contains_answer_rate:.1%} | "
                f"{metrics.normalized_exact_match_rate:.1%} | {metrics.normalized_contains_rate:.1%} |"
            )

        lines.extend([
            "",
            "## IoU at Different Thresholds",
            "",
            "| Strategy | IoU@0.25 | IoU@0.5 | IoU@0.75 |",
            "|----------|----------|---------|----------|",
        ])

        for name, metrics in aggregated.items():
            iou_25 = metrics.iou_at_thresholds.get(0.25, 0)
            iou_50 = metrics.iou_at_thresholds.get(0.5, 0)
            iou_75 = metrics.iou_at_thresholds.get(0.75, 0)
            lines.append(f"| {name} | {iou_25:.3f} | {iou_50:.3f} | {iou_75:.3f} |")

        with open(output_file, "w") as f:
            f.write("\n".join(lines))


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the benchmark."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    """Main entry point for the benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run document retrieval benchmark"
    )
    parser.add_argument(
        "--strategies",
        type=str,
        default="all",
        help="Comma-separated list of strategies to run (ocr_only, colpali_only, spatial_grounding, all)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to process (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./benchmark_results",
        help="Directory for output files",
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to dataset directory (will download if not found)",
    )
    parser.add_argument(
        "--relevance-threshold",
        type=float,
        default=0.3,
        help="Relevance threshold for spatial grounding (default: 0.3)",
    )
    parser.add_argument(
        "--colpali-url",
        type=str,
        default=None,
        help="ColPali service URL",
    )
    parser.add_argument(
        "--ocr-url",
        type=str,
        default=None,
        help="OCR service URL",
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        default=None,
        help="LLM service URL",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="LLM model name",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the dataset, don't run benchmark",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Build config with overrides
    config_overrides = {
        "max_samples": args.max_samples,
        "output_dir": args.output_dir,
        "relevance_threshold": args.relevance_threshold,
        "verbose": args.verbose,
    }

    if args.dataset_dir:
        config_overrides["dataset_cache_dir"] = args.dataset_dir
    if args.colpali_url:
        config_overrides["colpali_url"] = args.colpali_url
    if args.ocr_url:
        config_overrides["ocr_url"] = args.ocr_url
    if args.llm_url:
        config_overrides["llm_url"] = args.llm_url
    if args.llm_model:
        config_overrides["llm_model"] = args.llm_model

    config = load_config(**config_overrides)

    # Download dataset if requested
    if args.download_only:
        logger.info("Downloading dataset...")
        download_dataset(config.dataset_cache_dir, config.dataset_name)
        logger.info("Dataset downloaded successfully")
        return

    # Initialize runner
    runner = BenchmarkRunner(config)

    # Parse strategies
    if args.strategies == "all":
        strategy_names = list(BenchmarkRunner.STRATEGY_CLASSES.keys())
    else:
        strategy_names = [s.strip() for s in args.strategies.split(",")]

    runner.initialize_strategies(strategy_names)

    # Load dataset
    dataset = runner.load_dataset()

    # Run benchmark
    logger.info(f"Running benchmark with strategies: {strategy_names}")
    aggregated = runner.run(dataset)

    # Save results
    output_path = runner.save_results(aggregated)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)

    for name, metrics in aggregated.items():
        print(f"\n{name}:")
        print(f"  Samples: {metrics.num_samples} ({metrics.num_errors} errors)")
        print(f"  Mean IoU: {metrics.mean_region_iou:.3f}")
        print(f"  Precision/Recall/F1: {metrics.mean_region_precision:.3f}/{metrics.mean_region_recall:.3f}/{metrics.mean_region_f1:.3f}")
        print(f"  Mean Time: {metrics.mean_total_time_ms:.1f}ms")
        print(f"  Mean Tokens: {metrics.mean_input_tokens + metrics.mean_output_tokens:.0f}")
        print(f"  Answer Contains Rate: {metrics.normalized_contains_rate:.1%}")

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
