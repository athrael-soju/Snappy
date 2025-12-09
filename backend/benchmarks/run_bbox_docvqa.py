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

import os
import sys
from pathlib import Path as _Path

# Ensure backend directory is in path for imports (before any other imports)
_BENCHMARKS_DIR = _Path(__file__).parent
_BACKEND_DIR = _BENCHMARKS_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Set HuggingFace cache to local .eval_cache directory (before importing HF libraries)
_EVAL_CACHE_DIR = _BENCHMARKS_DIR / ".eval_cache"
os.environ.setdefault("HF_HOME", str(_EVAL_CACHE_DIR))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(_EVAL_CACHE_DIR))

# ruff: noqa: E402  # Imports must be after sys.path setup
import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np
import tiktoken

from .aggregation import AggregationMethod, PatchToRegionAggregator
from .baselines import BaselineGenerator
from .clients import BenchmarkColPaliClient, BenchmarkOcrClient
from .local_models import LocalColPaliModel, LocalModelClient
from .config import BenchmarkConfig, create_ablation_configs, get_default_config
from .evaluation import (
    BBoxEvaluator,
    BenchmarkResults,
    StratifiedEvaluator,
    compute_aggregate_iou,
    compute_gt_coverage,
)
from .loaders.bbox_docvqa import BBoxDocVQALoader, BBoxDocVQASample
from .selection import RegionSelector, SelectionMethod
from .merging import MergingMethod
from .utils.coordinates import NormalizedBox, compute_iou, normalize_bbox
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
        local_model_id: Optional[str] = None,
        merge_regions: bool = False,
        merge_method: MergingMethod = "proximity",
        merge_distance: float = 0.05,
        merge_score_ratio: float = 0.0,
        merge_max_area: float = 1.0,
        merge_fallback_area: float = 0.0,
        no_merge_for_text: bool = False,
        no_merge_for_table: bool = False,
        no_merge_for_image: bool = False,
    ):
        """
        Initialize the benchmark runner.

        Args:
            config: Benchmark configuration
            colpali_client: Optional ColPali client (created from config if not provided)
            ocr_client: Optional OCR client (created from config if not provided)
            local_model_id: Optional local model ID to use instead of HTTP service
            merge_regions: Whether to merge adjacent regions after selection
            merge_method: Merging method to use
            merge_distance: Distance threshold for proximity-based merging
            merge_score_ratio: Only merge regions with min/max score ratio >= threshold
            merge_max_area: Maximum area of merged region (0-1 normalized)
            merge_fallback_area: If top merged region exceeds this area, return all originals
            no_merge_for_text: Skip merging for Text-type samples (adaptive strategy)
            no_merge_for_table: Skip merging for Table-type samples (adaptive strategy)
            no_merge_for_image: Skip merging for Image-type samples (adaptive strategy)
        """
        self.config = config
        self.local_model_id = local_model_id
        self.merge_regions = merge_regions
        self.merge_method = merge_method
        self.merge_distance = merge_distance
        self.merge_score_ratio = merge_score_ratio
        self.merge_max_area = merge_max_area
        self.merge_fallback_area = merge_fallback_area
        self.no_merge_for_text = no_merge_for_text
        self.no_merge_for_table = no_merge_for_table
        self.no_merge_for_image = no_merge_for_image

        # Initialize local model if specified (bypasses HTTP service)
        self.local_model: Optional[LocalColPaliModel] = None
        if local_model_id:
            logger.info(f"Loading local model: {local_model_id}")
            self.local_model = LocalColPaliModel(model_id=local_model_id)
            self.colpali_client = LocalModelClient(self.local_model)
        else:
            # Initialize HTTP client from config
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

        # Store predictions per (aggregation_method, selection_method) for evaluation
        # Structure: predictions[agg_method][sel_method] = List[List[NormalizedBox]]
        self.predictions: Dict[str, Dict[str, List[List[NormalizedBox]]]] = {
            agg_method: {sel_method: [] for sel_method in config.selection.methods}
            for agg_method in config.aggregation.methods
        }

        # Cache for OCR regions (reused by baselines and visualizations)
        self._ocr_regions_cache: Dict[str, List[Dict[str, Any]]] = {}

        # Cache for heatmaps (reused by visualizations)
        self._heatmap_cache: Dict[str, np.ndarray] = {}

        # Tokenizer for counting tokens in region content
        self._tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding

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
        errors = []

        # Check ColPali (local model or HTTP service)
        if self.local_model_id:
            # Local model - check if loaded
            colpali_healthy = self.colpali_client.health_check()
            if not colpali_healthy:
                errors.append(f"Local model {self.local_model_id} failed to load")
            else:
                logger.info(f"Local model ready: {self.local_model_id}")
        else:
            # HTTP service
            colpali_healthy = self.colpali_client.health_check()
            if not colpali_healthy:
                errors.append(
                    f"ColPali service at {self.config.colpali.url} is not responding"
                )
            else:
                logger.info(f"ColPali service healthy at {self.config.colpali.url}")

        # Check OCR service
        ocr_healthy = self.ocr_client.health_check()
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
        all_samples = list(self._loader)

        # Filter samples by indices or max_samples
        if self.config.dataset.sample_indices:
            # Select specific samples by index
            samples = []
            for idx in self.config.dataset.sample_indices:
                if 0 <= idx < len(all_samples):
                    samples.append(all_samples[idx])
                else:
                    logger.warning(
                        f"Sample index {idx} out of range (0-{len(all_samples)-1})"
                    )
            logger.info(
                f"Selected {len(samples)} specific samples: {self.config.dataset.sample_indices}"
            )
        elif self.config.dataset.max_samples:
            samples = all_samples[: self.config.dataset.max_samples]
        else:
            samples = all_samples

        logger.info(f"Loaded {len(samples)} samples")

        # Process samples
        all_ground_truth: List[List[NormalizedBox]] = []
        all_metadata: List[Dict[str, Any]] = []
        sample_start_time = time.time()

        for idx, sample in enumerate(samples):
            sample_iter_start = time.time()

            try:
                _predictions, gt_boxes, metadata = self._process_sample(sample)
                all_ground_truth.append(gt_boxes)
                all_metadata.append(metadata)

                # Per-sample progress logging
                elapsed = time.time() - sample_start_time
                avg_per_sample = elapsed / (idx + 1)
                remaining = avg_per_sample * (len(samples) - idx - 1)
                eta_mins = remaining / 60
                sample_time = time.time() - sample_iter_start
                num_regions = metadata.get("num_ocr_regions", 0)

                # Always log progress (use print for immediate visibility)
                print(
                    f"[{idx + 1}/{len(samples)}] {sample.sample_id} [{sample.region_type}] "
                    f"- {num_regions} regions - {sample_time:.1f}s "
                    f"(ETA: {eta_mins:.1f}m)"
                )

                # Save checkpoint after every sample
                self._save_checkpoint(idx + 1, len(samples), elapsed)

            except Exception as e:
                logger.error(f"Error processing sample {sample.sample_id}: {e}")
                # Add empty predictions for all method combinations on error
                for agg_method in self.config.aggregation.methods:
                    for sel_method in self.config.selection.methods:
                        self.predictions[agg_method][sel_method].append([])
                all_ground_truth.append([])
                all_metadata.append({"sample_id": sample.sample_id, "error": str(e)})

        # Evaluate all aggregation × selection method combinations
        logger.info("Evaluating aggregation × selection methods...")
        eval_results_grid: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for agg_method in self.config.aggregation.methods:
            eval_results_grid[agg_method] = {}
            for sel_method in self.config.selection.methods:
                method_predictions = self.predictions[agg_method][sel_method]
                eval_results = self.evaluator.evaluate_batch(
                    method_predictions,
                    all_ground_truth,
                    [m.get("sample_id", "") for m in all_metadata],
                )
                eval_results_grid[agg_method][sel_method] = (
                    self._benchmark_results_to_dict(eval_results)
                )

        # Use default methods as "main" results for backwards compatibility
        default_agg = self.config.aggregation.default_method
        default_sel = self.config.selection.default_method
        main_results = self.evaluator.evaluate_batch(
            self.predictions[default_agg][default_sel],
            all_ground_truth,
            [m.get("sample_id", "") for m in all_metadata],
        )

        # Evaluate stratified (using default methods)
        stratified_evaluator = StratifiedEvaluator(self.evaluator)

        stratified_results = {}
        default_predictions = self.predictions[default_agg][default_sel]
        for stratify_by in ["category", "region_type", "domain"]:
            stratified_results[stratify_by] = stratified_evaluator.evaluate_stratified(
                default_predictions,
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
            "aggregation_selection_results": eval_results_grid,
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

        # Evaluate all aggregation × selection method combinations
        iou_threshold = 0.25  # Use lower threshold to count partial matches
        results_by_agg_sel: Dict[str, Dict[str, Any]] = {}

        for agg_method in self.config.aggregation.methods:
            # Aggregate patches to regions using this aggregation method
            region_scores = self.aggregator.aggregate(
                heatmap=heatmap,
                regions=ocr_regions,
                method=cast(AggregationMethod, agg_method),
                image_width=sample.image_width,
                image_height=sample.image_height,
            )

            results_by_agg_sel[agg_method] = {}

            for sel_method in self.config.selection.methods:
                # Adaptive merging: skip for certain region types if configured
                should_merge = self.merge_regions
                if self.no_merge_for_text and sample.region_type == "Text":
                    should_merge = False
                if self.no_merge_for_table and sample.region_type == "Table":
                    should_merge = False
                if self.no_merge_for_image and sample.region_type == "Image":
                    should_merge = False

                selection_result = self.selector.select(
                    region_scores,
                    method=cast(SelectionMethod, sel_method),
                    k=self.config.selection.default_k,
                    threshold=self.config.selection.default_threshold,
                    relative_threshold=self.config.selection.default_relative_threshold,
                    # Merging options
                    merge_regions=should_merge,
                    merge_method=cast(MergingMethod, self.merge_method),
                    merge_distance=self.merge_distance,
                    merge_score_ratio=self.merge_score_ratio,
                    merge_max_area=self.merge_max_area,
                    merge_fallback_area=self.merge_fallback_area,
                )

                # Extract prediction boxes
                method_predictions = [r.bbox for r in selection_result.selected_regions]

                # Store predictions for batch evaluation
                self.predictions[agg_method][sel_method].append(method_predictions)

                # Calculate matching statistics
                num_matching = 0
                max_iou_per_pred = []
                for pred in method_predictions:
                    max_iou = 0.0
                    for gt in gt_boxes:
                        iou = compute_iou(pred, gt)
                        max_iou = max(max_iou, iou)
                    max_iou_per_pred.append(max_iou)
                    if max_iou >= iou_threshold:
                        num_matching += 1

                # Compute aggregate metrics for this method combination
                agg_iou = compute_aggregate_iou(method_predictions, gt_boxes)
                gt_cov = compute_gt_coverage(method_predictions, gt_boxes)

                # Count tokens from full content BEFORE truncation (fix for accurate token counts)
                img_w = sample.image_width or 0
                img_h = sample.image_height or 0
                selected_tokens = self._count_scored_region_tokens(
                    selection_result.selected_regions, img_w, img_h
                )

                results_by_agg_sel[agg_method][sel_method] = {
                    "num_selected": len(method_predictions),
                    "num_matching": num_matching,
                    "max_iou": max(max_iou_per_pred) if max_iou_per_pred else 0.0,
                    "aggregate_iou": agg_iou,
                    "gt_coverage": gt_cov,
                    "threshold_used": selection_result.threshold_used,
                    "tokens_selected": selected_tokens,  # Full token count
                    "region_scores": [
                        {
                            "bbox": r.bbox,
                            "score": r.score,
                            "label": r.label,
                            "iou": (
                                max_iou_per_pred[i]
                                if i < len(max_iou_per_pred)
                                else 0.0
                            ),
                            "content": r.content[:100] if r.content else "",
                        }
                        for i, r in enumerate(selection_result.selected_regions)
                    ],
                }

        # Use default methods for backwards compatibility
        default_agg = self.config.aggregation.default_method
        default_sel = self.config.selection.default_method
        default_result = results_by_agg_sel[default_agg][default_sel]
        predictions = self.predictions[default_agg][default_sel][-1]

        # Track if merging was applied for this sample (based on type-based exclusions)
        merge_applied = self.merge_regions
        if self.no_merge_for_text and sample.region_type == "Text":
            merge_applied = False
        if self.no_merge_for_table and sample.region_type == "Table":
            merge_applied = False
        if self.no_merge_for_image and sample.region_type == "Image":
            merge_applied = False

        # Get image dimensions (default to 0 if not available)
        img_w = sample.image_width or 0
        img_h = sample.image_height or 0

        # Calculate full image tokens (baseline for comparison)
        tokens_full_image = self._calc_image_tokens(img_w, img_h) if img_w > 0 and img_h > 0 else 0

        # Count tokens in all OCR regions (text + image crop tokens)
        tokens_all_regions = self._count_region_tokens(ocr_regions, img_w, img_h)

        # Get pre-computed tokens from selected regions (computed from full content in loop)
        tokens_selected_raw = default_result["tokens_selected"]

        # Cap selected tokens at full image cost - if sending crops costs more than
        # the full image, we'd just send the full image in practice
        # This happens because each crop has its own base cost (85 tokens) and tile overhead
        tokens_selected = min(tokens_selected_raw, tokens_full_image) if tokens_full_image > 0 else tokens_selected_raw

        # Calculate savings vs both baselines
        tokens_saved_vs_ocr_pct = (
            (1 - tokens_selected / tokens_all_regions) * 100
            if tokens_all_regions > 0
            else 0.0
        )
        tokens_saved_vs_image_pct = (
            (1 - tokens_selected / tokens_full_image) * 100
            if tokens_full_image > 0
            else 0.0
        )

        # Store sample result with all method results
        self.sample_results.append(
            {
                "sample_id": sample.sample_id,
                "question": sample.question,
                "answer": sample.answer,
                "region_type": sample.region_type,
                "num_ocr_regions": len(ocr_regions),
                "num_ground_truth": len(gt_boxes),
                "aggregation_selection_results": results_by_agg_sel,
                # Keep default method stats at top level for backwards compatibility
                "num_selected": default_result["num_selected"],
                "num_matching": default_result["num_matching"],
                "max_iou": default_result["max_iou"],
                "region_scores": default_result["region_scores"],
                # Token statistics
                "tokens_full_image": tokens_full_image,
                "tokens_all_regions": tokens_all_regions,
                "tokens_selected": tokens_selected,
                "tokens_saved_vs_ocr_pct": tokens_saved_vs_ocr_pct,
                "tokens_saved_vs_image_pct": tokens_saved_vs_image_pct,
                # Merging info
                "merge_applied": merge_applied,
            }
        )

        metadata = {
            "sample_id": sample.sample_id,
            "category": sample.category,
            "region_type": sample.region_type,
            "domain": sample.domain,
            "num_ocr_regions": len(ocr_regions),
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

        # Valid baseline names
        valid_baselines = {
            "random",
            "bm25",
            "cosine",
            "uniform_patches",
            "center_bias",
            "top_left_bias",
        }

        for baseline_name in self.config.baselines.enabled:
            # Validate baseline name
            if baseline_name not in valid_baselines:
                raise ValueError(
                    f"Unknown baseline method: '{baseline_name}'. "
                    f"Valid options: {sorted(valid_baselines)}"
                )

            logger.info(f"Running baseline: {baseline_name}")

            predictions = []
            skipped_samples = 0
            for sample in samples:
                # Use cached OCR regions from main processing pass
                ocr_regions = self._ocr_regions_cache.get(sample.sample_id, [])
                if not ocr_regions:
                    logger.warning(
                        f"No cached OCR regions for {sample.sample_id}, using empty predictions"
                    )
                    predictions.append([])
                    skipped_samples += 1
                    continue

                # Get image dimensions for bbox normalization
                img_width = sample.image_width
                img_height = sample.image_height

                # Determine k for baselines (0 means all regions)
                baseline_k = self.config.selection.default_k
                if baseline_k == 0:
                    baseline_k = len(ocr_regions)

                if baseline_name == "random":
                    # Random uses its own k config
                    random_k = self.config.baselines.random_k
                    if random_k == 0:
                        random_k = len(ocr_regions)
                    result = self.baseline_generator.random_selection(
                        ocr_regions,
                        k=random_k,
                        image_width=img_width,
                        image_height=img_height,
                    )
                elif baseline_name == "bm25":
                    result = self.baseline_generator.text_similarity_bm25(
                        ocr_regions,
                        query=sample.question,
                        k=baseline_k,
                        image_width=img_width,
                        image_height=img_height,
                    )
                elif baseline_name == "cosine":
                    result = self.baseline_generator.text_similarity_cosine(
                        ocr_regions,
                        query=sample.question,
                        k=baseline_k,
                        image_width=img_width,
                        image_height=img_height,
                    )
                elif baseline_name == "uniform_patches":
                    result = self.baseline_generator.uniform_patches(
                        ocr_regions,
                        image_width=img_width,
                        image_height=img_height,
                    )
                    # Apply selection to uniform baseline (0 means all)
                    if self.config.selection.default_k > 0:
                        result.region_scores = result.region_scores[
                            : self.config.selection.default_k
                        ]
                elif baseline_name == "center_bias":
                    result = self.baseline_generator.center_bias(
                        ocr_regions,
                        image_width=img_width,
                        image_height=img_height,
                    )
                    if self.config.selection.default_k > 0:
                        result.region_scores = result.region_scores[
                            : self.config.selection.default_k
                        ]
                elif baseline_name == "top_left_bias":
                    result = self.baseline_generator.top_left_bias(
                        ocr_regions,
                        image_width=img_width,
                        image_height=img_height,
                    )
                    if self.config.selection.default_k > 0:
                        result.region_scores = result.region_scores[
                            : self.config.selection.default_k
                        ]

                predictions.append([r.bbox for r in result.region_scores])

            # Log warning if samples were skipped
            if skipped_samples > 0:
                logger.warning(
                    f"Baseline '{baseline_name}': {skipped_samples}/{len(samples)} samples had no OCR regions"
                )

            # Evaluate baseline
            eval_results = self.evaluator.evaluate_batch(
                predictions,
                ground_truth,
                [s.sample_id for s in samples],
            )

            result_dict = self._benchmark_results_to_dict(eval_results)
            result_dict["skipped_samples"] = (
                skipped_samples  # Track samples without OCR
            )
            baseline_results[baseline_name] = result_dict

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
            "mean_aggregate_iou": results.mean_aggregate_iou,
            "mean_gt_coverage": results.mean_gt_coverage,
            "coverage_hit_rate_at_thresholds": results.coverage_hit_rate_at_thresholds,
            "mAP": results.mAP,
            "total_samples": results.total_samples,
        }

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self._tokenizer.encode(text))

    def _count_region_tokens(
        self,
        regions: List[Dict[str, Any]],
        img_width: int = 0,
        img_height: int = 0,
    ) -> int:
        """Count total tokens across all region contents.

        For text regions: counts text tokens using tiktoken
        For image regions: calculates vision tokens based on bbox dimensions
        """
        total = 0
        for region in regions:
            label = region.get("label", "").lower()
            content = region.get("content", "")

            if label == "image" and img_width > 0 and img_height > 0:
                # Image region: calculate vision tokens based on bbox
                # Note: bbox in ocr_regions may be pixel coords, normalize first
                raw_bbox = region.get("bbox", [0, 0, 0, 0])
                bbox = normalize_bbox(raw_bbox, img_width, img_height)
                crop_w = int((bbox[2] - bbox[0]) * img_width)
                crop_h = int((bbox[3] - bbox[1]) * img_height)
                if crop_w > 0 and crop_h > 0:
                    total += self._calc_image_tokens(crop_w, crop_h)
            elif content:
                # Text/table region: count text tokens
                total += self._count_tokens(content)
        return total

    def _count_scored_region_tokens(
        self,
        scored_regions: List[Any],  # List of ScoredRegion objects
        img_width: int = 0,
        img_height: int = 0,
    ) -> int:
        """Count tokens from ScoredRegion objects (with full content).

        For text/table regions: counts text tokens using tiktoken
        For image regions: calculates vision tokens based on bbox dimensions
        For merged regions: calculates vision tokens for each source region individually
            (Snappy sends individual cropped images, not one union crop)

        NOTE: If OCR provides image descriptions (e.g., alt text, captions, or
        VLM-generated descriptions), we could send text instead of image crops,
        potentially saving significant tokens (text tokens << vision tokens).
        """
        total = 0
        # Calculate full image tokens once for capping
        full_image_tokens = self._calc_image_tokens(img_width, img_height) if img_width > 0 and img_height > 0 else 0

        for r in scored_regions:
            label = (r.label or "").lower()
            content = r.content or ""
            raw_region = r.raw_region or {}

            if label == "merged":
                # Merged region: calculate tokens for each source region individually
                source_bboxes = raw_region.get("source_bboxes", [])
                source_labels = raw_region.get("source_labels", [])
                source_contents = raw_region.get("source_contents", [])

                if source_bboxes:
                    for i, bbox in enumerate(source_bboxes):
                        src_label = source_labels[i].lower() if i < len(source_labels) else ""
                        src_content = source_contents[i] if i < len(source_contents) else ""

                        if src_label == "image" and img_width > 0 and img_height > 0:
                            # Image source: vision tokens
                            crop_w = int((bbox[2] - bbox[0]) * img_width)
                            crop_h = int((bbox[3] - bbox[1]) * img_height)
                            if crop_w > 0 and crop_h > 0:
                                region_tokens = self._calc_image_tokens(crop_w, crop_h)
                                total += min(region_tokens, full_image_tokens)
                        elif src_content:
                            # Text/table source: text tokens
                            total += self._count_tokens(src_content)
                else:
                    # Fallback to union bbox if source_bboxes not available
                    bbox = r.bbox or [0, 0, 0, 0]
                    if img_width > 0 and img_height > 0:
                        crop_w = int((bbox[2] - bbox[0]) * img_width)
                        crop_h = int((bbox[3] - bbox[1]) * img_height)
                        if crop_w > 0 and crop_h > 0:
                            region_tokens = self._calc_image_tokens(crop_w, crop_h)
                            total += min(region_tokens, full_image_tokens)
            elif label == "image" and img_width > 0 and img_height > 0:
                # Single image region: calculate vision tokens based on bbox
                bbox = r.bbox or [0, 0, 0, 0]
                crop_w = int((bbox[2] - bbox[0]) * img_width)
                crop_h = int((bbox[3] - bbox[1]) * img_height)
                if crop_w > 0 and crop_h > 0:
                    region_tokens = self._calc_image_tokens(crop_w, crop_h)
                    total += min(region_tokens, full_image_tokens)
            elif content:
                # Text/table region: count text tokens
                total += self._count_tokens(content)

        # Final cap: total selected tokens should never exceed full image
        # If sending all crops costs more than full image, we'd just send full image
        if full_image_tokens > 0:
            total = min(total, full_image_tokens)

        return total

    def _calc_image_tokens(self, width: int, height: int) -> int:
        """Calculate Claude vision tokens for an image based on dimensions.

        Uses Claude's vision token formula:
        - Images are resized to fit within 1568x1568 while maintaining aspect ratio
        - Then tiled into 512x512 tiles
        - Each tile costs ~170 tokens
        - Plus a base cost of 85 tokens
        """
        import math

        # Max dimension for Claude vision
        max_dim = 1568
        tile_size = 512
        tokens_per_tile = 170
        base_tokens = 85

        # Scale down if needed (maintain aspect ratio)
        scale = min(1.0, max_dim / max(width, height))
        scaled_w = int(width * scale)
        scaled_h = int(height * scale)

        # Calculate number of tiles
        tiles_x = math.ceil(scaled_w / tile_size)
        tiles_y = math.ceil(scaled_h / tile_size)

        return base_tokens + (tiles_x * tiles_y * tokens_per_tile)

    def _save_results(self) -> None:
        """Save benchmark results to files."""
        if self.config.output.save_json:
            json_path = self.run_dir / "results.json"
            with open(json_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"Saved results to {json_path}")

        if self.config.output.save_summary:
            summary_path = self.run_dir / "summary.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                self._write_summary(f)
            logger.info(f"Saved summary to {summary_path}")

    def _save_checkpoint(self, completed: int, total: int, elapsed: float) -> None:
        """Save compact checkpoint with essential metrics during long runs."""
        checkpoint_path = self.run_dir / "checkpoint.md"

        # Compute running stats for ALL aggregation × selection combinations
        agg_methods = self.config.aggregation.methods
        sel_methods = self.config.selection.methods

        # Stats grid: [agg_method][sel_method] -> {hits, total_coverage}
        stats_grid: Dict[str, Dict[str, Dict[str, float]]] = {
            agg: {sel: {"hits": 0, "coverage": 0.0, "selected": 0, "detected": 0}
                  for sel in sel_methods}
            for agg in agg_methods
        }

        # Token stats (same across methods, computed once)
        total_tokens_full_image = 0
        total_tokens_all = 0
        total_tokens_selected = 0

        for sample in self.sample_results:
            agg_sel = sample.get("aggregation_selection_results", {})
            total_tokens_full_image += sample.get("tokens_full_image", 0)
            total_tokens_all += sample.get("tokens_all_regions", 0)
            total_tokens_selected += sample.get("tokens_selected", 0)
            num_detected = sample.get("num_ocr_regions", 0)

            for agg_method in agg_methods:
                if agg_method not in agg_sel:
                    continue
                for sel_method in sel_methods:
                    if sel_method not in agg_sel[agg_method]:
                        continue
                    result = agg_sel[agg_method][sel_method]
                    if result.get("num_matching", 0) > 0:
                        stats_grid[agg_method][sel_method]["hits"] += 1
                    stats_grid[agg_method][sel_method]["coverage"] += result.get("gt_coverage", 0.0)
                    stats_grid[agg_method][sel_method]["selected"] += result.get("num_selected", 0)
                    stats_grid[agg_method][sel_method]["detected"] += num_detected

        # Token savings calculations
        avg_tokens_full_image = total_tokens_full_image / completed if completed > 0 else 0
        avg_tokens_all = total_tokens_all / completed if completed > 0 else 0
        avg_tokens_selected = total_tokens_selected / completed if completed > 0 else 0
        saved_vs_ocr_pct = (
            (1 - total_tokens_selected / total_tokens_all) * 100
            if total_tokens_all > 0
            else 0.0
        )
        saved_vs_image_pct = (
            (1 - total_tokens_selected / total_tokens_full_image) * 100
            if total_tokens_full_image > 0
            else 0.0
        )

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            f.write(f"# Checkpoint: {completed}/{total} samples\n\n")
            f.write(
                f"**Elapsed:** {elapsed/60:.1f}m | **ETA:** {(elapsed/completed)*(total-completed)/60:.1f}m\n\n"
            )

            # IoU@0.25 Hit Rate Grid
            f.write("## IoU@0.25 Hit Rate\n\n")
            header = "| Aggregation |"
            for sel in sel_methods:
                header += f" {sel} |"
            f.write(header + "\n")
            f.write("|-------------|" + "--------|" * len(sel_methods) + "\n")

            for agg_method in agg_methods:
                row = f"| **{agg_method}** |"
                for sel_method in sel_methods:
                    hits = stats_grid[agg_method][sel_method]["hits"]
                    hit_rate = hits / completed * 100 if completed > 0 else 0
                    row += f" {hit_rate:.0f}% |"
                f.write(row + "\n")
            f.write("\n")

            # GT Coverage Grid
            f.write("## GT Coverage (avg)\n\n")
            header = "| Aggregation |"
            for sel in sel_methods:
                header += f" {sel} |"
            f.write(header + "\n")
            f.write("|-------------|" + "--------|" * len(sel_methods) + "\n")

            for agg_method in agg_methods:
                row = f"| **{agg_method}** |"
                for sel_method in sel_methods:
                    coverage = stats_grid[agg_method][sel_method]["coverage"]
                    avg_cov = coverage / completed * 100 if completed > 0 else 0
                    row += f" {avg_cov:.0f}% |"
                f.write(row + "\n")
            f.write("\n")

            # Selection Rate Grid
            f.write("## Selection Rate (% regions kept)\n\n")
            header = "| Aggregation |"
            for sel in sel_methods:
                header += f" {sel} |"
            f.write(header + "\n")
            f.write("|-------------|" + "--------|" * len(sel_methods) + "\n")

            for agg_method in agg_methods:
                row = f"| **{agg_method}** |"
                for sel_method in sel_methods:
                    selected = stats_grid[agg_method][sel_method]["selected"]
                    detected = stats_grid[agg_method][sel_method]["detected"]
                    sel_rate = selected / detected * 100 if detected > 0 else 0
                    row += f" {sel_rate:.0f}% |"
                f.write(row + "\n")
            f.write("\n")

            # Token Savings
            f.write("## Token Savings\n\n")
            f.write("| Baseline | Total | Avg/Sample | vs Selected |\n")
            f.write("|----------|-------|------------|-------------|\n")
            f.write(
                f"| Full Image | {total_tokens_full_image:,} | {avg_tokens_full_image:.0f} | **{saved_vs_image_pct:.1f}% saved** |\n"
            )
            f.write(
                f"| All OCR | {total_tokens_all:,} | {avg_tokens_all:.0f} | {saved_vs_ocr_pct:.1f}% saved |\n"
            )
            f.write(
                f"| **Selected** | **{total_tokens_selected:,}** | **{avg_tokens_selected:.0f}** | - |\n\n"
            )

            # Recent Samples (compact, last 20)
            f.write("## Recent Samples\n\n")
            default_agg = self.config.aggregation.default_method
            default_sel = self.config.selection.default_method
            f.write(f"*Using {default_agg} + {default_sel}*\n\n")
            f.write(
                "| Sample | Type | Rgns | Sel | Hit | Cov |\n"
            )
            f.write(
                "|--------|------|------|-----|-----|-----|\n"
            )
            # Show last 20 samples for compactness
            for sample in self.sample_results[-20:]:
                sid = sample.get("sample_id", "?")
                rtype = sample.get("region_type", "?")[0]  # First letter only
                num_ocr = sample.get("num_ocr_regions", 0)
                agg_sel = sample.get("aggregation_selection_results", {})
                if default_agg in agg_sel and default_sel in agg_sel[default_agg]:
                    result = agg_sel[default_agg][default_sel]
                    num_sel = result.get("num_selected", 0)
                    hit = "✅" if result.get("num_matching", 0) > 0 else "❌"
                    cov = result.get("gt_coverage", 0.0) * 100
                else:
                    num_sel = 0
                    hit = "?"
                    cov = 0
                f.write(
                    f"| {sid} | {rtype} | {num_ocr} | {num_sel} | {hit} | {cov:.0f}% |\n"
                )

    def _generate_visualizations(self, samples: List[BBoxDocVQASample]) -> None:
        """Generate debug visualizations for select samples, organized by sample subfolder."""
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

        num_agg = len(self.config.aggregation.methods)
        num_sel = len(self.config.selection.methods)
        logger.info(
            f"Generating {len(indices)} x {num_agg} x {num_sel} visualizations..."
        )

        # Base visualization directory
        vis_base_dir = self.run_dir / self.config.visualization.output_dir

        for idx in indices:
            sample = samples[idx]
            try:
                # Create subfolder for this sample
                sample_vis_dir = vis_base_dir / sample.sample_id
                sample_vis_dir.mkdir(parents=True, exist_ok=True)

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
                gt_boxes = sample.get_normalized_bboxes()

                # Generate a visualization for each aggregation × selection combination
                for agg_method in self.config.aggregation.methods:
                    region_scores = self.aggregator.aggregate(
                        heatmap=heatmap,
                        regions=ocr_regions,
                        method=cast(AggregationMethod, agg_method),
                        image_width=sample.image_width,
                        image_height=sample.image_height,
                    )

                    for sel_method in self.config.selection.methods:
                        # Adaptive merging: skip for certain region types if configured
                        should_merge = self.merge_regions
                        if self.no_merge_for_text and sample.region_type == "Text":
                            should_merge = False
                        if self.no_merge_for_table and sample.region_type == "Table":
                            should_merge = False

                        selection_result = self.selector.select(
                            region_scores,
                            method=cast(SelectionMethod, sel_method),
                            k=self.config.selection.default_k,
                            threshold=self.config.selection.default_threshold,
                            relative_threshold=self.config.selection.default_relative_threshold,
                            # Merging options
                            merge_regions=should_merge,
                            merge_method=cast(MergingMethod, self.merge_method),
                            merge_distance=self.merge_distance,
                            merge_score_ratio=self.merge_score_ratio,
                            merge_max_area=self.merge_max_area,
                            merge_fallback_area=self.merge_fallback_area,
                        )

                        # Create visualization and save to sample subfolder
                        vis_image = self.visualizer.visualize_sample(
                            image=image,
                            heatmap=(
                                heatmap
                                if self.config.visualization.show_heatmap
                                else None
                            ),
                            ocr_regions=ocr_regions,
                            predictions=selection_result.selected_regions,
                            ground_truth=gt_boxes,
                            sample_id="",  # Don't auto-save, we handle it below
                            query=f"[{agg_method}+{sel_method}] {sample.question}",
                            all_region_scores=region_scores,
                        )

                        # Save with method-specific filename in sample subfolder
                        output_path = sample_vis_dir / f"{agg_method}_{sel_method}.png"
                        vis_image.convert("RGB").save(
                            output_path, dpi=(self.visualizer.dpi, self.visualizer.dpi)
                        )

                logger.debug(
                    f"Saved {num_agg * num_sel} visualizations to {sample_vis_dir}"
                )

            except Exception as e:
                logger.warning(f"Visualization failed for {sample.sample_id}: {e}")

    def _write_summary(self, f) -> None:
        """Write markdown-formatted summary with comparison tables."""
        # Header
        f.write(f"# Benchmark: {self.config.name}\n\n")

        metadata = self.results.get("metadata", {})
        f.write(f"**Date:** {metadata.get('timestamp', 'N/A')}\n")
        f.write(f"**Total Samples:** {metadata.get('total_samples', 0)}\n")
        f.write(f"**Elapsed Time:** {metadata.get('elapsed_seconds', 0):.2f}s\n\n")

        # Region Statistics Overview
        f.write("## Region Statistics Overview\n\n")
        total_ocr = sum(s.get("num_ocr_regions", 0) for s in self.sample_results)
        total_gt = sum(s.get("num_ground_truth", 0) for s in self.sample_results)
        total_selected = sum(s.get("num_selected", 0) for s in self.sample_results)
        n_samples = len(self.sample_results) if self.sample_results else 1
        avg_ocr = total_ocr / n_samples
        avg_gt = total_gt / n_samples
        avg_selected = total_selected / n_samples

        f.write(f"| Metric | Total | Avg per Sample |\n")
        f.write(f"|--------|-------|----------------|\n")
        f.write(f"| OCR Regions Detected | {total_ocr} | {avg_ocr:.1f} |\n")
        f.write(f"| Regions Selected | {total_selected} | {avg_selected:.1f} |\n")
        f.write(f"| Ground Truth Boxes | {total_gt} | {avg_gt:.1f} |\n\n")

        # Token Savings section
        f.write("### Token Savings (vs Full Image Baseline)\n\n")
        total_tokens_full_image = sum(
            s.get("tokens_full_image", 0) for s in self.sample_results
        )
        total_tokens_all = sum(
            s.get("tokens_all_regions", 0) for s in self.sample_results
        )
        total_tokens_selected = sum(
            s.get("tokens_selected", 0) for s in self.sample_results
        )
        avg_tokens_full_image = total_tokens_full_image / n_samples
        avg_tokens_all = total_tokens_all / n_samples
        avg_tokens_selected = total_tokens_selected / n_samples
        saved_vs_ocr_pct = (
            (1 - total_tokens_selected / total_tokens_all) * 100
            if total_tokens_all > 0
            else 0.0
        )
        saved_vs_image_pct = (
            (1 - total_tokens_selected / total_tokens_full_image) * 100
            if total_tokens_full_image > 0
            else 0.0
        )

        f.write("| Baseline | Total Tokens | Avg/Sample | vs Selected |\n")
        f.write("|----------|--------------|------------|-------------|\n")
        f.write(
            f"| Full Image (vision) | {total_tokens_full_image:,} | {avg_tokens_full_image:.0f} | **{saved_vs_image_pct:.1f}% saved** |\n"
        )
        f.write(
            f"| All OCR Regions | {total_tokens_all:,} | {avg_tokens_all:.0f} | {saved_vs_ocr_pct:.1f}% saved |\n"
        )
        f.write(
            f"| **Selected Regions** | **{total_tokens_selected:,}** | **{avg_tokens_selected:.0f}** | - |\n\n"
        )

        # Per-method selectivity: what % of detected regions does each method select?
        f.write("### Selection Rate (% of OCR regions selected)\n\n")
        f.write(
            "Shows what fraction of detected OCR regions each method keeps. Lower = more selective.\n\n"
        )

        sel_methods = self.config.selection.methods
        agg_methods = self.config.aggregation.methods

        # Build table header
        header = "| Aggregation |"
        for sel in sel_methods:
            header += f" {sel} |"
        f.write(header + "\n")

        # Separator
        sep = "|-------------|"
        for _ in sel_methods:
            sep += "----------|"
        f.write(sep + "\n")

        # Calculate selection rate for each combination
        for agg_method in agg_methods:
            row = f"| **{agg_method}** |"
            for sel_method in sel_methods:
                total_selected = 0
                total_detected = 0
                for sample in self.sample_results:
                    agg_sel = sample.get("aggregation_selection_results", {})
                    num_detected = sample.get("num_ocr_regions", 0)
                    if agg_method in agg_sel and sel_method in agg_sel[agg_method]:
                        result = agg_sel[agg_method][sel_method]
                        total_selected += result.get("num_selected", 0)
                        total_detected += num_detected
                selection_rate = (
                    total_selected / total_detected if total_detected > 0 else 0
                )
                row += f" {selection_rate:.0%} |"
            f.write(row + "\n")

        f.write("\n")

        # Aggregation × Selection Method Comparison Table
        f.write("## Aggregation × Selection Method Comparison\n\n")
        agg_sel_results = self.results.get("aggregation_selection_results", {})

        if agg_sel_results:
            # Build header row with selection methods
            sel_methods = self.config.selection.methods
            header = "| Aggregation |"
            for sel in sel_methods:
                header += f" {sel} |"
            f.write(header + "\n")

            # Separator
            sep = "|-------------|"
            for _ in sel_methods:
                sep += "--------|"
            f.write(sep + "\n")

            # Write rows for each aggregation method (showing IoU@0.25)
            for agg_method, sel_results in agg_sel_results.items():
                row = f"| **{agg_method}** |"
                for sel_method in sel_methods:
                    res = sel_results.get(sel_method, {})
                    hit_rates = res.get("hit_rate_at_thresholds", {})
                    iou_025 = hit_rates.get("0.25", hit_rates.get(0.25, 0))
                    row += f" {iou_025:.2%} |"
                f.write(row + "\n")

            f.write("\n*Values show IoU@0.25 hit rate*\n\n")

            # Coverage Hit Rate Grid
            f.write("### Coverage Hit Rate at Thresholds\n\n")
            cov_thresholds = [0.5, 0.7, 0.9]

            # Build header row with coverage thresholds
            header = "| Aggregation |"
            for thresh in cov_thresholds:
                header += f" cov@{int(thresh*100)}% |"
            f.write(header + "\n")

            # Separator
            sep = "|-------------|"
            for _ in cov_thresholds:
                sep += "---------|"
            f.write(sep + "\n")

            # Write rows for each aggregation method (using first selection method)
            for agg_method, sel_results in agg_sel_results.items():
                row = f"| **{agg_method}** |"
                # Use first selection method for coverage summary
                first_sel = list(sel_results.keys())[0] if sel_results else None
                if first_sel:
                    res = sel_results[first_sel]
                    cov_rates = res.get("coverage_hit_rate_at_thresholds", {})
                    for thresh in cov_thresholds:
                        rate = cov_rates.get(str(thresh), cov_rates.get(thresh, 0))
                        row += f" {rate:.0%} |"
                else:
                    for _ in cov_thresholds:
                        row += " 0% |"
                f.write(row + "\n")

            f.write(
                "\n*Shows percentage of samples with GT coverage >= threshold (using first selection method)*\n\n"
            )

            # Detailed table for each aggregation method
            for agg_method, sel_results in agg_sel_results.items():
                f.write(f"### {agg_method} Aggregation\n\n")
                f.write(
                    "| Selection | Mean IoU | Agg IoU | GT Cov | IoU@0.25 | IoU@0.5 | cov@50% | cov@70% | cov@90% |\n"
                )
                f.write(
                    "|-----------|----------|---------|--------|----------|---------|---------|---------|--------|\n"
                )

                for sel_method, res in sel_results.items():
                    hit_rates = res.get("hit_rate_at_thresholds", {})
                    cov_rates = res.get("coverage_hit_rate_at_thresholds", {})
                    f.write(
                        f"| {sel_method} "
                        f"| {res.get('mean_iou', 0):.4f} "
                        f"| {res.get('mean_aggregate_iou', 0):.4f} "
                        f"| {res.get('mean_gt_coverage', 0):.4f} "
                        f"| {hit_rates.get('0.25', hit_rates.get(0.25, 0)):.2%} "
                        f"| {hit_rates.get('0.5', hit_rates.get(0.5, 0)):.2%} "
                        f"| {cov_rates.get('0.5', cov_rates.get(0.5, 0)):.0%} "
                        f"| {cov_rates.get('0.7', cov_rates.get(0.7, 0)):.0%} "
                        f"| {cov_rates.get('0.9', cov_rates.get(0.9, 0)):.0%} |\n"
                    )
                f.write("\n")

        # Baseline Comparison
        f.write("## Baseline Comparison\n\n")
        baseline_results = self.results.get("baseline_results", {})

        if baseline_results:
            f.write(
                "| Baseline | IoU@0.25 | GT Cov | Agg IoU | cov@50% | cov@70% | cov@90% |\n"
            )
            f.write(
                "|----------|----------|--------|---------|---------|---------|--------|\n"
            )

            for name, res in baseline_results.items():
                hit_rates = res.get("hit_rate_at_thresholds", {})
                cov_rates = res.get("coverage_hit_rate_at_thresholds", {})
                iou_025 = hit_rates.get("0.25", hit_rates.get(0.25, 0))
                f.write(
                    f"| {name} "
                    f"| {iou_025:.2%} "
                    f"| {res.get('mean_gt_coverage', 0):.2%} "
                    f"| {res.get('mean_aggregate_iou', 0):.4f} "
                    f"| {cov_rates.get('0.5', cov_rates.get(0.5, 0)):.0%} "
                    f"| {cov_rates.get('0.7', cov_rates.get(0.7, 0)):.0%} "
                    f"| {cov_rates.get('0.9', cov_rates.get(0.9, 0)):.0%} |\n"
                )

            f.write("\n")

        # Per-Sample Results
        f.write("## Per-Sample Region Statistics\n\n")

        for sample in self.sample_results:
            sample_id = sample.get("sample_id", "unknown")
            region_type = sample.get("region_type", "unknown")
            num_ocr = sample.get("num_ocr_regions", 0)
            num_gt = sample.get("num_ground_truth", 0)

            # Get number of selected regions from default method
            num_selected = sample.get("num_selected", 0)

            f.write(f"### {sample_id} [{region_type}]\n\n")
            f.write(f"- **OCR Detected:** {num_ocr} regions\n")
            f.write(f"- **Selected:** {num_selected} regions\n")
            f.write(f"- **Ground Truth:** {num_gt} regions\n\n")

            # Per aggregation × selection results for this sample
            agg_sel_results = sample.get("aggregation_selection_results", {})
            if agg_sel_results:
                f.write("#### Aggregation × Selection Results\n\n")

                # Compact grid showing IoU hit and GT Coverage for each combination
                sel_methods = self.config.selection.methods
                header = "| Aggregation |"
                for sel in sel_methods:
                    header += f" {sel} |"
                f.write(header + "\n")

                sep = "|-------------|"
                for _ in sel_methods:
                    sep += "------------|"
                f.write(sep + "\n")

                for agg_method, sel_results in agg_sel_results.items():
                    row = f"| {agg_method} |"
                    for sel_method in sel_methods:
                        result = sel_results.get(sel_method, {})
                        gt_cov = result.get("gt_coverage", 0.0)
                        num_matching = result.get("num_matching", 0)
                        # Show both IoU hit status and GT coverage
                        icon = "✅" if num_matching > 0 else "❌"
                        row += f" {icon} cov:{gt_cov:.0%} |"
                    f.write(row + "\n")

                f.write("\n*Icon shows IoU@0.25 hit, cov shows GT Coverage*\n\n")

            # Show region details for default method (only hits, or message if no hits)
            region_scores = sample.get("region_scores", [])
            if region_scores:
                default_agg = self.config.aggregation.default_method
                default_sel = self.config.selection.default_method
                total_regions = len(region_scores)

                # Find hits (IoU >= 0.25)
                hits = [
                    (i, r)
                    for i, r in enumerate(region_scores)
                    if r.get("iou", 0.0) >= 0.25
                ]

                f.write(f"#### Regions (default: {default_agg} + {default_sel})\n\n")

                if hits:
                    f.write("| Rank | Type | Score | IoU | Status |\n")
                    f.write("|------|------|-------|-----|--------|\n")
                    for i, r in hits:
                        iou = r.get("iou", 0.0)
                        label = r.get("label", "?")
                        score = r.get("score", 0.0)
                        f.write(
                            f"| **{i+1}** (of {total_regions}) | {label} | {score:.3f} | {iou:.3f} | ✅ HIT |\n"
                        )
                else:
                    # No hits - show best IoU region as reference
                    best_idx, best_r = max(
                        enumerate(region_scores), key=lambda x: x[1].get("iou", 0.0)
                    )
                    best_iou = best_r.get("iou", 0.0)
                    best_label = best_r.get("label", "?")
                    f.write(
                        f"**No hits** (best IoU: {best_iou:.3f} at rank {best_idx+1} of {total_regions}, type: {best_label})\n"
                    )

                f.write("\n")

            f.write("---\n\n")

    def _print_summary(self) -> None:
        """Print summary to console."""
        print("\n" + "=" * 60)
        print(f"Benchmark: {self.config.name}")
        print("=" * 60)

        # Region Statistics
        total_ocr = sum(s.get("num_ocr_regions", 0) for s in self.sample_results)
        total_gt = sum(s.get("num_ground_truth", 0) for s in self.sample_results)
        num_samples = len(self.sample_results) if self.sample_results else 1
        avg_ocr = total_ocr / num_samples
        avg_gt = total_gt / num_samples

        print(f"\nRegion Statistics:")
        print(f"  OCR Regions: {total_ocr} total, {avg_ocr:.1f} avg/sample")
        print(f"  Ground Truth: {total_gt} total, {avg_gt:.1f} avg/sample")

        # Aggregation × Selection grid (IoU@0.25)
        agg_sel_results = self.results.get("aggregation_selection_results", {})
        if agg_sel_results:
            sel_methods = self.config.selection.methods
            print("\nAggregation × Selection (IoU@0.25):")

            # Header
            header = f"  {'Aggregation':<14}"
            for sel in sel_methods:
                header += f" {sel:>10}"
            print(header)
            print("  " + "-" * (14 + 11 * len(sel_methods)))

            # Rows
            for agg_method, sel_results in agg_sel_results.items():
                row = f"  {agg_method:<14}"
                for sel_method in sel_methods:
                    res = sel_results.get(sel_method, {})
                    hit_rates = res.get("hit_rate_at_thresholds", {})
                    iou_025 = hit_rates.get("0.25", hit_rates.get(0.25, 0))
                    row += f" {iou_025:>10.2%}"
                print(row)

            # GT Coverage grid (new aggregate metric)
            print("\nAggregation × Selection (GT Coverage):")
            header = f"  {'Aggregation':<14}"
            for sel in sel_methods:
                header += f" {sel:>10}"
            print(header)
            print("  " + "-" * (14 + 11 * len(sel_methods)))

            for agg_method, sel_results in agg_sel_results.items():
                row = f"  {agg_method:<14}"
                for sel_method in sel_methods:
                    res = sel_results.get(sel_method, {})
                    gt_cov = res.get("mean_gt_coverage", 0)
                    row += f" {gt_cov:>10.2%}"
                print(row)

            # Coverage hit rate at thresholds (cov@50%, cov@70%, cov@90%)
            print("\nCoverage Hit Rate at Thresholds:")
            cov_thresholds = [0.5, 0.7, 0.9]
            header = f"  {'Aggregation':<14}"
            for thresh in cov_thresholds:
                header += f" cov@{int(thresh*100):02d}%"
            print(header)
            print("  " + "-" * (14 + 10 * len(cov_thresholds)))

            for agg_method, sel_results in agg_sel_results.items():
                row = f"  {agg_method:<14}"
                # Use the first selection method for simplicity in console summary
                # (full grid is in the markdown summary)
                for sel_method in sel_methods[:1]:  # Just show default/first
                    res = sel_results.get(sel_method, {})
                    cov_rates = res.get("coverage_hit_rate_at_thresholds", {})
                    for thresh in cov_thresholds:
                        rate = cov_rates.get(str(thresh), cov_rates.get(thresh, 0))
                        row += f" {rate:>8.0%}"
                print(row)

        # Per-method selection rate (% of OCR regions kept)
        if agg_sel_results and self.sample_results:
            print("\nSelection Rate (% of OCR regions kept):")
            header = f"  {'Aggregation':<14}"
            for sel in sel_methods:
                header += f" {sel:>10}"
            print(header)
            print("  " + "-" * (14 + 11 * len(sel_methods)))

            for agg_method in self.config.aggregation.methods:
                row = f"  {agg_method:<14}"
                for sel_method in sel_methods:
                    total_selected = 0
                    total_detected = 0
                    for sample in self.sample_results:
                        agg_sel = sample.get("aggregation_selection_results", {})
                        num_detected = sample.get("num_ocr_regions", 0)
                        if agg_method in agg_sel and sel_method in agg_sel[agg_method]:
                            result = agg_sel[agg_method][sel_method]
                            total_selected += result.get("num_selected", 0)
                            total_detected += num_detected
                    selection_rate = (
                        total_selected / total_detected if total_detected > 0 else 0
                    )
                    row += f" {selection_rate:>10.0%}"
                print(row)

        print("\nBaseline Comparison:")
        print(f"  {'Baseline':<16} {'IoU@0.25':>10} {'GT Cov':>10} {'Agg IoU':>10}")
        print("  " + "-" * 48)
        for name, results in self.results.get("baseline_results", {}).items():
            hit_rates = results.get("hit_rate_at_thresholds", {})
            iou_025 = hit_rates.get("0.25", hit_rates.get(0.25, 0))
            gt_cov = results.get("mean_gt_coverage", 0)
            agg_iou = results.get("mean_aggregate_iou", 0)
            print(f"  {name:<16} {iou_025:>10.2%} {gt_cov:>10.2%} {agg_iou:>10.4f}")
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
        "--sample-indices",
        type=int,
        nargs="+",
        default=None,
        help="Specific sample indices to run (e.g., --sample-indices 9 11 18)",
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
    parser.add_argument(
        "--selection-methods",
        type=str,
        nargs="+",
        default=None,
        help=(
            "Selection methods to evaluate. Use 'all' to include all available methods. "
            "Available: top_k, threshold, percentile, otsu, elbow, gap, relative. "
            "Example: --selection-methods top_k otsu relative"
        ),
    )
    parser.add_argument(
        "--aggregation-methods",
        type=str,
        nargs="+",
        default=None,
        help=(
            "Aggregation methods to evaluate. Use 'all' to include all available methods. "
            "Available: max, mean, sum, iou_weighted, iou_weighted_norm. "
            "Example: --aggregation-methods iou_weighted max"
        ),
    )
    parser.add_argument(
        "--aggregation-method",
        type=str,
        default=None,
        choices=["max", "mean", "sum", "iou_weighted", "iou_weighted_norm"],
        help="Default patch-to-region aggregation method. Default: iou_weighted",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of top regions to select for top_k method. Use 0 to select all regions. Default: 0",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Absolute score threshold for 'threshold' selection method. Default: 0.3",
    )
    parser.add_argument(
        "--relative-threshold",
        type=float,
        default=None,
        help="Relative threshold (fraction of max score) for 'relative' selection method. Default: 0.5",
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="Disable visualization generation for faster benchmark runs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size for ColPali service requests. Higher values use more GPU memory but are faster. Default: 8",
    )
    parser.add_argument(
        "--ocr-timeout",
        type=int,
        default=None,
        help="Timeout in seconds for OCR service requests. Increase if processing complex documents. Default: 180",
    )
    parser.add_argument(
        "--local-model",
        type=str,
        default=None,
        help=(
            "Use a local ColPali-style model instead of HTTP service. "
            "Specify HuggingFace model ID (e.g., 'TomoroAI/tomoro-colqwen3-embed-4b'). "
            "Supports ColQwen3, ColModernVBert, and ColPali models."
        ),
    )
    # Region merging options
    parser.add_argument(
        "--merge-regions",
        action="store_true",
        help="Enable region merging to combine adjacent/overlapping regions after selection",
    )
    parser.add_argument(
        "--merge-method",
        type=str,
        default="proximity",
        choices=["proximity", "overlap", "connected", "none"],
        help="Region merging method (default: proximity)",
    )
    parser.add_argument(
        "--merge-distance",
        type=float,
        default=0.05,
        help="Distance threshold for proximity-based merging in normalized [0,1] space (default: 0.05)",
    )
    parser.add_argument(
        "--merge-score-ratio",
        type=float,
        default=0.0,
        help=(
            "Only merge regions if min(score)/max(score) >= threshold. "
            "Use 0.0 to disable (merge all). Range: 0.0-1.0. "
            "Example: 0.5 means regions must have scores within 2x of each other (default: 0.0)"
        ),
    )
    parser.add_argument(
        "--merge-max-area",
        type=float,
        default=1.0,
        help=(
            "Maximum area of merged region in normalized [0,1] space. "
            "Use 1.0 for no limit. Example: 0.25 limits merged regions to 25%% of page area (default: 1.0)"
        ),
    )
    parser.add_argument(
        "--merge-fallback-area",
        type=float,
        default=0.0,
        help=(
            "If top merged region exceeds this area fraction, return all original regions instead. "
            "Use 0.0 to disable. Example: 0.5 means if merged result covers >50%% of page, "
            "fall back to original unmerged regions (default: 0.0)"
        ),
    )
    parser.add_argument(
        "--no-merge-for-text",
        action="store_true",
        help=(
            "Disable region merging for 'Text' type samples. "
            "Text samples often have narrow GT regions that don't align well with merged horizontal bands. "
            "Use this to skip merging for Text while still merging Image samples."
        ),
    )
    parser.add_argument(
        "--no-merge-for-table",
        action="store_true",
        help=(
            "Disable region merging for 'Table' type samples. "
            "Table samples may have specific cell-based GT regions that don't align with merged regions."
        ),
    )
    parser.add_argument(
        "--no-merge-for-image",
        action="store_true",
        help=(
            "Disable region merging for 'Image' type samples. "
            "Image samples often have precise GT regions that get oversized when merged with surrounding text."
        ),
    )
    parser.add_argument(
        "--no-results-json",
        action="store_true",
        help=(
            "Skip saving the detailed results.json file. "
            "Useful for faster runs when only the summary.md is needed."
        ),
    )
    parser.add_argument(
        "--iou-thresholds",
        type=float,
        nargs="+",
        default=None,
        help=(
            "IoU thresholds for hit rate computation. "
            "Default: 0.25 0.5 0.75. "
            "Example: --iou-thresholds 0.20 0.25 0.5 to add 0.20 threshold"
        ),
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # All available methods
    ALL_SELECTION_METHODS = [
        "top_k",
        "threshold",
        "percentile",
        "otsu",
        "elbow",
        "gap",
        "relative",
        "confidence_gated",
    ]
    ALL_AGGREGATION_METHODS = [
        "max",
        "mean",
        "sum",
        "iou_weighted",
        "iou_weighted_norm",
    ]

    # Process selection methods argument
    selection_methods = None
    if args.selection_methods:
        if args.selection_methods == ["all"] or (
            "all" in args.selection_methods and len(args.selection_methods) == 1
        ):
            # "all" means include all available methods
            selection_methods = ALL_SELECTION_METHODS
        else:
            # Validate provided methods
            invalid_methods = [
                m for m in args.selection_methods if m not in ALL_SELECTION_METHODS
            ]
            if invalid_methods:
                parser.error(
                    f"Invalid selection methods: {invalid_methods}. Available: {ALL_SELECTION_METHODS}"
                )
            selection_methods = args.selection_methods

    # Process aggregation methods argument
    aggregation_methods = None
    if args.aggregation_methods:
        if args.aggregation_methods == ["all"] or (
            "all" in args.aggregation_methods and len(args.aggregation_methods) == 1
        ):
            aggregation_methods = ALL_AGGREGATION_METHODS
        else:
            invalid_methods = [
                m for m in args.aggregation_methods if m not in ALL_AGGREGATION_METHODS
            ]
            if invalid_methods:
                parser.error(
                    f"Invalid aggregation methods: {invalid_methods}. Available: {ALL_AGGREGATION_METHODS}"
                )
            aggregation_methods = args.aggregation_methods

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

            if args.sample_indices:
                config.dataset.sample_indices = args.sample_indices

            # Override service URLs from CLI
            if args.colpali_url:
                config.colpali.url = args.colpali_url
            if args.ocr_url:
                config.ocr.url = args.ocr_url

            # Override selection methods from CLI
            if selection_methods:
                config.selection.methods = selection_methods
                # Ensure default_method is in the methods list
                if config.selection.default_method not in selection_methods:
                    config.selection.default_method = selection_methods[0]

            # Override aggregation methods from CLI
            if aggregation_methods:
                config.aggregation.methods = aggregation_methods
                # Ensure default_method is in the methods list
                if config.aggregation.default_method not in aggregation_methods:
                    config.aggregation.default_method = aggregation_methods[0]

            # Override default aggregation method from CLI
            if args.aggregation_method:
                config.aggregation.default_method = args.aggregation_method

            # Override top-k from CLI
            if args.top_k is not None:
                config.selection.default_k = args.top_k

            # Override threshold from CLI
            if args.threshold is not None:
                config.selection.default_threshold = args.threshold

            # Override relative threshold from CLI
            if args.relative_threshold is not None:
                config.selection.default_relative_threshold = args.relative_threshold

            # Disable visualization if requested
            if args.no_viz:
                config.visualization.enabled = False

            # Disable results.json if requested
            if args.no_results_json:
                config.output.save_json = False

            # Override IoU thresholds from CLI
            if args.iou_thresholds:
                config.evaluation.iou_thresholds = sorted(args.iou_thresholds)

            runner = BenchmarkRunner(
                config,
                local_model_id=args.local_model,
                merge_regions=args.merge_regions,
                merge_method=args.merge_method,
                merge_distance=args.merge_distance,
                merge_score_ratio=args.merge_score_ratio,
                merge_max_area=args.merge_max_area,
                merge_fallback_area=args.merge_fallback_area,
                no_merge_for_text=args.no_merge_for_text,
                no_merge_for_table=args.no_merge_for_table,
                no_merge_for_image=args.no_merge_for_image,
            )
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

        if args.sample_indices:
            config.dataset.sample_indices = args.sample_indices

        # Override service URLs from CLI
        if args.colpali_url:
            config.colpali.url = args.colpali_url
        if args.ocr_url:
            config.ocr.url = args.ocr_url

        # Override selection methods from CLI
        if selection_methods:
            config.selection.methods = selection_methods
            # Ensure default_method is in the methods list
            if config.selection.default_method not in selection_methods:
                config.selection.default_method = selection_methods[0]

        # Override aggregation methods from CLI
        if aggregation_methods:
            config.aggregation.methods = aggregation_methods
            # Ensure default_method is in the methods list
            if config.aggregation.default_method not in aggregation_methods:
                config.aggregation.default_method = aggregation_methods[0]

        # Override default aggregation method from CLI
        if args.aggregation_method:
            config.aggregation.default_method = args.aggregation_method

        # Override top-k from CLI
        if args.top_k is not None:
            config.selection.default_k = args.top_k

        # Override threshold from CLI
        if args.threshold is not None:
            config.selection.default_threshold = args.threshold

        # Override relative threshold from CLI
        if args.relative_threshold is not None:
            config.selection.default_relative_threshold = args.relative_threshold

        # Override batch size from CLI
        if args.batch_size is not None:
            config.colpali.batch_size = args.batch_size

        # Override OCR timeout from CLI
        if args.ocr_timeout is not None:
            config.ocr.timeout = args.ocr_timeout

        # Disable visualization if requested
        if args.no_viz:
            config.visualization.enabled = False

        # Disable results.json if requested
        if args.no_results_json:
            config.output.save_json = False

        # Override IoU thresholds from CLI
        if args.iou_thresholds:
            config.evaluation.iou_thresholds = sorted(args.iou_thresholds)

        runner = BenchmarkRunner(
            config,
            local_model_id=args.local_model,
            merge_regions=args.merge_regions,
            merge_method=args.merge_method,
            merge_distance=args.merge_distance,
            merge_score_ratio=args.merge_score_ratio,
            merge_max_area=args.merge_max_area,
            merge_fallback_area=args.merge_fallback_area,
            no_merge_for_text=args.no_merge_for_text,
            no_merge_for_table=args.no_merge_for_table,
            no_merge_for_image=args.no_merge_for_image,
        )
        runner.run()


if __name__ == "__main__":
    main()
