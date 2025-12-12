"""
Generate charts for the paper from benchmark results.

Usage:
    python scripts/generate_paper_charts.py <path_to_summary.json>

Example:
    python scripts/generate_paper_charts.py backend/benchmarks/runs/bbox_docvqa_benchmark_20251211_163412/summary.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Use a clean style suitable for papers
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

# Color palette - colorblind friendly
COLORS = {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "tertiary": "#F18F01",
    "success": "#3A7D44",
    "neutral": "#6C757D",
}

CATEGORY_COLORS = {
    "cs": "#2E86AB",
    "econ": "#A23B72",
    "eess": "#F18F01",
    "math": "#C73E1D",
    "physics": "#3A7D44",
    "q-bio": "#6C757D",
    "q-fin": "#9B5DE5",
    "stat": "#00BBF9",
}


def load_data(json_path: str) -> dict:
    """Load benchmark results from JSON file."""
    with open(json_path) as f:
        return json.load(f)


def compute_category_stats(data: dict) -> dict:
    """Compute per-category statistics from sample results."""
    category_samples = defaultdict(list)

    for sample in data["sample_results"]:
        if not sample.get("failed", False):
            category_samples[sample["category"]].append(sample)

    stats = {}
    for category, samples in category_samples.items():
        ious = [s["mean_iou"] for s in samples]
        stats[category] = {
            "n": len(samples),
            "mean_iou": np.mean(ious),
            "std_iou": np.std(ious),
        }

    return stats


def plot_category_performance(stats: dict, output_dir: Path):
    """Bar chart of Mean IoU by category."""
    categories = sorted(stats.keys())
    mean_ious = [stats[c]["mean_iou"] for c in categories]
    std_ious = [stats[c]["std_iou"] for c in categories]
    colors = [CATEGORY_COLORS.get(c, COLORS["neutral"]) for c in categories]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(categories, mean_ious, yerr=std_ious, capsize=3, color=colors, edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Mean IoU")
    ax.set_xlabel("Category")
    ax.set_title("Localization Performance by Document Category")
    ax.set_ylim(0, 1)

    # Add value labels on bars
    for bar, val in zip(bars, mean_ious):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{val:.2f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_dir / "category_performance.png")
    plt.close()
    print("Saved: category_performance.png")


def plot_token_savings(data: dict, output_dir: Path):
    """Bar chart showing token savings."""
    token_summary = data["token_summary"]

    labels = ["Selected\n(Ours)", "Full OCR", "Full Image"]
    values = [
        token_summary["total_tokens_selected"],
        token_summary["total_tokens_all_ocr"],
        token_summary["total_tokens_full_image"],
    ]
    # Convert to millions for readability
    values_m = [v / 1e6 for v in values]

    colors = [COLORS["success"], COLORS["secondary"], COLORS["neutral"]]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values_m, color=colors, edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Total Tokens (millions)")
    ax.set_title("Token Usage Comparison")

    # Add value labels
    for bar, val in zip(bars, values_m):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{val:.2f}M", ha="center", va="bottom", fontsize=9)

    # Add savings annotations
    savings_ocr = token_summary["savings_vs_all_ocr"]
    savings_img = token_summary["savings_vs_full_image"]
    ax.annotate(
        f"−{savings_ocr}",
        xy=(1, values_m[1]),
        xytext=(0.5, values_m[1] * 0.7),
        fontsize=10,
        color=COLORS["success"],
        fontweight="bold",
        ha="center",
    )
    ax.annotate(
        f"−{savings_img}",
        xy=(2, values_m[2]),
        xytext=(1.5, values_m[2] * 0.6),
        fontsize=10,
        color=COLORS["success"],
        fontweight="bold",
        ha="center",
    )

    plt.tight_layout()
    plt.savefig(output_dir / "token_savings.png")
    plt.close()
    print("Saved: token_savings.png")


def main():
    parser = argparse.ArgumentParser(description="Generate paper charts from benchmark results")
    parser.add_argument("summary_json", type=str, help="Path to summary.json file")
    parser.add_argument("--output-dir", type=str, default="paper/figures", help="Output directory for charts")
    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.summary_json}")
    data = load_data(args.summary_json)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Compute statistics
    print("Computing category statistics...")
    stats = compute_category_stats(data)

    # Generate charts
    print("\nGenerating charts...")
    plot_category_performance(stats, output_dir)
    plot_token_savings(data, output_dir)

    print(f"\nDone! Generated 2 charts in {output_dir}")

    # Print summary stats
    print("\n--- Summary Statistics ---")
    print(f"Total samples: {data['summary']['num_samples']}")
    print(f"Mean IoU: {data['summary']['mean_iou']:.3f}")
    print(f"IoU@0.5 Hit Rate: {data['summary']['iou_at_0_5']*100:.1f}%")
    print(f"Token savings vs OCR: {data['token_summary']['savings_vs_all_ocr']}")
    print(f"Token savings vs Image: {data['token_summary']['savings_vs_full_image']}")


if __name__ == "__main__":
    main()
