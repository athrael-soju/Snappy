"""
Report generator for benchmark results.

Generates:
- JSON results files
- Markdown summary reports
- CSV exports for analysis
- Comparison tables
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmarks.metrics import MetricsCollector, SampleResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate benchmark reports in multiple formats.
    """

    def __init__(self, output_dir: str = "./benchmark_results"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_full_report(
        self,
        metrics_collector: MetricsCollector,
        config: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate all report formats.

        Args:
            metrics_collector: Collector with benchmark results
            config: Benchmark configuration

        Returns:
            Dictionary mapping format to file path
        """
        report_paths = {}

        # JSON results
        json_path = self._generate_json_report(metrics_collector, config)
        report_paths["json"] = str(json_path)

        # Markdown summary
        md_path = self._generate_markdown_report(metrics_collector, config)
        report_paths["markdown"] = str(md_path)

        # CSV export
        csv_path = self._generate_csv_export(metrics_collector)
        report_paths["csv"] = str(csv_path)

        logger.info(f"Reports generated in {self.output_dir}")
        return report_paths

    def _generate_json_report(
        self,
        metrics_collector: MetricsCollector,
        config: Dict[str, Any],
    ) -> Path:
        """Generate JSON report with all results."""
        report = {
            "metadata": {
                "timestamp": self._timestamp,
                "config": config,
            },
            "results": {},
        }

        # Add per-strategy results
        comparison = metrics_collector.compare_strategies()
        for strategy, metrics in comparison.items():
            report["results"][strategy] = {
                "aggregate_metrics": metrics,
                "samples": [
                    self._sample_to_dict(s)
                    for s in metrics_collector.get_strategy_results(strategy)
                ],
            }

        # Save JSON
        json_path = self.output_dir / f"benchmark_results_{self._timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        return json_path

    def _generate_markdown_report(
        self,
        metrics_collector: MetricsCollector,
        config: Dict[str, Any],
    ) -> Path:
        """Generate Markdown summary report."""
        comparison = metrics_collector.compare_strategies()
        strategies = list(comparison.keys())

        lines = [
            "# Benchmark Results Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            "",
            f"- **Dataset:** {config.get('dataset_name', 'N/A')}",
            f"- **Samples:** {config.get('max_samples', 'All')}",
            f"- **Top-K:** {config.get('top_k', 5)}",
            f"- **LLM:** {config.get('llm_model', 'N/A')}",
            "",
            "## Summary Comparison",
            "",
        ]

        # Comparison table
        if strategies:
            lines.append("| Metric | " + " | ".join(strategies) + " |")
            lines.append("|--------|" + "|".join(["--------"] * len(strategies)) + "|")

            # Correctness metrics
            for metric in ["exact_match", "f1_score", "anls"]:
                values = []
                for s in strategies:
                    val = comparison[s].get("correctness", {}).get(metric, 0)
                    values.append(f"{val:.3f}")
                lines.append(f"| {metric} | " + " | ".join(values) + " |")

            # Latency metrics
            for metric in ["total_ms", "retrieval_ms"]:
                values = []
                for s in strategies:
                    val = (
                        comparison[s]
                        .get("latency", {})
                        .get(metric, {})
                        .get("mean", 0)
                    )
                    values.append(f"{val:.1f}")
                lines.append(f"| {metric} (mean) | " + " | ".join(values) + " |")

            # Token metrics
            for metric in ["input_tokens", "output_tokens"]:
                values = []
                for s in strategies:
                    val = comparison[s].get("tokens", {}).get(metric, {}).get("mean", 0)
                    values.append(f"{val:.0f}")
                lines.append(f"| {metric} (mean) | " + " | ".join(values) + " |")

        # Detailed per-strategy sections
        lines.extend(["", "## Detailed Results", ""])

        for strategy in strategies:
            metrics = comparison[strategy]
            lines.extend(
                [
                    f"### {strategy}",
                    "",
                    f"**Samples:** {metrics.get('successful_samples', 0)} / {metrics.get('total_samples', 0)}",
                    f"**Error Rate:** {metrics.get('error_rate', 0):.2%}",
                    "",
                ]
            )

            # Correctness details
            if "correctness" in metrics:
                lines.extend(["#### Correctness Metrics", ""])
                for name, value in metrics["correctness"].items():
                    lines.append(f"- **{name}:** {value:.4f}")
                lines.append("")

            # Latency details
            if "latency" in metrics:
                lines.extend(["#### Latency Metrics (ms)", ""])
                for name, stats in metrics["latency"].items():
                    lines.append(
                        f"- **{name}:** mean={stats['mean']:.1f}, "
                        f"p50={stats['p50']:.1f}, p95={stats['p95']:.1f}"
                    )
                lines.append("")

            # Retrieval details
            if "retrieval" in metrics:
                lines.extend(["#### Retrieval Metrics", ""])
                for name, value in metrics["retrieval"].items():
                    lines.append(f"- **{name}:** {value:.4f}")
                lines.append("")

        # Save Markdown
        md_path = self.output_dir / f"benchmark_report_{self._timestamp}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return md_path

    def _generate_csv_export(
        self,
        metrics_collector: MetricsCollector,
    ) -> Path:
        """Generate CSV export of sample-level results."""
        import csv

        csv_path = self.output_dir / f"benchmark_samples_{self._timestamp}.csv"

        # Collect all samples
        all_samples = []
        for strategy, results in metrics_collector.results.items():
            for result in results:
                row = {
                    "strategy": strategy,
                    "sample_id": result.sample_id,
                    "query": result.query,
                    "ground_truth": result.ground_truth,
                    "predicted_answer": result.predicted_answer,
                    "exact_match": result.correctness.exact_match,
                    "f1_score": result.correctness.f1_score,
                    "anls": result.correctness.anls,
                    "retrieval_ms": result.latency.retrieval_ms,
                    "llm_inference_ms": result.latency.llm_inference_ms,
                    "total_ms": result.latency.total_ms,
                    "input_tokens": result.tokens.input_tokens,
                    "output_tokens": result.tokens.output_tokens,
                    "hit": result.retrieval.hit,
                    "mrr": result.retrieval.reciprocal_rank,
                    "error": result.error or "",
                }
                all_samples.append(row)

        if all_samples:
            fieldnames = list(all_samples[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_samples)

        return csv_path

    def _sample_to_dict(self, sample: SampleResult) -> Dict[str, Any]:
        """Convert SampleResult to dictionary."""
        return {
            "sample_id": sample.sample_id,
            "query": sample.query,
            "ground_truth": sample.ground_truth,
            "predicted_answer": sample.predicted_answer,
            "strategy": sample.strategy,
            "latency": {
                "retrieval_ms": sample.latency.retrieval_ms,
                "llm_inference_ms": sample.latency.llm_inference_ms,
                "total_ms": sample.latency.total_ms,
                "region_filtering_ms": sample.latency.region_filtering_ms,
                "embedding_ms": sample.latency.embedding_ms,
            },
            "tokens": {
                "input_tokens": sample.tokens.input_tokens,
                "output_tokens": sample.tokens.output_tokens,
                "total_tokens": sample.tokens.total_tokens,
            },
            "retrieval": {
                "hit": sample.retrieval.hit,
                "reciprocal_rank": sample.retrieval.reciprocal_rank,
                "precision_at_k": sample.retrieval.precision_at_k,
                "recall_at_k": sample.retrieval.recall_at_k,
                "bbox_iou": sample.retrieval.bbox_iou,
            },
            "correctness": {
                "exact_match": sample.correctness.exact_match,
                "f1_score": sample.correctness.f1_score,
                "anls": sample.correctness.anls,
                "semantic_similarity": sample.correctness.semantic_similarity,
            },
            "error": sample.error,
            "retrieved_context": sample.retrieved_context,
            "retrieved_regions": sample.retrieved_regions,
        }

    def generate_comparison_table(
        self,
        metrics_collector: MetricsCollector,
        latex: bool = False,
    ) -> str:
        """
        Generate a comparison table for paper/documentation.

        Args:
            metrics_collector: Collector with results
            latex: If True, output LaTeX format

        Returns:
            Table as string
        """
        comparison = metrics_collector.compare_strategies()
        strategies = list(comparison.keys())

        if latex:
            return self._generate_latex_table(comparison, strategies)
        else:
            return self._generate_ascii_table(comparison, strategies)

    def _generate_latex_table(
        self, comparison: Dict[str, Any], strategies: List[str]
    ) -> str:
        """Generate LaTeX table."""
        lines = [
            "\\begin{table}[h]",
            "\\centering",
            "\\caption{Benchmark Results Comparison}",
            "\\begin{tabular}{l" + "c" * len(strategies) + "}",
            "\\toprule",
            "Metric & " + " & ".join(strategies) + " \\\\",
            "\\midrule",
        ]

        # Add metrics
        metrics_to_show = [
            ("Exact Match", "correctness", "exact_match"),
            ("F1 Score", "correctness", "f1_score"),
            ("ANLS", "correctness", "anls"),
            ("Latency (ms)", "latency", "total_ms"),
            ("Input Tokens", "tokens", "input_tokens"),
        ]

        for display_name, category, metric in metrics_to_show:
            values = []
            for s in strategies:
                if category == "latency":
                    val = (
                        comparison[s]
                        .get(category, {})
                        .get(metric, {})
                        .get("mean", 0)
                    )
                elif category == "tokens":
                    val = comparison[s].get(category, {}).get(metric, {}).get("mean", 0)
                else:
                    val = comparison[s].get(category, {}).get(metric, 0)
                values.append(f"{val:.3f}" if val < 10 else f"{val:.1f}")
            lines.append(f"{display_name} & " + " & ".join(values) + " \\\\")

        lines.extend(
            [
                "\\bottomrule",
                "\\end{tabular}",
                "\\end{table}",
            ]
        )

        return "\n".join(lines)

    def _generate_ascii_table(
        self, comparison: Dict[str, Any], strategies: List[str]
    ) -> str:
        """Generate ASCII table."""
        # Calculate column widths
        col_width = max(15, max(len(s) for s in strategies) + 2)

        lines = [
            "+" + "-" * 20 + ("+" + "-" * col_width) * len(strategies) + "+",
            "| Metric" + " " * 13 + "".join(f"| {s:^{col_width-2}} " for s in strategies) + "|",
            "+" + "=" * 20 + ("+" + "=" * col_width) * len(strategies) + "+",
        ]

        # Add metrics
        metrics_to_show = [
            ("Exact Match", "correctness", "exact_match"),
            ("F1 Score", "correctness", "f1_score"),
            ("ANLS", "correctness", "anls"),
            ("Latency (ms)", "latency", "total_ms"),
            ("Input Tokens", "tokens", "input_tokens"),
            ("Output Tokens", "tokens", "output_tokens"),
        ]

        for display_name, category, metric in metrics_to_show:
            values = []
            for s in strategies:
                if category == "latency":
                    val = (
                        comparison[s]
                        .get(category, {})
                        .get(metric, {})
                        .get("mean", 0)
                    )
                elif category == "tokens":
                    val = comparison[s].get(category, {}).get(metric, {}).get("mean", 0)
                else:
                    val = comparison[s].get(category, {}).get(metric, 0)

                formatted = f"{val:.3f}" if val < 10 else f"{val:.1f}"
                values.append(f"| {formatted:^{col_width-2}} ")

            lines.append(f"| {display_name:<18} " + "".join(values) + "|")

        lines.append("+" + "-" * 20 + ("+" + "-" * col_width) * len(strategies) + "+")

        return "\n".join(lines)
