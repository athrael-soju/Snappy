#!/usr/bin/env python3
"""
Entry point for running the BBox_DocVQA benchmark.

This script provides a command-line interface for running the benchmark
with various configurations and options.

Usage:
    python -m benchmarks.run_bbox_docvqa --config configs/benchmarks/bbox_docvqa.yaml
    python -m benchmarks.run_bbox_docvqa --max-samples 100 --filter single_page
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the benchmark."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def create_colpali_inference_func(
    colpali_url: str = "http://localhost:7000",
    timeout: int = 300,
):
    """
    Create a function for ColPali model inference.

    Args:
        colpali_url: URL of the ColPali service
        timeout: Request timeout in seconds

    Returns:
        Function that takes (query, image) and returns (combined_map, token_maps)
    """
    import io

    import requests

    def inference(query: str, image: Any) -> Tuple[np.ndarray, List[np.ndarray]]:
        # Prepare image
        if hasattr(image, "save"):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            image_bytes = buffer.getvalue()
        else:
            image_bytes = image

        # Call interpretability endpoint
        response = requests.post(
            f"{colpali_url}/interpret",
            data={"query": query},
            files={"file": ("image.png", image_bytes, "image/png")},
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        # Parse similarity maps
        token_maps = []
        for sim_map in result.get("similarity_maps", []):
            map_data = sim_map.get("similarity_map", [])
            if map_data:
                token_maps.append(np.array(map_data))

        # Create combined map (max across tokens)
        if token_maps:
            combined_map = np.maximum.reduce(token_maps)
        else:
            n_patches_x = result.get("n_patches_x", 32)
            n_patches_y = result.get("n_patches_y", 32)
            combined_map = np.zeros((n_patches_y, n_patches_x))

        return combined_map, token_maps

    return inference


def create_deepseek_ocr_func(
    ocr_url: str = "http://localhost:8200",
    timeout: int = 120,
):
    """
    Create a function for DeepSeek OCR extraction.

    Args:
        ocr_url: URL of the DeepSeek OCR service
        timeout: Request timeout in seconds

    Returns:
        Function that takes image and returns (regions, texts)
    """
    import io

    import requests

    from benchmarks.utils.coordinates import Box, normalize_bbox_deepseek

    def ocr_extract(image: Any) -> Tuple[List[Box], List[str]]:
        # Prepare image
        if hasattr(image, "save"):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            image_bytes = buffer.getvalue()
        else:
            image_bytes = image

        # Call OCR endpoint with grounding
        response = requests.post(
            f"{ocr_url}/api/ocr",
            files={"file": ("image.png", image_bytes, "image/png")},
            data={"include_grounding": True},
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        regions = []
        texts = []

        # Parse OCR regions
        for region in result.get("regions", []):
            bbox = region.get("bbox", [])
            text = region.get("content", region.get("text", ""))

            if len(bbox) >= 4:
                # DeepSeek coordinates are 0-999
                box = normalize_bbox_deepseek(tuple(bbox[:4]))
                regions.append(box)
                texts.append(text)

        return regions, texts

    return ocr_extract


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the BBox_DocVQA benchmark for patch-to-region relevance propagation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with config file
    python -m benchmarks.run_bbox_docvqa --config configs/benchmarks/bbox_docvqa.yaml

    # Run with limited samples for testing
    python -m benchmarks.run_bbox_docvqa --max-samples 10 --filter single_page

    # Run in simulation mode (no model required)
    python -m benchmarks.run_bbox_docvqa --simulate --max-samples 50
        """,
    )

    # Config file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file",
    )

    # Dataset options
    parser.add_argument(
        "--dataset",
        type=str,
        default="Yuwh07/BBox_DocVQA_Bench",
        help="HuggingFace dataset path",
    )
    parser.add_argument(
        "--filter",
        type=str,
        choices=["single_page", "multi_page", "all"],
        default="single_page",
        help="Filter samples by page type",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum number of samples to process",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        help="Cache directory for dataset",
    )

    # Model options
    parser.add_argument(
        "--colpali-url",
        type=str,
        default="http://localhost:7000",
        help="ColPali service URL",
    )
    parser.add_argument(
        "--ocr-url",
        type=str,
        default="http://localhost:8200",
        help="DeepSeek OCR service URL",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode without real model inference",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/bbox_docvqa",
        help="Directory for output files",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "yaml", "csv"],
        default="json",
        help="Output format for results",
    )
    parser.add_argument(
        "--save-predictions",
        action="store_true",
        help="Save individual sample predictions",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Load configuration
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config = BenchmarkConfig.from_yaml(args.config)
    else:
        config = BenchmarkConfig()

    # Override with command-line arguments
    if args.dataset:
        config.dataset_path = args.dataset
    if args.filter:
        config.filter_type = args.filter
    if args.max_samples:
        config.max_samples = args.max_samples
    if args.cache_dir:
        config.cache_dir = args.cache_dir
    if args.output_dir:
        config.results_dir = args.output_dir
    if args.output_format:
        config.report_format = args.output_format
    if args.save_predictions:
        config.save_predictions = True

    # Create inference functions
    model_inference = None
    ocr_func = None

    if not args.simulate:
        try:
            logger.info("Creating model inference functions...")
            model_inference = create_colpali_inference_func(args.colpali_url)
            ocr_func = create_deepseek_ocr_func(args.ocr_url)
        except Exception as e:
            logger.warning(f"Could not create inference functions: {e}")
            logger.warning("Falling back to simulation mode")
            args.simulate = True

    if args.simulate:
        logger.info("Running in simulation mode (no real model inference)")

    # Create and run pipeline
    pipeline = BenchmarkPipeline(
        config=config,
        model_inference=model_inference,
        ocr_func=ocr_func,
    )

    try:
        logger.info("Loading dataset...")
        pipeline.load_dataset()

        logger.info("Running benchmark...")
        results = pipeline.run()

        # Print summary
        pipeline.print_summary()

        # Save results
        output_path = pipeline.save_results()
        logger.info(f"Results saved to {output_path}")

        # Check success criteria
        mean_iou = results.overall_metrics.metrics.get("mean_mean_iou", 0.0)
        recall_5 = results.overall_metrics.metrics.get("mean_recall@5", 0.0)

        logger.info(f"Mean IoU: {mean_iou:.4f} (target: > 0.40)")
        logger.info(f"Recall@5: {recall_5:.4f} (target: > 0.60)")

        # Return success if targets met
        if mean_iou > 0.40 and recall_5 > 0.60:
            logger.info("SUCCESS: Benchmark targets met!")
            return 0
        else:
            logger.warning("Benchmark targets not met")
            return 1

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
