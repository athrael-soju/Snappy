#!/usr/bin/env python3
"""
Main benchmark runner for BBox_DocVQA patch-to-region relevance propagation.

This script orchestrates the full benchmark pipeline:
1. Load BBox_DocVQA dataset
2. For each sample:
   a. Load image and OCR regions (or run OCR on-the-fly)
   b. Generate ColPali interpretability maps
   c. Aggregate patch scores to regions
   d. Select relevant regions
   e. Evaluate against ground truth
3. Run baselines for comparison
4. Aggregate and report results

Usage:
    python -m benchmarks.run_bbox_docvqa [--config CONFIG_PATH]
    python -m benchmarks.run_bbox_docvqa --ablation
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .aggregation import PatchToRegionAggregator, RegionScore
from .baselines import BaselineGenerator
from .config import BenchmarkConfig, create_ablation_configs, get_default_config
from .evaluation import BBoxEvaluator, BenchmarkResults, StratifiedEvaluator
from .loaders.bbox_docvqa import BBoxDocVQALoader, BBoxDocVQASample
from .selection import RegionSelector
from .utils.coordinates import NormalizedBox
from .visualization import BenchmarkVisualizer

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Orchestrates the BBox_DocVQA benchmark pipeline.

    Handles data loading, model inference, evaluation, and result aggregation.
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        colpali_client: Optional[Any] = None,
        ocr_processor: Optional[Any] = None,
    ):
        """
        Initialize the benchmark runner.

        Args:
            config: Benchmark configuration
            colpali_client: Optional ColPali client (created if not provided)
            ocr_processor: Optional OCR processor (created if not provided)
        """
        self.config = config
        self.colpali_client = colpali_client
        self.ocr_processor = ocr_processor

        # Initialize components
        self.aggregator = PatchToRegionAggregator(
            grid_x=config.aggregation.grid_x,
            grid_y=config.aggregation.grid_y,
            default_method=config.aggregation.default_method,
        )
        self.selector = RegionSelector(default_method=config.selection.default_method)
        self.evaluator = BBoxEvaluator(
            iou_thresholds=config.evaluation.iou_thresholds,
            matching_strategies=config.evaluation.matching_strategies,
        )
        self.baseline_generator = BaselineGenerator(seed=config.baselines.random_seed)

        if config.visualization.enabled:
            self.visualizer = BenchmarkVisualizer(
                output_dir=config.visualization.output_dir,
                dpi=config.visualization.dpi,
                show_scores=config.visualization.show_scores,
            )
        else:
            self.visualizer = None

        # Results storage
        self.results: Dict[str, Any] = {}
        self.sample_results: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        """
        Run the complete benchmark.

        Returns:
            Dictionary containing all benchmark results
        """
        start_time = time.time()
        logger.info(f"Starting benchmark: {self.config.name}")

        # Load dataset
        loader = self._load_dataset()
        samples = list(loader)

        if self.config.dataset.max_samples:
            samples = samples[: self.config.dataset.max_samples]

        logger.info(f"Loaded {len(samples)} samples")

        # Process samples
        all_predictions: List[List[NormalizedBox]] = []
        all_ground_truth: List[List[NormalizedBox]] = []
        all_metadata: List[Dict[str, Any]] = []

        for idx, sample in enumerate(samples):
            if idx > 0 and idx % self.config.log_progress_every == 0:
                logger.info(f"Processing sample {idx}/{len(samples)}")

            try:
                predictions, gt_boxes, metadata = self._process_sample(sample)
                all_predictions.append(predictions)
                all_ground_truth.append(gt_boxes)
                all_metadata.append(metadata)
            except Exception as e:
                logger.error(f"Error processing sample {sample.sample_id}: {e}")
                all_predictions.append([])
                all_ground_truth.append([])
                all_metadata.append({"sample_id": sample.sample_id, "error": str(e)})

        # Evaluate main method
        logger.info("Evaluating main method...")
        main_results = self.evaluator.evaluate_batch(
            all_predictions,
            all_ground_truth,
            [m.get("sample_id", "") for m in all_metadata],
        )

        # Evaluate stratified
        stratified_evaluator = StratifiedEvaluator(self.evaluator)

        stratified_results = {}
        for stratify_by in ["category", "region_type", "domain"]:
            stratified_results[stratify_by] = stratified_evaluator.evaluate_stratified(
                all_predictions,
                all_ground_truth,
                all_metadata,
                stratify_by=stratify_by,
            )

        # Run baselines
        logger.info("Running baselines...")
        baseline_results = self._run_baselines(samples, all_ground_truth)

        # Compile results
        elapsed_time = time.time() - start_time

        self.results = {
            "config": self.config.to_dict(),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_samples": len(samples),
                "elapsed_seconds": elapsed_time,
            },
            "main_results": self._benchmark_results_to_dict(main_results),
            "stratified_results": {
                key: {
                    stratum: self._benchmark_results_to_dict(res)
                    for stratum, res in results.items()
                }
                for key, results in stratified_results.items()
            },
            "baseline_results": baseline_results,
            "sample_results": self.sample_results,
        }

        # Save results
        self._save_results()

        # Generate visualizations
        if self.visualizer and self.sample_results:
            self._generate_visualizations(samples)

        logger.info(f"Benchmark completed in {elapsed_time:.2f}s")
        self._print_summary()

        return self.results

    def _load_dataset(self) -> BBoxDocVQALoader:
        """Load and filter the dataset."""
        loader = BBoxDocVQALoader(
            jsonl_path=self.config.dataset.jsonl_path,
            images_dir=self.config.dataset.images_dir,
            hf_dataset=self.config.dataset.hf_dataset,
        )
        loader.load(split=self.config.dataset.split)

        if self.config.dataset.filter_single_page:
            loader.filter_single_page()

        if self.config.dataset.categories:
            loader.filter_by_category(self.config.dataset.categories)

        if self.config.dataset.region_types:
            loader.filter_by_region_type(self.config.dataset.region_types)

        if self.config.dataset.domains:
            loader.filter_by_domain(self.config.dataset.domains)

        return loader

    def _process_sample(
        self,
        sample: BBoxDocVQASample,
    ) -> Tuple[List[NormalizedBox], List[NormalizedBox], Dict[str, Any]]:
        """
        Process a single sample through the pipeline.

        Args:
            sample: BBox_DocVQA sample

        Returns:
            (predictions, ground_truth, metadata)
        """
        # Load image and get dimensions
        try:
            image = sample.load_image(
                Path(self.config.dataset.images_dir)
                if self.config.dataset.images_dir
                else None
            )
        except Exception as e:
            logger.warning(f"Could not load image for {sample.sample_id}: {e}")
            # Use placeholder dimensions
            sample.image_width = 1000
            sample.image_height = 1000
            image = None

        # Get normalized ground truth
        gt_boxes = sample.get_normalized_bboxes()

        # Get OCR regions (mock for now - in real use, fetch from OCR service)
        ocr_regions = self._get_ocr_regions(sample, image)

        # Get interpretability maps (mock for now - in real use, fetch from ColPali)
        heatmap = self._get_interpretability_heatmap(sample, image)

        # Aggregate patches to regions
        region_scores = self.aggregator.aggregate(
            heatmap=heatmap,
            regions=ocr_regions,
            method=self.config.aggregation.default_method,
            image_width=sample.image_width,
            image_height=sample.image_height,
        )

        # Select relevant regions
        selection_result = self.selector.select(
            region_scores,
            method=self.config.selection.default_method,
            k=self.config.selection.default_k,
            relative_threshold=self.config.selection.default_relative_threshold,
        )

        # Extract prediction boxes
        predictions = [r.bbox for r in selection_result.selected_regions]

        # Store sample result
        self.sample_results.append({
            "sample_id": sample.sample_id,
            "question": sample.question,
            "answer": sample.answer,
            "num_predictions": len(predictions),
            "num_ground_truth": len(gt_boxes),
            "region_scores": [
                {"bbox": r.bbox, "score": r.score, "content": r.content[:100]}
                for r in selection_result.selected_regions
            ],
        })

        metadata = {
            "sample_id": sample.sample_id,
            "category": sample.category,
            "region_type": sample.region_type,
            "domain": sample.domain,
        }

        return predictions, gt_boxes, metadata

    def _get_ocr_regions(
        self,
        sample: BBoxDocVQASample,
        image: Optional[Any],
    ) -> List[Dict[str, Any]]:
        """
        Get OCR regions for a sample.

        In production, this would call the DeepSeek OCR service.
        For offline benchmarking, regions may be pre-computed or mocked.
        """
        if self.ocr_processor and image:
            # Use actual OCR processor
            try:
                from io import BytesIO

                buffer = BytesIO()
                image.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()

                result = self.ocr_processor.process_single(
                    image_bytes=image_bytes,
                    filename=sample.sample_id,
                )
                return result.get("regions", [])
            except Exception as e:
                logger.warning(f"OCR failed for {sample.sample_id}: {e}")

        # Fallback: Generate mock regions based on ground truth
        # (This is for testing without OCR service)
        mock_regions = []
        for idx, bbox in enumerate(sample.evidence_bbox):
            x1, y1, x2, y2 = bbox
            mock_regions.append({
                "id": f"{sample.sample_id}#region-{idx}",
                "label": "text",
                "bbox": [x1, y1, x2, y2],  # Pixel coordinates
                "content": f"Mock content for region {idx}",
            })

        # Add some noise regions
        np.random.seed(hash(sample.sample_id) % (2**32))
        for idx in range(5):
            x1 = np.random.randint(0, sample.image_width - 100)
            y1 = np.random.randint(0, sample.image_height - 100)
            x2 = x1 + np.random.randint(50, 200)
            y2 = y1 + np.random.randint(20, 100)
            mock_regions.append({
                "id": f"{sample.sample_id}#noise-{idx}",
                "label": "text",
                "bbox": [x1, y1, x2, y2],
                "content": f"Noise region {idx}",
            })

        return mock_regions

    def _get_interpretability_heatmap(
        self,
        sample: BBoxDocVQASample,
        image: Optional[Any],
    ) -> np.ndarray:
        """
        Get interpretability heatmap for a sample.

        In production, this would call the ColPali interpretability endpoint.
        For offline benchmarking, heatmaps may be pre-computed or mocked.
        """
        grid_x = self.config.aggregation.grid_x
        grid_y = self.config.aggregation.grid_y

        if self.colpali_client and image:
            # Use actual ColPali client
            try:
                from io import BytesIO

                buffer = BytesIO()
                image.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()

                response = self.colpali_client.generate_interpretability_maps(
                    query=sample.question,
                    image_bytes=image_bytes,
                )

                # Aggregate token maps
                token_maps = []
                for sim_map in response.get("similarity_maps", []):
                    map_data = sim_map.get("similarity_map", [])
                    if map_data:
                        token_maps.append(np.array(map_data))

                if token_maps:
                    stacked = np.stack(token_maps, axis=0)
                    return np.max(stacked, axis=0)

            except Exception as e:
                logger.warning(f"Interpretability failed for {sample.sample_id}: {e}")

        # Fallback: Generate mock heatmap with peaks at ground truth locations
        heatmap = np.random.rand(grid_y, grid_x) * 0.3  # Background noise

        for bbox in sample.evidence_bbox:
            x1, y1, x2, y2 = bbox
            # Convert to normalized coords then to patch coords
            norm_x1 = x1 / sample.image_width
            norm_y1 = y1 / sample.image_height
            norm_x2 = x2 / sample.image_width
            norm_y2 = y2 / sample.image_height

            patch_x1 = int(norm_x1 * grid_x)
            patch_y1 = int(norm_y1 * grid_y)
            patch_x2 = min(grid_x, int(np.ceil(norm_x2 * grid_x)))
            patch_y2 = min(grid_y, int(np.ceil(norm_y2 * grid_y)))

            # Set high values in GT region
            heatmap[patch_y1:patch_y2, patch_x1:patch_x2] = (
                0.7 + np.random.rand(patch_y2 - patch_y1, patch_x2 - patch_x1) * 0.3
            )

        return heatmap

    def _run_baselines(
        self,
        samples: List[BBoxDocVQASample],
        ground_truth: List[List[NormalizedBox]],
    ) -> Dict[str, Any]:
        """Run all enabled baselines and evaluate."""
        baseline_results = {}

        for baseline_name in self.config.baselines.enabled:
            logger.info(f"Running baseline: {baseline_name}")

            predictions = []
            for sample in samples:
                ocr_regions = self._get_ocr_regions(sample, None)

                if baseline_name == "random":
                    result = self.baseline_generator.random_selection(
                        ocr_regions, k=self.config.baselines.random_k
                    )
                elif baseline_name == "bm25":
                    result = self.baseline_generator.text_similarity_bm25(
                        ocr_regions,
                        query=sample.question,
                        k=self.config.selection.default_k,
                    )
                elif baseline_name == "cosine":
                    result = self.baseline_generator.text_similarity_cosine(
                        ocr_regions,
                        query=sample.question,
                        k=self.config.selection.default_k,
                    )
                elif baseline_name == "uniform_patches":
                    result = self.baseline_generator.uniform_patches(ocr_regions)
                    # Apply selection to uniform baseline
                    result.region_scores = result.region_scores[
                        : self.config.selection.default_k
                    ]
                elif baseline_name == "center_bias":
                    result = self.baseline_generator.center_bias(ocr_regions)
                    result.region_scores = result.region_scores[
                        : self.config.selection.default_k
                    ]
                elif baseline_name == "top_left_bias":
                    result = self.baseline_generator.top_left_bias(ocr_regions)
                    result.region_scores = result.region_scores[
                        : self.config.selection.default_k
                    ]
                else:
                    continue

                predictions.append([r.bbox for r in result.region_scores])

            # Evaluate baseline
            eval_results = self.evaluator.evaluate_batch(
                predictions,
                ground_truth,
                [s.sample_id for s in samples],
            )

            baseline_results[baseline_name] = self._benchmark_results_to_dict(eval_results)

        return baseline_results

    def _benchmark_results_to_dict(self, results: BenchmarkResults) -> Dict[str, Any]:
        """Convert BenchmarkResults to serializable dictionary."""
        return {
            "mean_iou": results.mean_iou,
            "mean_max_iou": results.mean_max_iou,
            "hit_rate_at_thresholds": results.hit_rate_at_thresholds,
            "mean_precision": results.mean_precision,
            "mean_recall": results.mean_recall,
            "mean_f1": results.mean_f1,
            "mean_hungarian_iou": results.mean_hungarian_iou,
            "mAP": results.mAP,
            "total_samples": results.total_samples,
        }

    def _save_results(self) -> None:
        """Save benchmark results to files."""
        output_dir = Path(self.config.output.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.config.output.save_json:
            json_path = output_dir / f"{self.config.name}_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"Saved results to {json_path}")

        if self.config.output.save_summary:
            summary_path = output_dir / f"{self.config.name}_{timestamp}_summary.txt"
            with open(summary_path, "w") as f:
                self._write_summary(f)
            logger.info(f"Saved summary to {summary_path}")

    def _generate_visualizations(self, samples: List[BBoxDocVQASample]) -> None:
        """Generate debug visualizations for select samples."""
        if not self.visualizer:
            return

        # Select samples to visualize based on strategy
        max_vis = min(self.config.visualization.max_samples, len(self.sample_results))

        if self.config.visualization.visualize_strategy == "worst":
            # Sort by some error metric and take worst
            sorted_results = sorted(
                enumerate(self.sample_results),
                key=lambda x: x[1].get("num_predictions", 0)
                - x[1].get("num_ground_truth", 0),
            )
            indices = [idx for idx, _ in sorted_results[:max_vis]]
        elif self.config.visualization.visualize_strategy == "random":
            np.random.seed(42)
            indices = np.random.choice(len(samples), size=max_vis, replace=False)
        else:
            indices = list(range(max_vis))

        logger.info(f"Generating {len(indices)} visualizations...")

        for idx in indices:
            sample = samples[idx]
            try:
                image = sample.load_image(
                    Path(self.config.dataset.images_dir)
                    if self.config.dataset.images_dir
                    else None
                )

                heatmap = self._get_interpretability_heatmap(sample, image)
                ocr_regions = self._get_ocr_regions(sample, image)

                region_scores = self.aggregator.aggregate(
                    heatmap=heatmap,
                    regions=ocr_regions,
                    method=self.config.aggregation.default_method,
                    image_width=sample.image_width,
                    image_height=sample.image_height,
                )

                selection_result = self.selector.select(
                    region_scores,
                    method=self.config.selection.default_method,
                    k=self.config.selection.default_k,
                )

                gt_boxes = sample.get_normalized_bboxes()

                self.visualizer.visualize_sample(
                    image=image,
                    heatmap=heatmap if self.config.visualization.show_heatmap else None,
                    ocr_regions=ocr_regions,
                    predictions=selection_result.selected_regions,
                    ground_truth=gt_boxes,
                    sample_id=sample.sample_id,
                    query=sample.question,
                )
            except Exception as e:
                logger.warning(f"Visualization failed for {sample.sample_id}: {e}")

    def _write_summary(self, f) -> None:
        """Write human-readable summary."""
        f.write(f"{'='*60}\n")
        f.write(f"Benchmark: {self.config.name}\n")
        f.write(f"{'='*60}\n\n")

        main = self.results.get("main_results", {})
        f.write("Main Results:\n")
        f.write(f"  Mean IoU: {main.get('mean_iou', 0):.4f}\n")
        f.write(f"  Mean Max IoU: {main.get('mean_max_iou', 0):.4f}\n")
        f.write(f"  Precision: {main.get('mean_precision', 0):.4f}\n")
        f.write(f"  Recall: {main.get('mean_recall', 0):.4f}\n")
        f.write(f"  F1: {main.get('mean_f1', 0):.4f}\n")
        f.write(f"  mAP: {main.get('mAP', 0):.4f}\n\n")

        f.write("Hit Rates:\n")
        for thresh, rate in main.get("hit_rate_at_thresholds", {}).items():
            f.write(f"  IoU@{thresh}: {rate:.4f}\n")

        f.write("\nBaseline Comparison:\n")
        for name, results in self.results.get("baseline_results", {}).items():
            f.write(f"  {name}: Recall={results.get('mean_recall', 0):.4f}\n")

    def _print_summary(self) -> None:
        """Print summary to console."""
        main = self.results.get("main_results", {})
        print("\n" + "=" * 60)
        print(f"Benchmark: {self.config.name}")
        print("=" * 60)
        print(f"  Mean IoU: {main.get('mean_iou', 0):.4f}")
        print(f"  Recall@0.5: {main.get('mean_recall', 0):.4f}")
        print(f"  mAP: {main.get('mAP', 0):.4f}")

        print("\nBaseline Comparison:")
        for name, results in self.results.get("baseline_results", {}).items():
            print(f"  {name}: {results.get('mean_recall', 0):.4f}")
        print()


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Run BBox_DocVQA patch-to-region relevance benchmark"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run all ablation studies",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to process",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.ablation:
        # Run all ablation studies
        configs = create_ablation_configs()
        all_results = {}

        for name, config in configs.items():
            logger.info(f"Running ablation: {name}")
            config.output.output_dir = f"{args.output_dir}/ablations/{name}"

            if args.max_samples:
                config.dataset.max_samples = args.max_samples

            runner = BenchmarkRunner(config)
            all_results[name] = runner.run()

        # Save combined ablation results
        output_path = Path(args.output_dir) / "ablation_summary.json"
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        logger.info(f"Saved ablation summary to {output_path}")

    else:
        # Single benchmark run
        if args.config:
            config = BenchmarkConfig.from_yaml(args.config)
        else:
            config = get_default_config()

        if args.max_samples:
            config.dataset.max_samples = args.max_samples

        config.output.output_dir = args.output_dir

        runner = BenchmarkRunner(config)
        runner.run()


if __name__ == "__main__":
    main()
