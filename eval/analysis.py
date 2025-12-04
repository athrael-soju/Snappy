"""
Analysis and visualization for benchmark results.

Provides tools for:
- Threshold sensitivity analysis
- Aggregation method comparison
- Results visualization
- Statistical significance testing
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def load_results(results_path: Path) -> List[Dict[str, Any]]:
    """Load per-sample results from JSON file."""
    with open(results_path) as f:
        return json.load(f)


def load_aggregated(aggregated_path: Path) -> Dict[str, Any]:
    """Load aggregated results from JSON file."""
    with open(aggregated_path) as f:
        return json.load(f)


def filter_results(
    results: List[Dict[str, Any]],
    condition: Optional[str] = None,
    aggregation: Optional[str] = None,
    threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Filter results by condition, aggregation, or threshold."""
    filtered = results
    if condition is not None:
        filtered = [r for r in filtered if r["condition"] == condition]
    if aggregation is not None:
        filtered = [r for r in filtered if r.get("aggregation") == aggregation]
    if threshold is not None:
        filtered = [r for r in filtered if r.get("threshold") == threshold]
    return filtered


def compute_threshold_curve(
    results: List[Dict[str, Any]],
    aggregation: str = "max",
    metric: str = "anls",
) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute metric values across thresholds.

    Args:
        results: Per-sample results
        aggregation: Aggregation method to analyze
        metric: Metric to track

    Returns:
        (thresholds, means, stds)
    """
    # Get unique thresholds
    thresholds = sorted(
        set(
            r["threshold"]
            for r in results
            if r["condition"] == "hybrid" and r["aggregation"] == aggregation
        )
    )

    means = []
    stds = []

    for t in thresholds:
        values = [
            r[metric]
            for r in results
            if r["condition"] == "hybrid"
            and r["aggregation"] == aggregation
            and r["threshold"] == t
        ]
        if values:
            means.append(np.mean(values))
            stds.append(np.std(values))
        else:
            means.append(0.0)
            stds.append(0.0)

    return thresholds, means, stds


def compute_aggregation_comparison(
    results: List[Dict[str, Any]],
    threshold: float = 0.3,
    metrics: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Compare aggregation methods at a fixed threshold.

    Args:
        results: Per-sample results
        threshold: Threshold to compare at
        metrics: List of metrics to compare

    Returns:
        {aggregation: {metric: mean}}
    """
    if metrics is None:
        metrics = ["anls", "iou_at_1", "iou_at_k", "precision_at_5", "recall", "context_tokens"]

    aggregations = ["max", "mean", "sum"]
    comparison = {}

    for agg in aggregations:
        filtered = filter_results(
            results, condition="hybrid", aggregation=agg, threshold=threshold
        )
        if not filtered:
            continue

        comparison[agg] = {}
        for metric in metrics:
            values = [r[metric] for r in filtered if metric in r]
            comparison[agg][metric] = float(np.mean(values)) if values else 0.0

    return comparison


def compute_condition_comparison(
    results: List[Dict[str, Any]],
    hybrid_aggregation: str = "max",
    hybrid_threshold: float = 0.3,
    metrics: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Compare all conditions.

    Args:
        results: Per-sample results
        hybrid_aggregation: Aggregation for hybrid condition
        hybrid_threshold: Threshold for hybrid condition
        metrics: List of metrics to compare

    Returns:
        {condition: {metric: mean}}
    """
    if metrics is None:
        metrics = ["anls", "iou_at_1", "iou_at_k", "precision_at_5", "recall", "context_tokens", "latency_ms"]

    comparison = {}

    # Get unique conditions
    conditions = set(r["condition"] for r in results)

    for condition in conditions:
        if condition == "hybrid":
            filtered = filter_results(
                results,
                condition="hybrid",
                aggregation=hybrid_aggregation,
                threshold=hybrid_threshold,
            )
            key = f"hybrid ({hybrid_aggregation}, t={hybrid_threshold})"
        else:
            filtered = filter_results(results, condition=condition)
            key = condition

        if not filtered:
            continue

        comparison[key] = {}
        for metric in metrics:
            values = [r[metric] for r in filtered if metric in r]
            comparison[key][metric] = float(np.mean(values)) if values else 0.0

    return comparison


def paired_bootstrap_test(
    values_a: List[float],
    values_b: List[float],
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """
    Perform paired bootstrap significance test.

    Args:
        values_a: Values from condition A
        values_b: Values from condition B (same samples)
        n_bootstrap: Number of bootstrap samples
        seed: Random seed

    Returns:
        (mean_diff, ci_lower, ci_upper)
    """
    np.random.seed(seed)

    n = len(values_a)
    if n != len(values_b):
        raise ValueError("Value lists must have same length")

    diffs = np.array(values_a) - np.array(values_b)
    observed_diff = np.mean(diffs)

    # Bootstrap
    bootstrap_diffs = []
    for _ in range(n_bootstrap):
        indices = np.random.choice(n, size=n, replace=True)
        bootstrap_diff = np.mean(diffs[indices])
        bootstrap_diffs.append(bootstrap_diff)

    bootstrap_diffs = np.array(bootstrap_diffs)
    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)

    return float(observed_diff), float(ci_lower), float(ci_upper)


def compute_significance_tests(
    results: List[Dict[str, Any]],
    baseline_condition: str = "page_only",
    test_aggregation: str = "max",
    test_threshold: float = 0.3,
    metric: str = "anls",
) -> Dict[str, Tuple[float, float, float]]:
    """
    Compute significance tests comparing hybrid to baselines.

    Args:
        results: Per-sample results
        baseline_condition: Baseline to compare against
        test_aggregation: Aggregation for hybrid
        test_threshold: Threshold for hybrid
        metric: Metric to compare

    Returns:
        {comparison_name: (mean_diff, ci_lower, ci_upper)}
    """
    # Get sample IDs
    sample_ids = sorted(set(r["sample_id"] for r in results))

    # Build value dictionaries by sample_id
    def get_values(condition: str, agg: Optional[str] = None, thresh: Optional[float] = None):
        filtered = filter_results(results, condition=condition, aggregation=agg, threshold=thresh)
        return {r["sample_id"]: r[metric] for r in filtered}

    hybrid_values = get_values("hybrid", test_aggregation, test_threshold)

    comparisons = {}

    # Compare against each baseline
    for condition in ["page_only", "ocr_bm25", "ocr_dense"]:
        baseline_values = get_values(condition)

        # Get paired values
        paired_ids = set(hybrid_values.keys()) & set(baseline_values.keys())
        if len(paired_ids) < 10:
            continue

        hybrid_list = [hybrid_values[sid] for sid in paired_ids]
        baseline_list = [baseline_values[sid] for sid in paired_ids]

        diff, ci_low, ci_high = paired_bootstrap_test(hybrid_list, baseline_list)
        comparisons[f"hybrid_vs_{condition}"] = (diff, ci_low, ci_high)

    return comparisons


def generate_results_table(
    aggregated: Dict[str, Any],
    metrics: Optional[List[str]] = None,
) -> str:
    """
    Generate a markdown table of results.

    Args:
        aggregated: Aggregated results
        metrics: Metrics to include

    Returns:
        Markdown table string
    """
    if metrics is None:
        metrics = ["anls", "iou_at_1", "iou_at_k", "precision_at_5", "recall", "context_tokens"]

    # Build header
    header = "| Condition |"
    for metric in metrics:
        header += f" {metric} |"
    header += "\n"

    separator = "|" + "----|" * (len(metrics) + 1) + "\n"

    # Build rows
    rows = ""
    for key in sorted(aggregated.keys()):
        data = aggregated[key]
        row = f"| {key} |"
        for metric in metrics:
            mean_key = f"{metric}_mean"
            std_key = f"{metric}_std"
            if mean_key in data:
                mean = data[mean_key]
                std = data.get(std_key, 0)
                if metric == "context_tokens":
                    row += f" {mean:.0f} |"
                else:
                    row += f" {mean:.3f} +/- {std:.3f} |"
            else:
                row += " - |"
        rows += row + "\n"

    return header + separator + rows


def plot_threshold_sensitivity(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (12, 8),
) -> None:
    """
    Plot threshold sensitivity for all aggregation methods.

    Args:
        results: Per-sample results
        output_path: Path to save plot (None = display)
        figsize: Figure size
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib required for plotting")
        return

    fig, axes = plt.subplots(2, 3, figsize=figsize)
    axes = axes.flatten()

    metrics = ["anls", "iou_at_1", "iou_at_k", "precision_at_5", "recall", "context_tokens"]
    aggregations = ["max", "mean", "sum"]
    colors = {"max": "blue", "mean": "green", "sum": "orange"}

    for idx, metric in enumerate(metrics):
        ax = axes[idx]

        for agg in aggregations:
            thresholds, means, stds = compute_threshold_curve(results, agg, metric)
            means = np.array(means)
            stds = np.array(stds)

            ax.plot(thresholds, means, label=agg, color=colors[agg], marker="o")
            ax.fill_between(
                thresholds,
                means - stds,
                means + stds,
                alpha=0.2,
                color=colors[agg],
            )

        ax.set_xlabel("Threshold")
        ax.set_ylabel(metric)
        ax.set_title(f"{metric} vs Threshold")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved plot to {output_path}")
    else:
        plt.show()


def plot_condition_comparison(
    results: List[Dict[str, Any]],
    hybrid_aggregation: str = "max",
    hybrid_threshold: float = 0.3,
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> None:
    """
    Plot bar chart comparing conditions.

    Args:
        results: Per-sample results
        hybrid_aggregation: Aggregation for hybrid
        hybrid_threshold: Threshold for hybrid
        output_path: Path to save plot
        figsize: Figure size
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib required for plotting")
        return

    comparison = compute_condition_comparison(
        results, hybrid_aggregation, hybrid_threshold
    )

    metrics = ["anls", "iou_at_1", "precision_at_5", "recall"]
    conditions = list(comparison.keys())

    x = np.arange(len(conditions))
    width = 0.2
    offsets = np.linspace(-width * 1.5, width * 1.5, len(metrics))

    fig, ax = plt.subplots(figsize=figsize)

    for i, metric in enumerate(metrics):
        values = [comparison[c].get(metric, 0) for c in conditions]
        ax.bar(x + offsets[i], values, width, label=metric)

    ax.set_xlabel("Condition")
    ax.set_ylabel("Score")
    ax.set_title("Condition Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved plot to {output_path}")
    else:
        plt.show()


def plot_efficiency_tradeoff(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (8, 6),
) -> None:
    """
    Plot ANLS vs context tokens trade-off.

    Args:
        results: Per-sample results
        output_path: Path to save plot
        figsize: Figure size
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib required for plotting")
        return

    fig, ax = plt.subplots(figsize=figsize)

    conditions = set(r["condition"] for r in results)
    colors = {
        "hybrid": "blue",
        "page_only": "red",
        "ocr_bm25": "green",
        "ocr_dense": "purple",
    }
    markers = {"max": "o", "mean": "s", "sum": "^"}

    for condition in conditions:
        if condition == "hybrid":
            for agg in ["max", "mean", "sum"]:
                thresholds = sorted(
                    set(
                        r["threshold"]
                        for r in results
                        if r["condition"] == "hybrid" and r["aggregation"] == agg
                    )
                )

                anls_values = []
                token_values = []

                for t in thresholds:
                    filtered = filter_results(
                        results, condition="hybrid", aggregation=agg, threshold=t
                    )
                    if filtered:
                        anls_values.append(np.mean([r["anls"] for r in filtered]))
                        token_values.append(np.mean([r["context_tokens"] for r in filtered]))

                ax.plot(
                    token_values,
                    anls_values,
                    label=f"hybrid ({agg})",
                    color=colors["hybrid"],
                    marker=markers[agg],
                    linestyle="--" if agg != "max" else "-",
                )
        else:
            filtered = filter_results(results, condition=condition)
            if filtered:
                anls = np.mean([r["anls"] for r in filtered])
                tokens = np.mean([r["context_tokens"] for r in filtered])
                ax.scatter(
                    tokens,
                    anls,
                    label=condition,
                    color=colors.get(condition, "gray"),
                    s=100,
                    marker="*",
                )

    ax.set_xlabel("Context Tokens")
    ax.set_ylabel("ANLS")
    ax.set_title("Efficiency vs Quality Trade-off")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved plot to {output_path}")
    else:
        plt.show()


def generate_analysis_report(
    results_path: Path,
    output_dir: Path,
    hybrid_aggregation: str = "max",
    hybrid_threshold: float = 0.3,
) -> str:
    """
    Generate a complete analysis report.

    Args:
        results_path: Path to per-sample results JSON
        output_dir: Directory to save plots
        hybrid_aggregation: Aggregation for comparisons
        hybrid_threshold: Threshold for comparisons

    Returns:
        Markdown report string
    """
    results = load_results(results_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = "# Evaluation Analysis Report\n\n"

    # Condition comparison
    report += "## Condition Comparison\n\n"
    comparison = compute_condition_comparison(
        results, hybrid_aggregation, hybrid_threshold
    )

    # Build comparison table
    metrics = ["anls", "iou_at_1", "iou_at_k", "precision_at_5", "recall", "context_tokens", "latency_ms"]
    header = "| Condition |" + " | ".join(metrics) + " |\n"
    separator = "|" + " --- |" * (len(metrics) + 1) + "\n"
    rows = ""
    for cond, data in comparison.items():
        row = f"| {cond} |"
        for m in metrics:
            val = data.get(m, 0)
            if m in ["context_tokens", "latency_ms"]:
                row += f" {val:.0f} |"
            else:
                row += f" {val:.3f} |"
        rows += row + "\n"

    report += header + separator + rows + "\n"

    # Aggregation comparison
    report += "## Aggregation Method Comparison (at threshold={:.1f})\n\n".format(
        hybrid_threshold
    )
    agg_comparison = compute_aggregation_comparison(results, hybrid_threshold)

    header = "| Aggregation |" + " | ".join(metrics) + " |\n"
    separator = "|" + " --- |" * (len(metrics) + 1) + "\n"
    rows = ""
    for agg, data in agg_comparison.items():
        row = f"| {agg} |"
        for m in metrics:
            val = data.get(m, 0)
            if m in ["context_tokens", "latency_ms"]:
                row += f" {val:.0f} |"
            else:
                row += f" {val:.3f} |"
        rows += row + "\n"

    report += header + separator + rows + "\n"

    # Statistical significance
    report += "## Statistical Significance (ANLS)\n\n"
    sig_tests = compute_significance_tests(
        results, "page_only", hybrid_aggregation, hybrid_threshold, "anls"
    )

    report += "| Comparison | Mean Diff | 95% CI |\n"
    report += "| --- | --- | --- |\n"
    for name, (diff, ci_low, ci_high) in sig_tests.items():
        sig = "*" if ci_low > 0 or ci_high < 0 else ""
        report += f"| {name} | {diff:+.3f}{sig} | [{ci_low:.3f}, {ci_high:.3f}] |\n"
    report += "\n*significant at p<0.05\n\n"

    # Generate plots
    try:
        plot_threshold_sensitivity(results, output_dir / "threshold_sensitivity.png")
        plot_condition_comparison(
            results, hybrid_aggregation, hybrid_threshold,
            output_dir / "condition_comparison.png"
        )
        plot_efficiency_tradeoff(results, output_dir / "efficiency_tradeoff.png")

        report += "## Plots\n\n"
        report += "- [Threshold Sensitivity](threshold_sensitivity.png)\n"
        report += "- [Condition Comparison](condition_comparison.png)\n"
        report += "- [Efficiency Trade-off](efficiency_tradeoff.png)\n"
    except Exception as e:
        logger.warning(f"Failed to generate plots: {e}")
        report += "## Plots\n\nPlot generation failed. Install matplotlib for visualizations.\n"

    # Save report
    report_path = output_dir / "analysis_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"Saved analysis report to {report_path}")
    return report


def main():
    """CLI entry point for analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze benchmark results")
    parser.add_argument(
        "results",
        type=Path,
        help="Path to per-sample results JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="eval/analysis",
        help="Output directory for plots and report",
    )
    parser.add_argument(
        "--aggregation",
        type=str,
        default="max",
        choices=["max", "mean", "sum"],
        help="Aggregation method for comparisons",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Threshold for comparisons",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    report = generate_analysis_report(
        args.results,
        args.output_dir,
        args.aggregation,
        args.threshold,
    )

    print(report)


if __name__ == "__main__":
    main()
