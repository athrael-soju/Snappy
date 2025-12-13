from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from benchmarks directory
BENCHMARKS_DIR = Path(__file__).resolve().parent
load_dotenv(BENCHMARKS_DIR / ".env")

# Ensure backend root is importable for config + clients
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from benchmarks.dataset_runner import (  # noqa: E402
    BenchmarkConfig,
    BBoxDocVQARunner,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a lightweight BBox-DocVQA benchmark using ColPali + DeepSeek OCR."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=None,
        help="Path to a snapshot containing BBox_DocVQA_Bench.jsonl "
        "(defaults to benchmarks/.eval_cache/... if present).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Number of samples to evaluate (default: 0, meaning no limit).",
    )
    parser.add_argument(
        "--filter-docs",
        type=str,
        nargs="+",
        default=None,
        help="Filter to specific doc names (e.g., --filter-docs 2406.05299 2411.15797).",
    )
    parser.add_argument(
        "--filter-samples",
        type=int,
        nargs="+",
        default=None,
        help="Filter to specific sample IDs (0-indexed, e.g., --filter-samples 0 5 10 42).",
    )
    parser.add_argument(
        "--method",
        choices=["adaptive", "percentile", "max", "none"],
        default="none",
        help="Region thresholding strategy.",
    )
    parser.add_argument(
        "--percentile",
        type=float,
        default=80.0,
        help="Percentile for percentile thresholding (default: 80).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional top-k cap on returned regions.",
    )
    parser.add_argument(
        "--min-overlap",
        type=float,
        default=0.0,
        help="Minimum IoU overlap with a patch to count toward region scoring.",
    )
    parser.add_argument(
        "--aggregation",
        choices=["max", "mean", "sum"],
        default="max",
        help="Token aggregation strategy for heatmap: max (MaxSim), mean, or sum (boosts overlapping areas).",
    )
    parser.add_argument(
        "--region-scoring",
        choices=["weighted_avg", "max"],
        default="weighted_avg",
        help="Region scoring method: weighted_avg (IoU-weighted average) or max (max patch score).",
    )
    parser.add_argument(
        "--deepseek-url",
        type=str,
        default=None,
        help="DeepSeek OCR base URL (default: DEEPSEEK_OCR_URL or http://localhost:8200).",
    )
    parser.add_argument(
        "--deepseek-mode",
        type=str,
        default=None,
        help="DeepSeek OCR mode (e.g., Gundam, Tiny).",
    )
    parser.add_argument(
        "--deepseek-task",
        type=str,
        default=None,
        help="DeepSeek OCR task (e.g., markdown, plain_ocr, locate).",
    )
    parser.add_argument(
        "--deepseek-timeout",
        type=int,
        default=None,
        help="DeepSeek OCR timeout in seconds (default: 180 from config, use 600 for complex documents).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks") / "runs",
        help="Directory to write benchmark results (default: benchmarks/runs).",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save per-sample visualizations (GT in green, OCR in blue, predicted in magenta).",
    )
    parser.add_argument(
        "--visualize-limit",
        type=int,
        default=None,
        help="Max visualizations to render (default: no limit). Use 0 for no visualizations.",
    )
    parser.set_defaults(visualize_heatmap=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Treat --limit 0 as "no limit" (None)
    sample_limit = args.limit if args.limit and args.limit > 0 else None

    # Get embedding model from env
    embedding_model = os.getenv("EMBEDDING_MODEL", "colmodernvbert")

    bench_config = BenchmarkConfig(
        dataset_root=args.dataset_root,
        sample_limit=sample_limit,
        filter_docs=args.filter_docs,
        filter_samples=args.filter_samples,
        threshold_method=args.method,
        percentile=args.percentile,
        top_k=args.top_k,
        min_patch_overlap=args.min_overlap,
        token_aggregation=args.aggregation,
        region_scoring=args.region_scoring,
        deepseek_url=args.deepseek_url,
        deepseek_mode=args.deepseek_mode,
        deepseek_task=args.deepseek_task,
        deepseek_timeout=args.deepseek_timeout,
        output_dir=args.output_dir,
        visualize=args.visualize,
        visualize_limit=args.visualize_limit,
        visualize_heatmap=args.visualize_heatmap,
        embedding_model=embedding_model,
    )

    runner = BBoxDocVQARunner(bench_config)
    results, summary, summary_path = runner.run()

    logging.info(
        "Benchmark complete: mean IoU=%.3f, IoU@0.5=%.3f, samples=%d, summary=%s",
        summary["mean_iou"],
        summary["iou_at_0_5"],
        summary["num_samples"],
        summary_path,
    )
    detection_summary = summary.get("detection_summary", {})
    if detection_summary:
        logging.info(
            "OCR region coverage: mean IoU=%.3f, IoU@0.5=%.3f",
            detection_summary.get("mean_iou", 0.0),
            detection_summary.get("iou_at_0_5", 0.0),
        )

    # Emit a short console-friendly table
    for res in results:
        logging.info(
            "[%s] doc=%s mean_iou=%.3f preds=%d elapsed=%.1fms",
            res.sample.category,
            res.sample.doc_name,
            res.metrics.mean_iou,
            len(res.predicted_boxes),
            res.elapsed_ms,
        )


if __name__ == "__main__":
    main()
