"""
Benchmark Pipeline Orchestrator.

This module provides the main pipeline for running the BBox_DocVQA
benchmark, coordinating dataset loading, model inference, aggregation,
selection, and evaluation.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import yaml
from numpy.typing import NDArray

from .aggregation import AggregationMethod, compute_region_scores_multi_token
from .baselines import BaselineMethod, run_all_baselines
from .evaluation import (
    AggregatedMetrics,
    EvaluationResult,
    MatchingStrategy,
    aggregate_results,
    compare_to_baseline,
    evaluate_sample,
    evaluate_stratified,
)
from .loaders.bbox_docvqa import (
    BBoxDocVQALoader,
    BBoxDocVQASample,
    ComplexityType,
)
from .selection import SelectionMethod, select_regions
from .utils.coordinates import Box

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark run."""

    # Dataset
    dataset_path: str = "Yuwh07/BBox_DocVQA_Bench"
    filter_type: str = "single_page"
    cache_dir: Optional[str] = None
    max_samples: Optional[int] = None

    # Model
    n_patches_x: int = 32
    n_patches_y: int = 32

    # Aggregation
    aggregation_methods: List[str] = field(
        default_factory=lambda: ["max", "mean", "sum", "iou_weighted"]
    )
    default_aggregation: str = "iou_weighted"
    token_aggregation: str = "max"

    # Selection
    selection_methods: List[str] = field(
        default_factory=lambda: ["top_k", "threshold", "otsu"]
    )
    default_selection: str = "top_k"
    top_k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    threshold_values: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3, 0.5])

    # Evaluation
    iou_thresholds: List[float] = field(default_factory=lambda: [0.25, 0.5, 0.75])
    matching_strategy: str = "set_coverage"

    # Baselines
    run_baselines: bool = True
    baseline_methods: List[str] = field(
        default_factory=lambda: ["random_ocr", "text_similarity", "uniform_patches"]
    )

    # Output
    results_dir: str = "results/bbox_docvqa"
    save_predictions: bool = True
    save_visualizations: bool = False
    report_format: str = "json"

    @classmethod
    def from_yaml(cls, path: str) -> "BenchmarkConfig":
        """Load config from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Flatten nested structure
        flat = {}

        if "dataset" in data:
            flat["dataset_path"] = data["dataset"].get("path", cls.dataset_path)
            flat["filter_type"] = data["dataset"].get("filter", cls.filter_type)
            flat["cache_dir"] = data["dataset"].get("cache_dir")
            flat["max_samples"] = data["dataset"].get("max_samples")

        if "model" in data:
            flat["n_patches_x"] = data["model"].get("patch_grid_x", cls.n_patches_x)
            flat["n_patches_y"] = data["model"].get("patch_grid_y", cls.n_patches_y)

        if "aggregation" in data:
            flat["aggregation_methods"] = data["aggregation"].get(
                "methods", cls().aggregation_methods
            )
            flat["default_aggregation"] = data["aggregation"].get(
                "default", cls.default_aggregation
            )

        if "selection" in data:
            flat["selection_methods"] = data["selection"].get(
                "methods", cls().selection_methods
            )
            flat["default_selection"] = data["selection"].get(
                "default", cls.default_selection
            )
            if "top_k" in data["selection"]:
                flat["top_k_values"] = data["selection"]["top_k"].get(
                    "values", cls().top_k_values
                )
            if "threshold" in data["selection"]:
                flat["threshold_values"] = data["selection"]["threshold"].get(
                    "values", cls().threshold_values
                )

        if "evaluation" in data:
            flat["iou_thresholds"] = data["evaluation"].get(
                "iou_thresholds", cls().iou_thresholds
            )
            flat["matching_strategy"] = data["evaluation"].get(
                "default_matching", cls.matching_strategy
            )

        if "baselines" in data:
            flat["baseline_methods"] = data["baselines"].get(
                "enabled", cls().baseline_methods
            )

        if "output" in data:
            flat["results_dir"] = data["output"].get("results_dir", cls.results_dir)
            flat["save_predictions"] = data["output"].get(
                "save_predictions", cls.save_predictions
            )
            flat["save_visualizations"] = data["output"].get(
                "save_visualizations", cls.save_visualizations
            )
            flat["report_format"] = data["output"].get(
                "report_format", cls.report_format
            )

        # Remove None values
        flat = {k: v for k, v in flat.items() if v is not None}

        return cls(**flat)


@dataclass
class SamplePrediction:
    """Prediction for a single sample."""

    sample_id: str
    query: str
    predicted_regions: List[Box]
    predicted_scores: List[float]
    ground_truth_regions: List[Box]
    aggregation_method: str
    selection_method: str
    selection_params: Dict[str, Any]


@dataclass
class BenchmarkResults:
    """Complete benchmark results."""

    config: BenchmarkConfig
    timestamp: str
    total_samples: int
    overall_metrics: AggregatedMetrics
    stratified_metrics: Dict[str, AggregatedMetrics]
    baseline_comparisons: Dict[str, Dict[str, float]]
    method_grid_results: Dict[str, AggregatedMetrics]
    predictions: Optional[List[SamplePrediction]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "total_samples": self.total_samples,
            "overall_metrics": self.overall_metrics.to_dict(),
            "stratified_metrics": {
                k: v.to_dict() for k, v in self.stratified_metrics.items()
            },
            "baseline_comparisons": self.baseline_comparisons,
            "method_grid_results": {
                k: v.to_dict() for k, v in self.method_grid_results.items()
            },
        }

    def save(self, path: str) -> None:
        """Save results to file."""
        data = self.to_dict()

        if path.endswith(".json"):
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        elif path.endswith(".yaml"):
            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            # Default to JSON
            with open(path + ".json", "w") as f:
                json.dump(data, f, indent=2)


# Type alias for model inference function
ModelInferenceFunc = Callable[
    [str, Any],  # query, image
    Tuple[NDArray[np.floating], List[NDArray[np.floating]]],  # (patch_map, token_maps)
]

# Type alias for OCR function
OCRFunc = Callable[
    [Any],  # image
    Tuple[List[Box], List[str]],  # (regions, texts)
]


class BenchmarkPipeline:
    """
    Main pipeline for running the BBox_DocVQA benchmark.

    This orchestrates:
    1. Dataset loading
    2. Model inference (similarity maps)
    3. OCR region extraction
    4. Patch-to-region aggregation
    5. Region selection
    6. Evaluation against ground truth
    7. Baseline comparisons
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        model_inference: Optional[ModelInferenceFunc] = None,
        ocr_func: Optional[OCRFunc] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            config: Benchmark configuration
            model_inference: Function to get similarity maps from model
            ocr_func: Function to extract OCR regions from image
        """
        self.config = config
        self.model_inference = model_inference
        self.ocr_func = ocr_func
        self.loader: Optional[BBoxDocVQALoader] = None
        self.results: Optional[BenchmarkResults] = None

    def load_dataset(self) -> "BenchmarkPipeline":
        """Load the benchmark dataset."""
        logger.info(f"Loading dataset from {self.config.dataset_path}")

        self.loader = BBoxDocVQALoader(
            dataset_path=self.config.dataset_path,
            cache_dir=self.config.cache_dir,
            filter_type=self.config.filter_type,
        )
        self.loader.load()

        logger.info(f"Loaded {len(self.loader)} samples")
        return self

    def run(
        self,
        samples: Optional[List[BBoxDocVQASample]] = None,
    ) -> BenchmarkResults:
        """
        Run the full benchmark pipeline.

        Args:
            samples: Optional list of samples to use (defaults to loaded dataset)

        Returns:
            BenchmarkResults with all metrics
        """
        if samples is None:
            if self.loader is None:
                self.load_dataset()
            samples = self.loader.samples

        if self.config.max_samples:
            samples = samples[: self.config.max_samples]

        logger.info(f"Running benchmark on {len(samples)} samples")

        # Results storage
        all_results: List[EvaluationResult] = []
        results_by_complexity: Dict[str, List[EvaluationResult]] = {
            c.value: [] for c in ComplexityType
        }
        predictions: List[SamplePrediction] = []

        # Grid search results
        method_grid_results: Dict[str, List[EvaluationResult]] = {}

        # Baseline results
        baseline_results: Dict[str, List[EvaluationResult]] = {
            m: [] for m in self.config.baseline_methods
        }

        matching_strategy = MatchingStrategy(self.config.matching_strategy)

        for sample in samples:
            try:
                result = self._process_sample(
                    sample,
                    matching_strategy,
                    predictions,
                    method_grid_results,
                    baseline_results,
                )
                all_results.append(result)
                results_by_complexity[sample.complexity.value].append(result)

            except Exception as e:
                logger.error(f"Error processing sample {sample.sample_id}: {e}")
                continue

        # Aggregate results
        overall_metrics = aggregate_results(all_results)
        stratified_metrics = {
            k: aggregate_results(v) for k, v in results_by_complexity.items()
        }

        # Aggregate method grid results
        grid_metrics = {
            k: aggregate_results(v) for k, v in method_grid_results.items()
        }

        # Baseline comparisons
        baseline_comparisons = {}
        for baseline_name, baseline_result_list in baseline_results.items():
            if baseline_result_list:
                baseline_agg = aggregate_results(baseline_result_list)
                baseline_comparisons[baseline_name] = compare_to_baseline(
                    overall_metrics,
                    baseline_agg,
                    metric_name="mean_mean_iou",
                )

        self.results = BenchmarkResults(
            config=self.config,
            timestamp=datetime.now().isoformat(),
            total_samples=len(samples),
            overall_metrics=overall_metrics,
            stratified_metrics=stratified_metrics,
            baseline_comparisons=baseline_comparisons,
            method_grid_results=grid_metrics,
            predictions=predictions if self.config.save_predictions else None,
        )

        return self.results

    def _process_sample(
        self,
        sample: BBoxDocVQASample,
        matching_strategy: MatchingStrategy,
        predictions: List[SamplePrediction],
        method_grid_results: Dict[str, List[EvaluationResult]],
        baseline_results: Dict[str, List[EvaluationResult]],
    ) -> EvaluationResult:
        """Process a single sample."""
        # Get ground truth boxes
        gt_boxes = [gt.box for gt in sample.ground_truth_boxes]

        # Get OCR regions and similarity maps
        if self.model_inference is not None and self.ocr_func is not None:
            # Full pipeline with real model
            regions, region_texts = self._get_ocr_regions(sample)
            token_maps = self._get_similarity_maps(sample)
        else:
            # Simulated mode for testing - use GT boxes as regions
            regions = gt_boxes
            region_texts = ["" for _ in regions]
            # Simulate perfect similarity maps
            token_maps = self._simulate_similarity_maps(regions)

        # Run with default configuration
        default_agg = AggregationMethod(self.config.default_aggregation)
        scored_regions = compute_region_scores_multi_token(
            regions,
            token_maps,
            method=default_agg,
            token_aggregation=self.config.token_aggregation,
            n_patches_x=self.config.n_patches_x,
            n_patches_y=self.config.n_patches_y,
        )

        # Apply default selection
        default_k = self.config.top_k_values[0] if self.config.top_k_values else 5
        selected = select_regions(
            scored_regions,
            SelectionMethod(self.config.default_selection),
            k=default_k,
        )

        # Get predicted boxes
        selected_indices = [idx for idx, _ in selected]
        selected_scores = [score for _, score in selected]
        predicted_boxes = [regions[i] for i in selected_indices]

        # Evaluate
        result = evaluate_sample(
            predictions=predicted_boxes,
            ground_truth=gt_boxes,
            sample_id=sample.sample_id,
            strategy=matching_strategy,
            iou_thresholds=self.config.iou_thresholds,
            scores=selected_scores,
        )

        # Save prediction
        if self.config.save_predictions:
            predictions.append(
                SamplePrediction(
                    sample_id=sample.sample_id,
                    query=sample.question,
                    predicted_regions=predicted_boxes,
                    predicted_scores=selected_scores,
                    ground_truth_regions=gt_boxes,
                    aggregation_method=self.config.default_aggregation,
                    selection_method=self.config.default_selection,
                    selection_params={"k": default_k},
                )
            )

        # Grid search over methods
        for agg_method in self.config.aggregation_methods:
            for sel_method in self.config.selection_methods:
                for k in self.config.top_k_values:
                    key = f"{agg_method}_{sel_method}_k{k}"

                    if key not in method_grid_results:
                        method_grid_results[key] = []

                    try:
                        agg = AggregationMethod(agg_method)
                        scored = compute_region_scores_multi_token(
                            regions,
                            token_maps,
                            method=agg,
                            token_aggregation=self.config.token_aggregation,
                            n_patches_x=self.config.n_patches_x,
                            n_patches_y=self.config.n_patches_y,
                        )

                        sel = SelectionMethod(sel_method)
                        selected = select_regions(scored, sel, k=k)

                        pred_boxes = [regions[i] for i, _ in selected]
                        pred_scores = [s for _, s in selected]

                        eval_result = evaluate_sample(
                            predictions=pred_boxes,
                            ground_truth=gt_boxes,
                            sample_id=sample.sample_id,
                            strategy=matching_strategy,
                            iou_thresholds=self.config.iou_thresholds,
                            scores=pred_scores,
                        )
                        method_grid_results[key].append(eval_result)

                    except Exception as e:
                        logger.debug(f"Error with method {key}: {e}")

        # Run baselines
        if self.config.run_baselines:
            baseline_preds = run_all_baselines(
                regions=regions,
                query=sample.question,
                region_texts=region_texts if region_texts else None,
                k=default_k,
                n_patches_x=self.config.n_patches_x,
                n_patches_y=self.config.n_patches_y,
            )

            for baseline_name, baseline_selected in baseline_preds.items():
                if baseline_name not in baseline_results:
                    baseline_results[baseline_name] = []

                baseline_boxes = [regions[i] for i, _ in baseline_selected]
                baseline_scores = [s for _, s in baseline_selected]

                baseline_eval = evaluate_sample(
                    predictions=baseline_boxes,
                    ground_truth=gt_boxes,
                    sample_id=sample.sample_id,
                    strategy=matching_strategy,
                    iou_thresholds=self.config.iou_thresholds,
                    scores=baseline_scores,
                )
                baseline_results[baseline_name].append(baseline_eval)

        return result

    def _get_ocr_regions(
        self,
        sample: BBoxDocVQASample,
    ) -> Tuple[List[Box], List[str]]:
        """Get OCR regions for a sample."""
        if self.ocr_func is None:
            raise ValueError("OCR function not provided")

        # Load image (first page for single-page samples)
        # This is a placeholder - actual implementation depends on data format
        image = self._load_image(sample)
        return self.ocr_func(image)

    def _get_similarity_maps(
        self,
        sample: BBoxDocVQASample,
    ) -> List[NDArray[np.floating]]:
        """Get similarity maps from model."""
        if self.model_inference is None:
            raise ValueError("Model inference function not provided")

        image = self._load_image(sample)
        _, token_maps = self.model_inference(sample.question, image)
        return token_maps

    def _load_image(self, sample: BBoxDocVQASample) -> Any:
        """Load image for a sample."""
        # Placeholder - actual implementation depends on data format
        if sample.image_paths:
            from PIL import Image

            return Image.open(sample.image_paths[0])
        return None

    def _simulate_similarity_maps(
        self,
        regions: List[Box],
    ) -> List[NDArray[np.floating]]:
        """
        Simulate similarity maps for testing.

        Creates maps where patches overlapping with regions have high scores.
        """
        # Create a single token map
        n_y = self.config.n_patches_y
        n_x = self.config.n_patches_x
        patch_map = np.zeros((n_y, n_x), dtype=np.float32)

        patch_width = 1.0 / n_x
        patch_height = 1.0 / n_y

        for region in regions:
            start_x = max(0, int(region.x1 / patch_width))
            end_x = min(n_x, int(np.ceil(region.x2 / patch_width)))
            start_y = max(0, int(region.y1 / patch_height))
            end_y = min(n_y, int(np.ceil(region.y2 / patch_height)))

            patch_map[start_y:end_y, start_x:end_x] = 1.0

        # Add some noise
        patch_map += np.random.rand(n_y, n_x) * 0.1

        return [patch_map]

    def save_results(self, path: Optional[str] = None) -> str:
        """
        Save benchmark results to file.

        Args:
            path: Output path (defaults to results_dir from config)

        Returns:
            Path to saved file
        """
        if self.results is None:
            raise RuntimeError("No results to save. Run benchmark first.")

        if path is None:
            os.makedirs(self.config.results_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = (
                ".json"
                if self.config.report_format == "json"
                else f".{self.config.report_format}"
            )
            path = os.path.join(
                self.config.results_dir,
                f"benchmark_results_{timestamp}{ext}",
            )

        self.results.save(path)
        logger.info(f"Results saved to {path}")
        return path

    def print_summary(self) -> None:
        """Print a summary of benchmark results."""
        if self.results is None:
            raise RuntimeError("No results to print. Run benchmark first.")

        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {self.results.timestamp}")
        print(f"Total samples: {self.results.total_samples}")
        print()

        print("OVERALL METRICS:")
        for name, value in sorted(self.results.overall_metrics.metrics.items()):
            if name.startswith("mean_"):
                print(f"  {name}: {value:.4f}")
        print()

        print("BY COMPLEXITY:")
        for category, metrics in self.results.stratified_metrics.items():
            if metrics.num_samples > 0:
                mean_iou = metrics.metrics.get("mean_mean_iou", 0.0)
                print(f"  {category} ({metrics.num_samples} samples): IoU={mean_iou:.4f}")
        print()

        print("BASELINE COMPARISONS:")
        for baseline, comparison in self.results.baseline_comparisons.items():
            method_val = comparison.get("method_value", 0)
            baseline_val = comparison.get("baseline_value", 0)
            improvement = comparison.get("relative_improvement", 0)
            beats = comparison.get("beats_baseline", False)
            print(
                f"  vs {baseline}: {method_val:.4f} vs {baseline_val:.4f} "
                f"({'+'if improvement >= 0 else ''}{improvement*100:.1f}%, "
                f"{'BEATS' if beats else 'LOSES'})"
            )
        print()
        print("=" * 60)
