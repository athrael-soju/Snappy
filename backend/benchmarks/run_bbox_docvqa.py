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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .aggregation import PatchToRegionAggregator
from .baselines import BaselineGenerator
from .clients import BenchmarkColPaliClient, BenchmarkOcrClient
from .config import BenchmarkConfig, create_ablation_configs, get_default_config
from .evaluation import BBoxEvaluator, BenchmarkResults, StratifiedEvaluator
from .loaders.bbox_docvqa import BBoxDocVQALoader, BBoxDocVQASample
from .selection import RegionSelector
from .utils.coordinates import NormalizedBox, compute_iou
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
        colpali_client: Optional[BenchmarkColPaliClient] = None,
        ocr_client: Optional[BenchmarkOcrClient] = None,
    ):
        """
        Initialize the benchmark runner.

        Args:
            config: Benchmark configuration
            colpali_client: Optional ColPali client (created from config if not provided)
            ocr_client: Optional OCR client (created from config if not provided)
        """
        self.config = config

        # Initialize service clients from config
        self.colpali_client = colpali_client or BenchmarkColPaliClient(
            base_url=config.colpali.url,
            timeout=config.colpali.timeout,
        )
        self.ocr_client = ocr_client or BenchmarkOcrClient(
            base_url=config.ocr.url,
            timeout=config.ocr.timeout,
            mode=config.ocr.mode,
            task=config.ocr.task,
            include_grounding=config.ocr.include_grounding,
        )

        # Check service health
        self._check_services()

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

        # Setup run directory
        self._setup_run_directory()

        if config.visualization.enabled:
            vis_dir = self.run_dir / config.visualization.output_dir
            self.visualizer = BenchmarkVisualizer(
                output_dir=str(vis_dir),
                dpi=config.visualization.dpi,
                show_scores=config.visualization.show_scores,
            )
        else:
            self.visualizer = None

        # Results storage
        self.results: Dict[str, Any] = {}
        self.sample_results: List[Dict[str, Any]] = []

        # Cache for OCR regions (reused by baselines and visualizations)
        self._ocr_regions_cache: Dict[str, List[Dict[str, Any]]] = {}

        # Cache for heatmaps (reused by visualizations)
        self._heatmap_cache: Dict[str, np.ndarray] = {}

        # Dataset loader (set during run)
        self._loader: Optional[BBoxDocVQALoader] = None

    def _setup_run_directory(self) -> None:
        """Create a unique directory for this benchmark run."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get the benchmarks folder (where this script lives)
        benchmarks_dir = Path(__file__).parent

        # Create run directory: benchmarks/runs/{name}_{timestamp}/
        base_dir = benchmarks_dir / self.config.output.base_dir
        self.run_dir = base_dir / f"{self.config.name}_{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Update config with the run directory
        self.config.output.run_dir = str(self.run_dir)

        logger.info(f"Run directory: {self.run_dir}")

    def _check_services(self) -> None:
        """Check that required services are available."""
        colpali_healthy = self.colpali_client.health_check()
        ocr_healthy = self.ocr_client.health_check()

        errors = []

        if not colpali_healthy:
            errors.append(f"ColPali service at {self.config.colpali.url} is not responding")
        else:
            logger.info(f"ColPali service healthy at {self.config.colpali.url}")

        if not ocr_healthy:
            errors.append(f"OCR service at {self.config.ocr.url} is not responding")
        else:
            logger.info(f"OCR service healthy at {self.config.ocr.url}")

        if errors:
            raise RuntimeError(
                "Required services unavailable:\n"
                + "\n".join(f"  - {e}" for e in errors)
                + "\n\nStart services with: docker-compose up colpali deepseek-ocr"
            )

    def run(self) -> Dict[str, Any]:
        """
        Run the complete benchmark.

        Returns:
            Dictionary containing all benchmark results
        """
        start_time = time.time()
        logger.info(f"Starting benchmark: {self.config.name}")

        # Load dataset
        self._loader = self._load_dataset()
        samples = list(self._loader)

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
        image = sample.load_image(
            images_dir=(
                Path(self.config.dataset.images_dir)
                if self.config.dataset.images_dir
                else None
            ),
            zip_reader=self._loader.zip_reader if self._loader else None,
        )

        # Get normalized ground truth
        gt_boxes = sample.get_normalized_bboxes()

        # Get OCR regions from service
        ocr_regions = self._get_ocr_regions(sample, image)

        # Get interpretability maps from ColPali
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

        # Calculate matching statistics
        iou_threshold = 0.25  # Use lower threshold to count partial matches
        num_matching = 0
        max_iou_per_pred = []
        for pred in predictions:
            max_iou = 0.0
            for gt in gt_boxes:
                iou = compute_iou(pred, gt)
                max_iou = max(max_iou, iou)
            max_iou_per_pred.append(max_iou)
            if max_iou >= iou_threshold:
                num_matching += 1

        # Store sample result
        self.sample_results.append({
            "sample_id": sample.sample_id,
            "question": sample.question,
            "answer": sample.answer,
            "region_type": sample.region_type,
            "num_ocr_regions": len(ocr_regions),
            "num_selected": len(predictions),
            "num_matching": num_matching,
            "num_ground_truth": len(gt_boxes),
            "max_iou": max(max_iou_per_pred) if max_iou_per_pred else 0.0,
            "region_scores": [
                {
                    "bbox": r.bbox,
                    "score": r.score,
                    "label": r.label,
                    "iou": max_iou_per_pred[i] if i < len(max_iou_per_pred) else 0.0,
                    "content": r.content[:100] if r.content else "",
                }
                for i, r in enumerate(selection_result.selected_regions)
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
        image: Any,
    ) -> List[Dict[str, Any]]:
        """
        Get OCR regions for a sample.

        Uses the OCR service to extract text regions with bounding boxes.
        Results are cached for reuse by baselines.

        Args:
            sample: The benchmark sample
            image: PIL Image (required)

        Returns:
            List of region dictionaries with id, label, bbox, content

        Raises:
            RuntimeError: If OCR fails or returns no regions
        """
        # Check cache first
        if sample.sample_id in self._ocr_regions_cache:
            return self._ocr_regions_cache[sample.sample_id]

        ocr_result = self.ocr_client.process_image(image)
        regions = self.ocr_client.extract_regions(ocr_result)

        if not regions:
            # Provide detailed debug info
            bbox_data = ocr_result.get("bounding_boxes", [])
            raise RuntimeError(
                f"OCR returned no regions for {sample.sample_id}. "
                f"Response keys: {list(ocr_result.keys())}, "
                f"bounding_boxes count: {len(bbox_data)}, "
                f"bounding_boxes sample: {bbox_data[:2] if bbox_data else 'empty'}"
            )

        logger.debug(f"OCR extracted {len(regions)} regions for {sample.sample_id}")

        # Cache for reuse by baselines
        self._ocr_regions_cache[sample.sample_id] = regions
        return regions

    def _get_interpretability_heatmap(
        self,
        sample: BBoxDocVQASample,
        image: Any,
    ) -> np.ndarray:
        """
        Get interpretability heatmap for a sample.

        Uses ColPali service to generate per-token similarity maps.
        Results are cached for reuse by visualizations.

        Args:
            sample: The benchmark sample
            image: PIL Image (required)

        Returns:
            2D numpy array heatmap of shape (grid_y, grid_x)

        Raises:
            RuntimeError: If ColPali fails or returns no token maps
        """
        # Check cache first
        if sample.sample_id in self._heatmap_cache:
            return self._heatmap_cache[sample.sample_id]

        response = self.colpali_client.generate_interpretability_maps(
            query=sample.question,
            image=image,
        )

        # Aggregate token maps (max over tokens)
        token_maps = []
        for sim_map in response.get("similarity_maps", []):
            map_data = sim_map.get("similarity_map", [])
            if map_data:
                token_maps.append(np.array(map_data))

        if not token_maps:
            raise RuntimeError(
                f"ColPali returned no token maps for {sample.sample_id}. "
                f"Response keys: {list(response.keys())}"
            )

        stacked = np.stack(token_maps, axis=0)
        heatmap = np.max(stacked, axis=0)
        logger.debug(
            f"ColPali generated {len(token_maps)} token maps for {sample.sample_id}, "
            f"heatmap shape: {heatmap.shape}"
        )

        # Cache for reuse by visualizations
        self._heatmap_cache[sample.sample_id] = heatmap
        return heatmap

    def _run_baselines(
        self,
        samples: List[BBoxDocVQASample],
        ground_truth: List[List[NormalizedBox]],
    ) -> Dict[str, Any]:
        """Run all enabled baselines and evaluate using cached OCR regions."""
        baseline_results = {}

        for baseline_name in self.config.baselines.enabled:
            logger.info(f"Running baseline: {baseline_name}")

            predictions = []
            for sample in samples:
                # Use cached OCR regions from main processing pass
                ocr_regions = self._ocr_regions_cache.get(sample.sample_id, [])
                if not ocr_regions:
                    logger.warning(f"No cached OCR regions for {sample.sample_id}, skipping")
                    predictions.append([])
                    continue

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
        if self.config.output.save_json:
            json_path = self.run_dir / "results.json"
            with open(json_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"Saved results to {json_path}")

        if self.config.output.save_summary:
            summary_path = self.run_dir / "summary.txt"
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
                    images_dir=(
                        Path(self.config.dataset.images_dir)
                        if self.config.dataset.images_dir
                        else None
                    ),
                    zip_reader=self._loader.zip_reader if self._loader else None,
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

        # Per-sample region statistics
        f.write(f"\n{'='*60}\n")
        f.write("Per-Sample Region Statistics:\n")
        f.write(f"{'='*60}\n\n")

        for sample in self.sample_results:
            sample_id = sample.get("sample_id", "unknown")
            region_type = sample.get("region_type", "unknown")
            num_ocr = sample.get("num_ocr_regions", 0)
            num_selected = sample.get("num_selected", 0)
            num_matching = sample.get("num_matching", 0)
            num_gt = sample.get("num_ground_truth", 0)
            max_iou = sample.get("max_iou", 0.0)

            match_status = "HIT" if num_matching > 0 else "MISS"
            f.write(f"{sample_id} [{region_type}] - {match_status}\n")
            f.write(f"  OCR Detected: {num_ocr} regions\n")
            f.write(f"  Selected: {num_selected} regions\n")
            f.write(f"  Matching (IoU>=0.25): {num_matching}/{num_selected}\n")
            f.write(f"  Ground Truth: {num_gt} regions\n")
            f.write(f"  Best IoU: {max_iou:.4f}\n")

            # Show top selected regions with their IoU
            region_scores = sample.get("region_scores", [])
            if region_scores:
                f.write("  Top Regions:\n")
                for i, r in enumerate(region_scores[:3]):  # Show top 3
                    iou = r.get("iou", 0.0)
                    label = r.get("label", "?")
                    score = r.get("score", 0.0)
                    match_mark = "✓" if iou >= 0.25 else "✗"
                    f.write(f"    {i+1}. [{label}] score={score:.3f} iou={iou:.3f} {match_mark}\n")
            f.write("\n")

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
        "--base-dir",
        type=str,
        default=None,
        help="Base directory for benchmark runs (default: benchmarks/runs)",
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
    parser.add_argument(
        "--colpali-url",
        type=str,
        default=None,
        help="ColPali service URL (default: http://localhost:7000)",
    )
    parser.add_argument(
        "--ocr-url",
        type=str,
        default=None,
        help="DeepSeek OCR service URL (default: http://localhost:8200)",
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

            if args.base_dir:
                config.output.base_dir = args.base_dir

            if args.max_samples:
                config.dataset.max_samples = args.max_samples

            # Override service URLs from CLI
            if args.colpali_url:
                config.colpali.url = args.colpali_url
            if args.ocr_url:
                config.ocr.url = args.ocr_url

            runner = BenchmarkRunner(config)
            all_results[name] = runner.run()

        # Save combined ablation results
        benchmarks_dir = Path(__file__).parent
        base_dir = args.base_dir if args.base_dir else "runs"
        output_path = benchmarks_dir / base_dir / "ablation_summary.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        logger.info(f"Saved ablation summary to {output_path}")

    else:
        # Single benchmark run
        if args.config:
            config = BenchmarkConfig.from_yaml(args.config)
        else:
            config = get_default_config()

        if args.base_dir:
            config.output.base_dir = args.base_dir

        if args.max_samples:
            config.dataset.max_samples = args.max_samples

        # Override service URLs from CLI
        if args.colpali_url:
            config.colpali.url = args.colpali_url
        if args.ocr_url:
            config.ocr.url = args.ocr_url

        runner = BenchmarkRunner(config)
        runner.run()


if __name__ == "__main__":
    main()
