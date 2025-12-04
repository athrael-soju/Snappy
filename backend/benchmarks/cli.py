"""
Command-line interface for running benchmarks.

Usage:
    python -m benchmarks.cli --help
    python -m benchmarks.cli run --max-samples 100 --strategies on_the_fly
    python -m benchmarks.cli report --input results.json
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from benchmarks.config import BenchmarkConfig, RetrievalStrategy
from benchmarks.runner import BenchmarkRunner, run_benchmark

# Load environment variables from .env files (searches up from current directory)
load_dotenv(override=False)  # Load from .env files in current or parent directories


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_strategies(strategies_str: str) -> List[RetrievalStrategy]:
    """Parse comma-separated strategy names."""
    strategies = []
    for name in strategies_str.split(","):
        name = name.strip().lower()
        try:
            strategies.append(RetrievalStrategy(name))
        except ValueError:
            print(f"Warning: Unknown strategy '{name}', skipping")
    return strategies or [RetrievalStrategy.ON_THE_FLY]


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Snappy Benchmark Suite - Compare document retrieval strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run benchmark
  python -m benchmarks.cli run

  # Quick test with 10 samples
  python -m benchmarks.cli run --max-samples 10

  # Filter by category
  python -m benchmarks.cli run --categories cs,math

  # Use specific LLM
  python -m benchmarks.cli run --llm-model gpt-5-nano --llm-provider openai

  # Generate report from existing results
  python -m benchmarks.cli report --input benchmark_results.json
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run benchmark")

    # Dataset options
    run_parser.add_argument(
        "--dataset",
        default="Yuwh07/BBox_DocVQA_Bench",
        help="HuggingFace dataset name or local path",
    )
    run_parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum samples to process (default: all)",
    )
    run_parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated arXiv categories to include (e.g., cs,math)",
    )
    run_parser.add_argument(
        "--cache-dir",
        default="./benchmark_cache",
        help="Directory for caching dataset",
    )

    # Strategy options
    run_parser.add_argument(
        "--strategies",
        default="on_the_fly",
        help="Comma-separated strategies to benchmark",
    )

    # Region relevance options
    run_parser.add_argument(
        "--region-threshold",
        type=float,
        default=0.3,
        help="Region relevance threshold",
    )
    run_parser.add_argument(
        "--region-top-k",
        type=int,
        default=10,
        help="Max regions to keep per page",
    )
    run_parser.add_argument(
        "--region-aggregation",
        default="max",
        choices=["max", "mean", "sum"],
        help="Region score aggregation method",
    )

    # LLM options
    run_parser.add_argument(
        "--llm-model",
        default="gpt-5-mini",
        help="OpenAI model name for RAG",
    )
    run_parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.0,
        help="LLM sampling temperature",
    )
    run_parser.add_argument(
        "--llm-max-tokens",
        type=int,
        default=512,
        help="Max tokens for LLM response",
    )

    # Service URLs
    run_parser.add_argument(
        "--colpali-url",
        default="http://localhost:7000",
        help="ColPali service URL",
    )
    run_parser.add_argument(
        "--deepseek-ocr-url",
        default="http://localhost:8200",
        help="DeepSeek OCR service URL",
    )

    # Output options
    run_parser.add_argument(
        "--output-dir",
        default="./benchmark_results",
        help="Directory for output files",
    )
    run_parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation",
    )

    # Execution options
    run_parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing",
    )
    run_parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per sample in seconds",
    )
    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report from results")
    report_parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON results file",
    )
    report_parser.add_argument(
        "--output-dir",
        default="./benchmark_results",
        help="Directory for output files",
    )
    report_parser.add_argument(
        "--latex",
        action="store_true",
        help="Generate LaTeX table",
    )
    report_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show dataset/strategy info")
    info_parser.add_argument(
        "--dataset",
        default="Yuwh07/BBox_DocVQA_Bench",
        help="Dataset to show info for",
    )

    return parser


async def cmd_run(args: argparse.Namespace) -> int:
    """Run benchmark command."""
    # Parse strategies
    strategies = parse_strategies(args.strategies)

    # Parse categories
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Create config
    config = BenchmarkConfig(
        dataset_name=args.dataset,
        cache_dir=args.cache_dir,
        max_samples=args.max_samples,
        categories=categories,
        strategies=strategies,
        region_relevance_threshold=args.region_threshold,
        region_top_k=args.region_top_k,
        region_score_aggregation=args.region_aggregation,
        llm_model=args.llm_model,
        llm_temperature=args.llm_temperature,
        llm_max_tokens=args.llm_max_tokens,
        colpali_url=args.colpali_url,
        deepseek_ocr_url=args.deepseek_ocr_url,
        output_dir=args.output_dir,
        generate_report=not args.no_report,
        batch_size=args.batch_size,
        timeout=args.timeout,
    )

    print("=" * 60)
    print("Snappy Benchmark Suite")
    print("=" * 60)
    print(f"Dataset: {config.dataset_name}")
    print(f"Samples: {config.max_samples or 'All'}")
    print(f"Strategies: {[s.value for s in strategies]}")
    print(f"LLM: OpenAI/{config.llm_model}")
    print("=" * 60)
    print()

    try:
        results = await run_benchmark(config)

        print()
        print("=" * 60)
        print("Results Summary")
        print("=" * 60)

        comparison = results.get("comparison", {})
        for strategy, metrics in comparison.items():
            print(f"\n{strategy}:")
            if "correctness" in metrics:
                print(f"  F1: {metrics['correctness'].get('f1_score', 0):.4f}")
                print(
                    f"  LLM Judge Acc: {metrics['correctness'].get('llm_judge_accuracy', 0):.2%}"
                )
            if "latency" in metrics:
                total = metrics["latency"].get("total_s", {})
                print(
                    f"  Latency: {total.get('mean', 0):.3f}s (p95: {total.get('p95', 0):.3f}s)"
                )
            if "tokens" in metrics:
                print(
                    f"  Tokens: {metrics['tokens'].get('total_tokens', {}).get('mean', 0):.0f} avg"
                )

        print()
        print(f"Total time: {results.get('total_time_seconds', 0):.1f}s")

        if "report_paths" in results:
            print("\nReports generated:")
            for fmt, path in results["report_paths"].items():
                print(f"  {fmt}: {path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Generate report from existing results."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    with open(input_path, "r") as f:
        results = json.load(f)

    print(f"Loaded results from {input_path}")

    # Generate comparison table
    comparison = results.get("results", {})
    strategies = list(comparison.keys())

    if args.latex:
        # LaTeX table
        print("\nLaTeX Table:")
        print("\\begin{table}[h]")
        print("\\centering")
        print("\\caption{Benchmark Results}")
        print("\\begin{tabular}{l" + "c" * len(strategies) + "}")
        print("\\toprule")
        print("Metric & " + " & ".join(strategies) + " \\\\")
        print("\\midrule")

        for metric in ["anls", "f1_score", "exact_match"]:
            values = []
            for s in strategies:
                val = (
                    comparison[s]
                    .get("aggregate_metrics", {})
                    .get("correctness", {})
                    .get(metric, 0)
                )
                values.append(f"{val:.3f}")
            print(f"{metric} & " + " & ".join(values) + " \\\\")

        print("\\bottomrule")
        print("\\end{tabular}")
        print("\\end{table}")
    else:
        # ASCII table
        print("\nResults Comparison:")
        print("-" * 60)
        header = "| Metric".ljust(20) + "".join(f"| {s:^15}" for s in strategies) + "|"
        print(header)
        print("-" * 60)

        for metric in ["anls", "f1_score", "exact_match"]:
            row = f"| {metric}".ljust(20)
            for s in strategies:
                val = (
                    comparison[s]
                    .get("aggregate_metrics", {})
                    .get("correctness", {})
                    .get(metric, 0)
                )
                row += f"| {val:^15.3f}"
            row += "|"
            print(row)

        print("-" * 60)

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show dataset info."""
    from benchmarks.dataset import BBoxDocVQADataset

    print(f"Loading dataset: {args.dataset}")

    try:
        dataset = BBoxDocVQADataset(dataset_name=args.dataset)
        dataset.load(max_samples=100)  # Just load a sample

        stats = dataset.get_statistics()

        print("\nDataset Statistics:")
        print(f"  Total samples: {stats.get('total_samples', 0)}")
        print(f"  Categories: {stats.get('categories', {})}")
        print(f"  Evidence types: {stats.get('evidence_types', {})}")
        print(f"  Multi-page samples: {stats.get('multi_page_samples', 0)}")
        print(f"  Multi-bbox samples: {stats.get('multi_bbox_samples', 0)}")

        return 0

    except Exception as e:
        print(f"Error loading dataset: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    verbose = getattr(args, "verbose", False)
    setup_logging(verbose)

    # Run command
    if args.command == "run":
        return asyncio.run(cmd_run(args))
    elif args.command == "report":
        return cmd_report(args)
    elif args.command == "info":
        return cmd_info(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
