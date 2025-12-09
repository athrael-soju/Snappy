#!/usr/bin/env python3
"""
CLI script for running BBox-DocVQA benchmarks.

Validates spatial grounding claims from arXiv:2512.02660 (Snappy)
using the BBox-DocVQA dataset.

This benchmark implements the Snappy approach:
- DeepSeek OCR extracts text regions with bounding boxes
- ColPali generates patch-level similarity maps
- Patch-to-region relevance propagation scores each OCR region

Both ColPali and DeepSeek OCR services are REQUIRED for online evaluation.

Usage:
    # Run with default settings (requires both ColPali and OCR services)
    python -m benchmarks.run_bbox_docvqa --dataset-path ./benchmarks/.eval_cache/...

    # Run specific strategies
    python -m benchmarks.run_bbox_docvqa --strategies balanced top5 knee

    # Run ablation study
    python -m benchmarks.run_bbox_docvqa --ablation

    # Run on subset for testing
    python -m benchmarks.run_bbox_docvqa --max-samples 100

    # Filter by instance type
    python -m benchmarks.run_bbox_docvqa --instance-types SPSBB

    # Ground truth baseline (no services required)
    python -m benchmarks.run_bbox_docvqa --baseline-only
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.runner import BenchmarkConfig, BenchmarkRunner, run_ablation_study
from benchmarks.strategies import STRATEGY_PRESETS


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


def get_colpali_client(url: str):
    """Initialize ColPali client."""
    try:
        from clients.colpali import ColPaliClient

        client = ColPaliClient(base_url=url)
        if client.health_check():
            logging.info(f"ColPali service connected at {url}")
            return client
        else:
            logging.warning(f"ColPali service not healthy at {url}")
            return None
    except Exception as e:
        logging.warning(f"Could not connect to ColPali: {e}")
        return None


def get_ocr_client(url: str):
    """Initialize DeepSeek OCR client for benchmarking.

    Note: This creates a minimal OCR client that doesn't require MinIO/DuckDB
    since we only need the HTTP client functionality for benchmarking.
    """
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # Check if service is available
        session = requests.Session()
        retry = Retry(
            total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
        )
        session.mount("http://", HTTPAdapter(max_retries=retry))
        session.mount("https://", HTTPAdapter(max_retries=retry))

        response = session.get(f"{url.rstrip('/')}/health", timeout=5)
        if response.status_code == 200:
            logging.info(f"DeepSeek OCR service connected at {url}")
            # Return a lightweight wrapper for benchmarking
            return BenchmarkOcrClient(url, session)
        else:
            logging.warning(f"DeepSeek OCR service not healthy at {url}")
            return None
    except Exception as e:
        logging.warning(f"Could not connect to DeepSeek OCR: {e}")
        return None


class BenchmarkOcrClient:
    """Lightweight OCR client for benchmarking (no MinIO/DuckDB dependency)."""

    def __init__(self, base_url: str, session):
        self.base_url = base_url.rstrip("/")
        self.session = session
        self.timeout = 60

    def run_ocr_image(
        self,
        image,
        *,
        include_grounding: bool = True,
        include_images: bool = False,
    ):
        """Run OCR on a PIL image and return results with bounding boxes."""
        import io

        # Convert PIL image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        files = {"image": ("image.png", buffer, "image/png")}
        data = {
            "mode": "Gundam",
            "task": "markdown",
            "include_grounding": str(include_grounding).lower(),
            "include_images": str(include_images).lower(),
        }

        response = self.session.post(
            f"{self.base_url}/api/ocr",
            files=files,
            data=data,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def is_enabled(self) -> bool:
        return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run BBox-DocVQA benchmark for spatial grounding evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic benchmark run
  python -m benchmarks.run_bbox_docvqa --dataset-path ./data/bbox_docvqa

  # Test with limited samples
  python -m benchmarks.run_bbox_docvqa --max-samples 50 --strategies top5

  # Run ablation study
  python -m benchmarks.run_bbox_docvqa --ablation --max-samples 100

  # Evaluate specific instance types
  python -m benchmarks.run_bbox_docvqa --instance-types SPSBB SPMBB
        """,
    )

    # Dataset arguments
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="benchmarks/.eval_cache/datasets--Yuwh07--BBox_DocVQA_Bench/snapshots/8def59df907ef87d08cea036038433143509cf62",
        help="Path to BBox-DocVQA dataset directory",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        type=str,
        default=None,
        help="Filter to specific categories (cs, econ, eess, math, physics, q-bio, q-fin, stat)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to evaluate (for testing)",
    )

    # Strategy arguments
    parser.add_argument(
        "--strategies",
        nargs="+",
        type=str,
        default=["all"],
        choices=list(STRATEGY_PRESETS.keys()),
        help="Filtering strategy (default: 'all' returns all OCR regions)",
    )

    # Evaluation settings
    parser.add_argument(
        "--score-aggregation",
        type=str,
        default="iou_weighted",
        choices=["max", "mean", "iou_weighted"],
        help="How to aggregate patch scores for regions",
    )
    parser.add_argument(
        "--token-aggregation",
        type=str,
        default="max",
        choices=["max", "mean"],
        help="How to aggregate scores across query tokens",
    )

    # Instance filtering
    parser.add_argument(
        "--instance-types",
        nargs="+",
        type=str,
        default=None,
        choices=["SPSBB", "SPMBB", "MPMBB"],
        help="Filter to specific instance types",
    )
    parser.add_argument(
        "--subimg-types",
        nargs="+",
        type=str,
        default=None,
        choices=["text", "table", "image"],
        help="Filter to specific sub-image types",
    )

    # ColPali configuration
    parser.add_argument(
        "--colpali-url",
        type=str,
        default="http://localhost:7000",
        help="ColPali service URL",
    )

    # OCR configuration
    parser.add_argument(
        "--ocr-url",
        type=str,
        default="http://localhost:8200",
        help="DeepSeek OCR service URL",
    )

    # Output settings
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmarks/runs",
        help="Directory for output files",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Name for this benchmark run",
    )
    parser.add_argument(
        "--no-save-predictions",
        action="store_true",
        help="Don't save detailed predictions",
    )

    # Run modes
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Only run ground truth baseline evaluation",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run ablation study over aggregation methods",
    )
    parser.add_argument(
        "--offline",
        type=str,
        default=None,
        help="Path to precomputed similarity maps for offline evaluation",
    )

    # Misc
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without running",
    )

    return parser.parse_args()


def add_custom_strategies(strategies: list) -> list:
    """Add custom threshold strategies if specified."""
    result = []
    for s in strategies:
        if s.startswith("threshold_"):
            # Parse threshold value
            try:
                threshold = float(s.split("_")[1])
                from benchmarks.strategies import ThresholdFilter

                STRATEGY_PRESETS[s] = ThresholdFilter(threshold=threshold)
            except (IndexError, ValueError):
                logging.warning(f"Invalid threshold strategy: {s}")
                continue
        result.append(s)
    return result


async def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # Add custom strategies
    strategies = add_custom_strategies(args.strategies)

    # Create configuration
    config = BenchmarkConfig(
        dataset_path=args.dataset_path,
        categories=args.categories,
        max_samples=args.max_samples,
        strategies=strategies,
        score_aggregation=args.score_aggregation,
        token_aggregation=args.token_aggregation,
        colpali_url=args.colpali_url,
        ocr_url=args.ocr_url,
        output_dir=args.output_dir,
        run_name=args.run_name,
        save_predictions=not args.no_save_predictions,
        instance_types=args.instance_types,
        subimg_types=args.subimg_types,
    )

    # Dry run - just show config
    if args.dry_run:
        print("\nBenchmark Configuration (Snappy approach):")
        print("=" * 50)
        print(f"Dataset: {config.dataset_path}")
        print(f"Categories: {config.categories or 'all'}")
        print(f"Max samples: {config.max_samples or 'all'}")
        print(f"Strategies: {config.strategies}")
        print(f"Score aggregation: {config.score_aggregation}")
        print(f"Token aggregation: {config.token_aggregation}")
        print(f"Candidate mode: OCR regions (Snappy approach)")
        print(f"ColPali URL: {config.colpali_url}")
        print(f"OCR URL: {config.ocr_url}")
        print(f"Instance types: {config.instance_types or 'all'}")
        print(f"Output: {config.output_dir}/{config.run_name}")
        print("=" * 50)
        return 0

    # Initialize ColPali and OCR clients (both required for online evaluation)
    colpali_client = None
    ocr_client = None

    if not args.offline and not args.baseline_only:
        # ColPali is required
        colpali_client = get_colpali_client(args.colpali_url)
        if colpali_client is None:
            logger.error(
                "ColPali service not available. Use --offline with precomputed maps "
                "or --baseline-only for ground truth evaluation."
            )
            return 1

        # OCR is required for the Snappy approach
        ocr_client = get_ocr_client(args.ocr_url)
        if ocr_client is None:
            logger.error(
                "DeepSeek OCR service not available. Both ColPali and OCR are required "
                "for the Snappy benchmark. Use --baseline-only for ground truth evaluation."
            )
            return 1
        logger.info("Using DeepSeek OCR for region extraction (Snappy approach)")

    # Initialize runner
    try:
        runner = BenchmarkRunner(config, colpali_client, ocr_client)
    except FileNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        return 1

    # Print dataset statistics
    stats = runner.dataset.get_statistics()
    print("\nDataset Statistics:")
    print("=" * 50)
    print(f"Total samples: {stats['total_samples']}")
    print(f"Unique documents: {stats['unique_documents']}")
    print(f"Instance types: {stats['instance_types']}")
    print(f"Categories: {stats['categories']}")
    print(f"Sub-image types: {stats['subimg_types']}")
    print("=" * 50)

    # Run baseline if requested
    if args.baseline_only:
        logger.info("Running ground truth baseline evaluation")
        baseline_results = runner.run_ground_truth_baseline()
        print("\nGround Truth Baseline Results:")
        print("=" * 50)
        print(f"Mean IoU: {baseline_results.overall.mean_iou:.3f}")
        print(f"IoU@0.5: {baseline_results.overall.iou_at_50:.3f}")
        print(f"IoU@0.7: {baseline_results.overall.iou_at_70:.3f}")
        print(f"F1: {baseline_results.overall.f1:.3f}")
        return 0

    # Run ablation study if requested
    if args.ablation:
        logger.info("Running ablation study")
        _ = run_ablation_study(config, colpali_client, ocr_client)
        print("\nAblation Study Complete")
        print(f"Results saved to {config.output_dir}")
        return 0

    # Run main evaluation
    if args.offline:
        logger.info(f"Running offline evaluation with maps from {args.offline}")
        _ = runner.run_offline_with_maps(args.offline)
    else:
        logger.info("Running online evaluation with ColPali API")
        _ = await runner.run_online()

    print(f"\nBenchmark complete. Results saved to {runner.output_dir}")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
