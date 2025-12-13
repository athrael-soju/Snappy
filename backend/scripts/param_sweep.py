#!/usr/bin/env python3
"""Parameter sweep for ablation studies on BBox-DocVQA benchmark."""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import os
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend directory
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

# Ensure backend root is importable
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from benchmarks.dataset_runner import BenchmarkConfig, BBoxDocVQARunner

logger = logging.getLogger(__name__)

# Default dataset path
DEFAULT_DATASET_PATH = (
    BACKEND_DIR
    / "benchmarks"
    / ".eval_cache"
    / "datasets--Yuwh07--BBox_DocVQA_Bench"
    / "snapshots"
    / "8def59df907ef87d08cea036038433143509cf62"
    / "BBox_DocVQA_Bench.jsonl"
)


def load_dataset_categories(dataset_path: Path) -> dict[str, list[int]]:
    """Load dataset and group sample indices by category."""
    categories: dict[str, list[int]] = defaultdict(list)

    with open(dataset_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            record = json.loads(line)
            category = record.get("category", "unknown")
            categories[category].append(idx)

    return dict(categories)


def stratified_sample(
    categories: dict[str, list[int]],
    samples_per_category: int,
    seed: int = 42,
) -> list[int]:
    """Select fixed number of samples from each category."""
    random.seed(seed)

    selected: list[int] = []

    for category, indices in sorted(categories.items()):
        n_select = min(samples_per_category, len(indices))
        sampled = random.sample(indices, n_select)
        selected.extend(sampled)
        logger.info(f"  {category}: {n_select}/{len(indices)} samples")

    return sorted(selected)


def run_sweep(
    samples_per_category: int,
    output_dir: Path,
    embedding_model: str,
    dataset_path: Path | None = None,
    seed: int = 42,
) -> list[dict]:
    """Run parameter sweep with specified configurations."""

    # Load dataset and perform stratified sampling
    ds_path = dataset_path or DEFAULT_DATASET_PATH
    logger.info(f"Loading dataset from: {ds_path}")
    categories = load_dataset_categories(ds_path)
    logger.info(f"Found {len(categories)} categories:")

    sample_indices = stratified_sample(categories, samples_per_category, seed)
    total_samples = len(sample_indices)
    logger.info(f"Selected {total_samples} samples total (seed={seed})")

    # Parameter grid as specified
    param_grid = {
        "percentile": [25.0, 75.0],
        "token_aggregation": ["mean", "sum"],
        "region_scoring": ["weighted_avg", "max"],  # "sum" not supported, using "max"
        "min_patch_overlap": [0.1, 0.25, 0.5],
    }

    # Generate all combinations
    keys = list(param_grid.keys())
    combinations = list(itertools.product(*[param_grid[k] for k in keys]))

    total_runs = len(combinations)
    logger.info(f"Starting parameter sweep: {total_runs} configurations")
    logger.info(f"Samples per category: {samples_per_category}, Total: {total_samples}, Model: {embedding_model}")

    results = []
    sweep_start = datetime.now()

    for i, combo in enumerate(combinations, 1):
        params = dict(zip(keys, combo))

        run_name = (
            f"p{int(params['percentile'])}_"
            f"agg-{params['token_aggregation']}_"
            f"rs-{params['region_scoring']}_"
            f"mo-{params['min_patch_overlap']}"
        )

        logger.info(f"\n{'='*60}")
        logger.info(f"Run {i}/{total_runs}: {run_name}")
        logger.info(f"Params: {params}")
        logger.info(f"{'='*60}")

        config = BenchmarkConfig(
            filter_samples=sample_indices,  # Use stratified sample indices
            sample_limit=None,  # No limit - use all filtered samples
            threshold_method="percentile",
            percentile=params["percentile"],
            token_aggregation=params["token_aggregation"],
            region_scoring=params["region_scoring"],
            min_patch_overlap=params["min_patch_overlap"],
            top_k=None,  # No cap on regions
            output_dir=output_dir / run_name,
            visualize=False,
            embedding_model=embedding_model,
        )

        try:
            runner = BBoxDocVQARunner(config)
            _, summary, summary_path = runner.run()

            result = {
                "run_name": run_name,
                "params": params,
                "metrics": {
                    "mean_iou": summary["mean_iou"],
                    "iou_at_0_25": summary.get("iou_at_0_25", 0),
                    "iou_at_0_5": summary["iou_at_0_5"],
                    "iou_at_0_7": summary.get("iou_at_0_7", 0),
                    "num_samples": summary["num_samples"],
                },
                "token_stats": summary.get("token_stats", {}),
                "summary_path": str(summary_path),
                "status": "success",
            }

            logger.info(
                f"✓ {run_name}: mean_iou={summary['mean_iou']:.3f}, "
                f"iou@0.5={summary['iou_at_0_5']:.3f}"
            )

        except Exception as e:
            logger.error(f"✗ {run_name} failed: {e}")
            result = {
                "run_name": run_name,
                "params": params,
                "status": "failed",
                "error": str(e),
            }

        results.append(result)

    # Save sweep summary
    sweep_duration = (datetime.now() - sweep_start).total_seconds()
    sweep_summary = {
        "timestamp": sweep_start.isoformat(),
        "duration_seconds": sweep_duration,
        "embedding_model": embedding_model,
        "samples_per_category": samples_per_category,
        "total_samples": total_samples,
        "sample_indices": sample_indices,
        "categories": list(categories.keys()),
        "seed": seed,
        "param_grid": param_grid,
        "total_runs": total_runs,
        "successful_runs": sum(1 for r in results if r["status"] == "success"),
        "results": results,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"sweep_summary_{sweep_start.strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w") as f:
        json.dump(sweep_summary, f, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"Sweep complete: {sweep_summary['successful_runs']}/{total_runs} successful")
    logger.info(f"Duration: {sweep_duration:.1f}s")
    logger.info(f"Summary saved to: {summary_path}")

    # Print results table
    print_results_table(results)

    return results


def print_results_table(results: list[dict]) -> None:
    """Print a formatted results table."""
    successful = [r for r in results if r["status"] == "success"]
    if not successful:
        logger.warning("No successful runs to display")
        return

    # Sort by mean_iou descending
    successful.sort(key=lambda x: x["metrics"]["mean_iou"], reverse=True)

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS RANKED BY MEAN IOU")
    logger.info("=" * 80)
    logger.info(
        f"{'Rank':<5} {'Percentile':<10} {'Aggregation':<12} "
        f"{'Scoring':<12} {'MinOverlap':<10} {'MeanIoU':<8} {'IoU@0.5':<8}"
    )
    logger.info("-" * 80)

    for rank, r in enumerate(successful, 1):
        p = r["params"]
        m = r["metrics"]
        logger.info(
            f"{rank:<5} {p['percentile']:<10.0f} {p['token_aggregation']:<12} "
            f"{p['region_scoring']:<12} {p['min_patch_overlap']:<10.2f} "
            f"{m['mean_iou']:<8.3f} {m['iou_at_0_5']:<8.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run parameter sweep for ablation studies"
    )
    parser.add_argument(
        "--samples-per-category",
        type=int,
        default=10,
        help="Number of samples per category (default: 10, ~80 total for 8 categories)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks") / "runs" / "sweep",
        help="Directory to write sweep results",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=os.getenv("EMBEDDING_MODEL", "colmodernvbert"),
        help="Embedding model to use",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    run_sweep(
        samples_per_category=args.samples_per_category,
        output_dir=args.output_dir,
        embedding_model=args.embedding_model,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
