"""
Benchmark runner for BBox-DocVQA evaluation.

Orchestrates the complete evaluation pipeline with support for:
- Multiple filtering strategies
- Ablation studies
- Progress tracking and checkpointing
- Results aggregation and reporting
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from tqdm import tqdm

from benchmarks.data_loader import BBoxDocVQADataset, BBoxDocVQASample
from benchmarks.evaluator import (
    EvaluationResult,
    PatchConfig,
    SpatialGroundingEvaluator,
)
from benchmarks.metrics import (
    BenchmarkResults,
    IoUMetrics,
    aggregate_metrics,
)
from benchmarks.strategies import (
    FilteringStrategy,
    STRATEGY_PRESETS,
    get_strategy,
)
from benchmarks.visualization import (
    draw_bboxes_on_image,
    visualize_similarity_heatmap,
    HAS_PIL,
)

# IoU thresholds for pass/fail determination
IOU_THRESHOLD_PASS = 0.5
IOU_THRESHOLD_GOOD = 0.7

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """
    Configuration for a benchmark run.

    This benchmark validates the Snappy approach (arXiv:2512.02660):
    OCR regions + ColPali patch-to-region relevance propagation.
    Both services are required - no fallbacks.
    """

    # Dataset configuration
    dataset_path: str
    categories: Optional[List[str]] = None
    max_samples: Optional[int] = None  # Limit samples for testing

    # Filtering strategies to evaluate
    strategies: List[str] = field(default_factory=lambda: ["all"])

    # Evaluation settings
    score_aggregation: str = "iou_weighted"
    token_aggregation: str = "max"

    # ColPali configuration
    colpali_url: Optional[str] = None
    image_size: int = 448
    patch_size: int = 14

    # OCR configuration
    ocr_url: Optional[str] = None

    # Run settings
    output_dir: str = "benchmarks/runs"
    run_name: Optional[str] = None
    save_predictions: bool = True
    checkpoint_interval: int = 100

    # Instance type filtering
    instance_types: Optional[List[str]] = None  # ['SPSBB', 'SPMBB', 'MPMBB']
    subimg_types: Optional[List[str]] = None  # ['text', 'table', 'image']

    def __post_init__(self):
        if self.run_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_name = f"bbox_docvqa_{timestamp}"


class BenchmarkRunner:
    """
    Runner for BBox-DocVQA benchmarks.

    Supports both online (with ColPali API) and offline evaluation modes.
    Uses DeepSeek OCR for region extraction when enabled.
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        colpali_client: Optional[Any] = None,
        ocr_client: Optional[Any] = None,
    ):
        """
        Initialize the benchmark runner.

        Args:
            config: Benchmark configuration
            colpali_client: Optional ColPali client for online evaluation
            ocr_client: Optional OCR client for region extraction
        """
        self.config = config
        self.colpali_client = colpali_client
        self.ocr_client = ocr_client

        # Initialize evaluator - OCR client is required for the Snappy approach
        patch_config = PatchConfig(
            image_size=config.image_size,
            patch_size=config.patch_size,
        )
        self.evaluator = SpatialGroundingEvaluator(
            colpali_client=colpali_client,
            ocr_client=ocr_client,
            patch_config=patch_config,
            score_aggregation=config.score_aggregation,
        )

        # Load dataset
        self.dataset = BBoxDocVQADataset(
            dataset_path=config.dataset_path,
            categories=config.categories,
        )

        # Filter samples if needed
        self.samples = self._filter_samples()

        # Setup output directory
        self.output_dir = Path(config.output_dir) / config.run_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize results storage
        self.results: Dict[str, List[EvaluationResult]] = {}
        self.strategies: Dict[str, FilteringStrategy] = {}

        # Load strategies
        for strategy_name in config.strategies:
            self.strategies[strategy_name] = get_strategy(strategy_name)

    def _filter_samples(self) -> List[BBoxDocVQASample]:
        """Filter samples based on config."""
        samples = list(self.dataset)

        # Filter by instance type
        if self.config.instance_types:
            samples = [
                s for s in samples if s.instance_type in self.config.instance_types
            ]

        # Filter by sub-image type
        if self.config.subimg_types:
            samples = [
                s
                for s in samples
                if any(
                    t in types
                    for types in s.subimg_types
                    for t in self.config.subimg_types
                )
            ]

        # Limit samples
        if self.config.max_samples:
            samples = samples[: self.config.max_samples]

        logger.info(f"Running evaluation on {len(samples)} samples")
        return samples

    async def run_online(self) -> Dict[str, BenchmarkResults]:
        """
        Run benchmark with online ColPali API calls.

        Uses the Snappy approach: OCR regions + ColPali patch-to-region relevance.

        Returns:
            Dictionary mapping strategy name to BenchmarkResults
        """
        if self.colpali_client is None:
            raise ValueError("ColPali client required for online evaluation")
        if self.ocr_client is None:
            raise ValueError("OCR client required for online evaluation")

        all_results = {}

        # Create visualizations directory
        viz_dir = self.output_dir / "sample_visualizations"
        viz_dir.mkdir(parents=True, exist_ok=True)

        for strategy_name, strategy in self.strategies.items():
            logger.info(f"Evaluating strategy: {strategy_name}")
            strategy_results = []
            sample_images = {}  # Store images for visualization

            for idx, sample in enumerate(tqdm(self.samples, desc=strategy_name)):
                # Load image (single-page for now)
                try:
                    image = self.dataset.get_image(sample, page_idx=0)
                except FileNotFoundError as e:
                    logger.warning(f"Image not found for {sample.doc_name}: {e}")
                    continue

                # Evaluate using OCR regions (extracted inside evaluate_sample_online)
                result = await self.evaluator.evaluate_sample_online(
                    sample=sample,
                    image=image,
                    filtering_strategy=strategy,
                    candidate_regions=None,  # Will extract OCR regions
                )
                strategy_results.append(result)

                # Store image reference for visualization
                sample_images[result.sample_id] = image

                # Checkpoint
                if (idx + 1) % self.config.checkpoint_interval == 0:
                    self._save_checkpoint(strategy_name, strategy_results)

            # Store results
            self.results[strategy_name] = strategy_results
            all_results[strategy_name] = self._aggregate_results(strategy_results)

            # Generate per-sample visualizations and save results
            self._save_strategy_results(strategy_name, strategy_results, sample_images)

        # Save overall summary
        self._save_summary(all_results)
        return all_results

    def run_offline_with_maps(
        self,
        similarity_maps_dir: str,
    ) -> Dict[str, BenchmarkResults]:
        """
        Run benchmark with precomputed similarity maps.

        NOTE: Offline mode uses patch-based candidate regions since OCR cannot
        be run without the original images. For full Snappy evaluation with
        OCR regions, use run_online() instead.

        Args:
            similarity_maps_dir: Directory containing precomputed maps

        Returns:
            Dictionary mapping strategy name to BenchmarkResults
        """
        logger.warning(
            "Offline mode uses patch-based candidates. "
            "For full Snappy evaluation with OCR regions, use run_online()."
        )

        maps_path = Path(similarity_maps_dir)
        all_results = {}

        for strategy_name, strategy in self.strategies.items():
            logger.info(f"Evaluating strategy: {strategy_name}")
            strategy_results = []

            for sample in tqdm(self.samples, desc=strategy_name):
                # Load precomputed maps
                sample_id = f"{sample.doc_name}_{sample.evidence_pages[0]}"
                maps_file = maps_path / f"{sample_id}.npz"

                if not maps_file.exists():
                    logger.warning(f"No precomputed maps for {sample_id}")
                    continue

                data = np.load(maps_file)
                similarity_maps = [data[f"map_{i}"] for i in range(len(data.files))]
                image_dims = tuple(data.get("image_dims", (2400, 3200)))

                # Generate patch-based candidate regions (offline mode limitation)
                candidates = self.evaluator.generate_candidate_regions(
                    image_dims[0],
                    image_dims[1],
                    mode="patches",
                )

                # Evaluate
                result = self.evaluator.evaluate_sample_offline(
                    sample=sample,
                    similarity_maps=similarity_maps,
                    image_dimensions=image_dims,
                    filtering_strategy=strategy,
                    candidate_regions=candidates,
                )
                strategy_results.append(result)

            self.results[strategy_name] = strategy_results
            all_results[strategy_name] = self._aggregate_results(strategy_results)
            self._save_strategy_results(strategy_name, strategy_results)

        self._save_summary(all_results)
        return all_results

    def run_ground_truth_baseline(self) -> BenchmarkResults:
        """
        Run baseline evaluation using ground truth bboxes as predictions.

        This provides an upper bound on achievable performance.

        Returns:
            BenchmarkResults for the ground truth baseline
        """
        logger.info("Running ground truth baseline evaluation")
        results = []

        for sample in tqdm(self.samples, desc="GT Baseline"):
            try:
                image_dims = self.dataset.get_image_dimensions(sample, page_idx=0)
            except FileNotFoundError:
                continue

            gt_bboxes = sample.bboxes[0] if sample.bboxes else []

            # Use GT as predictions (perfect predictions)
            metrics = IoUMetrics(
                mean_iou=1.0,
                iou_at_50=1.0,
                iou_at_70=1.0,
                precision=1.0,
                recall=1.0,
                f1=1.0,
                num_predictions=len(gt_bboxes),
                num_ground_truth=len(gt_bboxes),
            )

            result = EvaluationResult(
                sample_id=f"{sample.doc_name}_{sample.evidence_pages[0]}",
                query=sample.query,
                instance_type=sample.instance_type,
                category=sample.category,
                metrics=metrics,
                predicted_bboxes=gt_bboxes,
                ground_truth_bboxes=gt_bboxes,
                region_scores=[(bbox, 1.0) for bbox in gt_bboxes],
                image_dimensions=[image_dims],
            )
            results.append(result)

        return self._aggregate_results(results)

    def _aggregate_results(self, results: List[EvaluationResult]) -> BenchmarkResults:
        """Aggregate individual results into summary statistics."""
        if not results:
            return BenchmarkResults()

        # Filter out failed samples
        valid_results = [r for r in results if r.error is None]
        failed_count = len(results) - len(valid_results)

        if not valid_results:
            return BenchmarkResults(
                total_samples=len(results),
                failed_samples=failed_count,
            )

        # Aggregate overall metrics
        all_metrics = [r.metrics for r in valid_results]
        overall = aggregate_metrics(all_metrics)

        # Aggregate by instance type
        by_instance_type = {}
        for inst_type in ["SPSBB", "SPMBB", "MPMBB"]:
            type_metrics = [
                r.metrics for r in valid_results if r.instance_type == inst_type
            ]
            if type_metrics:
                by_instance_type[inst_type] = aggregate_metrics(type_metrics)

        # Aggregate by category
        by_category = {}
        categories = set(r.category for r in valid_results)
        for cat in categories:
            cat_metrics = [r.metrics for r in valid_results if r.category == cat]
            if cat_metrics:
                by_category[cat] = aggregate_metrics(cat_metrics)

        # Aggregate by sub-image type (approximate from sample data)
        by_subimg_type = {}  # Would need sample-level subimg_type tracking

        return BenchmarkResults(
            overall=overall,
            by_instance_type=by_instance_type,
            by_subimg_type=by_subimg_type,
            by_category=by_category,
            per_sample_ious=[r.metrics.mean_iou for r in valid_results],
            total_samples=len(results),
            failed_samples=failed_count,
        )

    def _save_checkpoint(
        self, strategy_name: str, results: List[EvaluationResult]
    ) -> None:
        """Save intermediate checkpoint."""
        checkpoint_file = self.output_dir / f"{strategy_name}_checkpoint.json"
        checkpoint_data = {
            "strategy": strategy_name,
            "num_samples": len(results),
            "timestamp": datetime.now().isoformat(),
            "results": [self._result_to_dict(r) for r in results[-100:]],  # Last 100
        }
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

    def _save_strategy_results(
        self,
        strategy_name: str,
        results: List[EvaluationResult],
        sample_images: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save complete results for a strategy with simplified per-sample reports."""
        # Aggregate results
        aggregated = self._aggregate_results(results)

        # Generate single consolidated markdown report with per-sample details
        self._generate_consolidated_report(
            strategy_name, results, aggregated, sample_images
        )

    def _save_summary(self, all_results: Dict[str, BenchmarkResults]) -> None:
        """Save overall benchmark summary."""
        summary_file = self.output_dir / "summary.json"

        summary = {
            "run_name": self.config.run_name,
            "dataset_path": self.config.dataset_path,
            "num_samples": len(self.samples),
            "strategies": list(self.strategies.keys()),
            "config": {
                "score_aggregation": self.config.score_aggregation,
                "token_aggregation": self.config.token_aggregation,
                "candidate_mode": "ocr",  # Snappy approach uses OCR regions
                "image_size": self.config.image_size,
                "patch_size": self.config.patch_size,
            },
            "results": {
                name: results.to_dict() for name, results in all_results.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to {summary_file}")

        # Print summary table
        self._print_summary_table(all_results)

    def _print_summary_table(self, all_results: Dict[str, BenchmarkResults]) -> None:
        """Print a summary table of results."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 80)
        print(
            f"{'Strategy':<20} {'mIoU':>8} {'IoU@0.5':>8} {'IoU@0.7':>8} "
            f"{'Prec':>8} {'Recall':>8} {'F1':>8}"
        )
        print("-" * 80)

        for strategy_name, results in all_results.items():
            m = results.overall
            print(
                f"{strategy_name:<20} {m.mean_iou:>8.3f} {m.iou_at_50:>8.3f} "
                f"{m.iou_at_70:>8.3f} {m.precision:>8.3f} {m.recall:>8.3f} "
                f"{m.f1:>8.3f}"
            )

        print("=" * 80)

        # Print per-instance-type breakdown for best strategy
        best_strategy = max(all_results.items(), key=lambda x: x[1].overall.f1)
        print(f"\nBest strategy: {best_strategy[0]}")
        print("\nBy Instance Type:")
        print(f"{'Type':<10} {'mIoU':>8} {'F1':>8} {'Samples':>10}")
        print("-" * 40)
        for inst_type, metrics in best_strategy[1].by_instance_type.items():
            print(f"{inst_type:<10} {metrics.mean_iou:>8.3f} {metrics.f1:>8.3f}")

    def _generate_consolidated_report(
        self,
        strategy_name: str,
        results: List[EvaluationResult],
        aggregated: BenchmarkResults,
        sample_images: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Generate a single consolidated report showing the full pipeline per sample."""
        report_file = self.output_dir / f"{strategy_name}_report.md"
        viz_dir = self.output_dir / "sample_visualizations"
        viz_dir.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Benchmark Report: {strategy_name}",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Mean IoU | {aggregated.overall.mean_iou:.3f} |",
            f"| IoU@0.5 | {aggregated.overall.iou_at_50:.3f} |",
            f"| IoU@0.7 | {aggregated.overall.iou_at_70:.3f} |",
            f"| Precision | {aggregated.overall.precision:.3f} |",
            f"| Recall | {aggregated.overall.recall:.3f} |",
            f"| F1 Score | {aggregated.overall.f1:.3f} |",
            "",
        ]

        # Count pass/fail
        passed = sum(
            1
            for r in results
            if r.error is None and r.metrics.mean_iou >= IOU_THRESHOLD_PASS
        )
        good = sum(
            1
            for r in results
            if r.error is None and r.metrics.mean_iou >= IOU_THRESHOLD_GOOD
        )
        failed = sum(1 for r in results if r.error is not None)
        total_valid = len([r for r in results if r.error is None])

        lines.extend(
            [
                f"**Pass Rate:** {passed}/{total_valid} ({passed/total_valid*100:.1f}%) with IoU >= {IOU_THRESHOLD_PASS}",
                f"**Good Rate:** {good}/{total_valid} ({good/total_valid*100:.1f}%) with IoU >= {IOU_THRESHOLD_GOOD}",
                f"**Errors:** {failed}/{len(results)}",
                "",
                "---",
                "",
                "## Per-Sample Results",
                "",
                "Each sample shows: detected regions -> selected regions -> matching with ground truth",
                "",
            ]
        )

        # Sort results by IoU descending
        sorted_results = sorted(
            [r for r in results if r.error is None],
            key=lambda x: x.metrics.mean_iou,
            reverse=True,
        )

        for i, result in enumerate(sorted_results):
            # Status indicator
            if result.metrics.mean_iou >= IOU_THRESHOLD_GOOD:
                status = "GOOD"
            elif result.metrics.mean_iou >= IOU_THRESHOLD_PASS:
                status = "PASS"
            else:
                status = "FAIL"

            lines.extend(
                [
                    f"### Sample {i+1}: {result.sample_id} [{status}]",
                    "",
                    f"**Query:** {result.query}",
                    f"**Category:** {result.category} | **Type:** {result.instance_type}",
                    f"**Result:** IoU = {result.metrics.mean_iou:.3f} | Precision = {result.metrics.precision:.3f} | Recall = {result.metrics.recall:.3f}",
                    "",
                ]
            )

            # Generate and save visualization if image available
            if sample_images and result.sample_id in sample_images and HAS_PIL:
                image = sample_images[result.sample_id]
                viz_filename = f"{strategy_name}_{result.sample_id}.png"
                viz_path = viz_dir / viz_filename

                try:
                    self._generate_sample_visualization(image, result, viz_path)
                    lines.append(
                        f"![{result.sample_id}](sample_visualizations/{viz_filename})"
                    )
                    lines.append("")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate visualization for {result.sample_id}: {e}"
                    )

            # 1. All OCR regions detected
            all_regions = result.all_ocr_regions or []
            lines.extend(
                [
                    f"**1. Regions Detected:** {len(all_regions)} OCR regions",
                    "",
                ]
            )
            if all_regions and len(all_regions) <= 10:
                for j, bbox in enumerate(all_regions):
                    lines.append(
                        f"   - Region {j+1}: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"
                    )
                lines.append("")
            elif all_regions:
                lines.append(f"   _(Showing first 5 of {len(all_regions)})_")
                for j, bbox in enumerate(all_regions[:5]):
                    lines.append(
                        f"   - Region {j+1}: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"
                    )
                lines.append("")

            # 2. Regions selected after filtering (with scores and labels)
            lines.extend(
                [
                    f"**2. Regions Selected:** {len(result.predicted_bboxes)} regions after filtering",
                    "",
                ]
            )
            # Get scores and labels for selected regions
            selected_with_scores = []
            score_label_map = {
                tuple(bbox): (score, label)
                for bbox, score, label in result.region_scores
            }
            for bbox in result.predicted_bboxes:
                score, label = score_label_map.get(tuple(bbox), (0.0, ""))
                selected_with_scores.append((bbox, score, label))

            for j, (bbox, score, label) in enumerate(selected_with_scores):
                # Get IoU with best matching GT
                pred_iou = (
                    result.prediction_ious[j]
                    if result.prediction_ious and j < len(result.prediction_ious)
                    else 0.0
                )
                label_str = f", {label}" if label else ""
                lines.append(
                    f"   - Selected {j+1}: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}] (score={score:.3f}, IoU={pred_iou:.3f}{label_str})"
                )
            if not selected_with_scores:
                lines.append("   _(No regions selected)_")
            lines.append("")

            # 3. Ground truth and matching
            lines.extend(
                [
                    f"**3. Ground Truth:** {len(result.ground_truth_bboxes)} expected regions",
                    "",
                ]
            )
            for j, bbox in enumerate(result.ground_truth_bboxes):
                lines.append(
                    f"   - GT {j+1}: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"
                )
            if not result.ground_truth_bboxes:
                lines.append("   _(No ground truth)_")
            lines.append("")

            lines.append("---")
            lines.append("")

        # Error samples at the end
        error_results = [r for r in results if r.error is not None]
        if error_results:
            lines.extend(
                [
                    "## Errors",
                    "",
                ]
            )
            for r in error_results:
                lines.extend(
                    [
                        f"### {r.sample_id}",
                        f"**Query:** {r.query}",
                        f"**Error:** {r.error}",
                        "",
                    ]
                )

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Consolidated report saved to {report_file}")

    def _generate_sample_visualization(
        self,
        image: Any,
        result: EvaluationResult,
        save_path: Path,
    ) -> None:
        """Generate visualization for a single sample showing heatmap + bboxes."""
        # Start with the original image
        if result.aggregated_similarity_map is not None:
            # Overlay heatmap on image
            viz_image = visualize_similarity_heatmap(
                image,
                result.aggregated_similarity_map,
                alpha=0.4,
                cmap="hot",
            )
        else:
            viz_image = image.copy()

        # Draw bounding boxes
        viz_image = draw_bboxes_on_image(
            viz_image,
            pred_bboxes=result.predicted_bboxes,
            gt_bboxes=result.ground_truth_bboxes,
            pred_color="cyan",
            gt_color="lime",
            line_width=3,
            show_labels=True,
        )

        # Save
        viz_image.save(save_path)
        logger.debug(f"Saved visualization to {save_path}")

    def _result_to_dict(self, result: EvaluationResult) -> Dict[str, Any]:
        """Convert EvaluationResult to dictionary."""
        return {
            "sample_id": result.sample_id,
            "query": result.query,
            "instance_type": result.instance_type,
            "category": result.category,
            "metrics": result.metrics.to_dict(),
            "predicted_bboxes": result.predicted_bboxes,
            "ground_truth_bboxes": result.ground_truth_bboxes,
            "image_dimensions": result.image_dimensions,
            "error": result.error,
        }


def run_ablation_study(
    config: BenchmarkConfig,
    colpali_client: Optional[Any] = None,
    ocr_client: Optional[Any] = None,
) -> Dict[str, Dict[str, BenchmarkResults]]:
    """
    Run ablation study over multiple configurations.

    Tests different combinations of:
    - Score aggregation methods
    - Token aggregation methods
    - Filtering strategies

    Args:
        config: Base benchmark configuration
        colpali_client: ColPali client (required)
        ocr_client: OCR client (required)

    Returns:
        Nested dict: {aggregation_method: {strategy: results}}
    """
    if colpali_client is None:
        raise ValueError("ColPali client required for ablation study")
    if ocr_client is None:
        raise ValueError("OCR client required for ablation study")

    ablation_results = {}

    score_aggregations = ["max", "mean", "iou_weighted"]
    token_aggregations = ["max", "mean"]

    for score_agg in score_aggregations:
        for token_agg in token_aggregations:
            config_name = f"{score_agg}_{token_agg}"
            logger.info(f"Running ablation: {config_name}")

            # Create modified config
            ablation_config = BenchmarkConfig(
                dataset_path=config.dataset_path,
                categories=config.categories,
                max_samples=config.max_samples,
                strategies=config.strategies,
                score_aggregation=score_agg,
                token_aggregation=token_agg,
                output_dir=f"{config.output_dir}/ablation_{config_name}",
                run_name=f"ablation_{config_name}",
            )

            runner = BenchmarkRunner(ablation_config, colpali_client, ocr_client)

            # Run evaluation
            results = asyncio.run(runner.run_online())
            ablation_results[config_name] = results

    return ablation_results
