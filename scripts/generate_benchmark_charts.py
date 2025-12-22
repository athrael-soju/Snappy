"""
Generate comparative benchmark charts for the paper.
Extensible for adding new models (e.g., ColQwen3-8B).
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Configuration
BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks"
FIGURES_DIR = Path(__file__).parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Model configurations - ordered by size (ascending)
MODELS = {
    "colmodernvbert-0.5b": {
        "label": "ColModernVBERT",
        "color": "#3498db",
        "marker": "s",
    },
    "colqwen3-4b": {
        "label": "ColQwen3-4B",
        "color": "#2ecc71",
        "marker": "o",
    },
    "colqwen3-8b": {
        "label": "ColQwen3-8B",
        "color": "#9b59b6",
        "marker": "^",
    },
}

# Category display order (by ColQwen3-4B performance)
CATEGORY_ORDER = ["cs", "eess", "q-bio", "physics", "stat", "q-fin", "econ", "math"]
CATEGORY_LABELS = {
    "cs": "CS",
    "eess": "EE",
    "q-bio": "Q-Bio",
    "physics": "Physics",
    "stat": "Stat",
    "q-fin": "Q-Fin",
    "econ": "Econ",
    "math": "Math",
}


def parse_progress_file(model_dir: Path) -> dict:
    """Parse the progress.md file to extract benchmark results."""
    progress_file = model_dir / "progress.md"
    if not progress_file.exists():
        return None

    content = progress_file.read_text(encoding="utf-8")

    # Extract summary metrics
    results = {
        "mean_iou": None,
        "iou_25": None,
        "iou_50": None,
        "iou_70": None,
        "selected_tokens": None,
        "all_ocr_tokens": None,
        "full_image_tokens": None,
        "categories": {},
    }

    # Parse summary section
    for line in content.split("\n"):
        if "**Mean IoU:**" in line:
            results["mean_iou"] = float(line.split(":**")[1].strip())
        elif "**IoU@0.25:**" in line:
            parts = line.split("(")[1].split(")")[0]
            results["iou_25"] = float(parts.replace("%", ""))
        elif "**IoU@0.5:**" in line:
            parts = line.split("(")[1].split(")")[0]
            results["iou_50"] = float(parts.replace("%", ""))
        elif "**IoU@0.7:**" in line:
            parts = line.split("(")[1].split(")")[0]
            results["iou_70"] = float(parts.replace("%", ""))
        elif "**Token Totals:**" in line:
            parts = line.split("|")
            results["selected_tokens"] = int(
                parts[0].split("Selected")[1].strip().replace(",", "")
            )
            results["all_ocr_tokens"] = int(
                parts[1].split("All OCR")[1].strip().replace(",", "")
            )
            results["full_image_tokens"] = int(
                parts[2].split("Full Image")[1].strip().replace(",", "")
            )

    # Parse per-category results from table rows
    from collections import defaultdict

    categories = defaultdict(
        lambda: {
            "n": 0,
            "iou_sum": 0,
            "hit25": 0,
            "hit50": 0,
            "hit70": 0,
            "iou_values": [],
        }
    )

    for line in content.split("\n"):
        if (
            line.startswith("|")
            and not line.startswith("| #")
            and not line.startswith("| **")
        ):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 7 and parts[3] in CATEGORY_ORDER:
                cat = parts[3]
                try:
                    iou = float(parts[6])
                    categories[cat]["n"] += 1
                    categories[cat]["iou_sum"] += iou
                    categories[cat]["iou_values"].append(iou)
                    if iou >= 0.25:
                        categories[cat]["hit25"] += 1
                    if iou >= 0.5:
                        categories[cat]["hit50"] += 1
                    if iou >= 0.7:
                        categories[cat]["hit70"] += 1
                except (ValueError, IndexError):
                    pass

    for cat, data in categories.items():
        if data["n"] > 0:
            results["categories"][cat] = {
                "n": data["n"],
                "mean_iou": data["iou_sum"] / data["n"],
                "iou_25": 100 * data["hit25"] / data["n"],
                "iou_50": 100 * data["hit50"] / data["n"],
                "iou_70": 100 * data["hit70"] / data["n"],
                "iou_values": data["iou_values"],
            }

    return results


def load_all_models() -> dict:
    """Load benchmark results for all configured models."""
    all_results = {}
    for model_id, config in MODELS.items():
        model_dir = BENCHMARKS_DIR / model_id
        if model_dir.exists():
            results = parse_progress_file(model_dir)
            if results:
                all_results[model_id] = {**config, **results}
                print(f"Loaded {model_id}: Mean IoU = {results['mean_iou']:.3f}")
    return all_results


def plot_category_comparison(
    results: dict,
    metric: str = "mean_iou",
    output_name: str = "category_comparison.png",
):
    """Generate grouped bar chart comparing models across categories."""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(CATEGORY_ORDER))
    width = 0.8 / len(results)
    offsets = np.linspace(-0.4 + width / 2, 0.4 - width / 2, len(results))

    metric_labels = {
        "mean_iou": "Mean IoU",
        "iou_25": "Hit Rate @ IoU 0.25 (%)",
        "iou_50": "Hit Rate @ IoU 0.5 (%)",
        "iou_70": "Hit Rate @ IoU 0.7 (%)",
    }

    for i, (model_id, data) in enumerate(results.items()):
        values = [
            data["categories"].get(cat, {}).get(metric, 0) for cat in CATEGORY_ORDER
        ]
        bars = ax.bar(
            x + offsets[i],
            values,
            width,
            label=data["label"],
            color=data["color"],
            edgecolor="white",
        )

    ax.set_xlabel("Document Category", fontsize=12)
    ax.set_ylabel(metric_labels.get(metric, metric), fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([CATEGORY_LABELS[c] for c in CATEGORY_ORDER])
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    if metric == "mean_iou":
        ax.set_ylim(0, 0.8)
    else:
        ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def plot_accuracy_efficiency_tradeoff(
    results: dict, output_name: str = "accuracy_efficiency_tradeoff.png"
):
    """Scatter plot showing accuracy vs token efficiency tradeoff."""
    fig, ax = plt.subplots(figsize=(8, 6))

    for model_id, data in results.items():
        token_savings = 100 * (1 - data["selected_tokens"] / data["full_image_tokens"])
        ax.scatter(
            token_savings,
            data["iou_50"],
            s=200,
            c=data["color"],
            marker=data["marker"],
            label=data["label"],
            edgecolors="white",
            linewidths=2,
        )
        # Add label next to point
        ax.annotate(
            data["label"],
            (token_savings, data["iou_50"]),
            xytext=(10, 5),
            textcoords="offset points",
            fontsize=10,
        )

    ax.set_xlabel("Token Savings vs Full Image (%)", fontsize=12)
    ax.set_ylabel("Hit Rate @ IoU 0.5 (%)", fontsize=12)
    ax.set_xlim(45, 65)
    ax.set_ylim(40, 70)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def plot_iou_thresholds_comparison(
    results: dict, output_name: str = "iou_thresholds_comparison.png"
):
    """Bar chart comparing hit rates across IoU thresholds."""
    fig, ax = plt.subplots(figsize=(10, 6))

    thresholds = ["IoU@0.25", "IoU@0.5", "IoU@0.7"]
    x = np.arange(len(thresholds))
    width = 0.8 / len(results)
    offsets = np.linspace(-0.4 + width / 2, 0.4 - width / 2, len(results))

    for i, (model_id, data) in enumerate(results.items()):
        values = [data["iou_25"], data["iou_50"], data["iou_70"]]
        bars = ax.bar(
            x + offsets[i],
            values,
            width,
            label=data["label"],
            color=data["color"],
            edgecolor="white",
        )
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_xlabel("IoU Threshold", fontsize=12)
    ax.set_ylabel("Hit Rate (%)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(thresholds)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def plot_token_comparison(results: dict, output_name: str = "token_comparison.png"):
    """Stacked bar chart showing token usage."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Add baselines
    ["Full Image", "All OCR"] + list(results.keys())
    first_model = list(results.values())[0]

    values = [
        first_model["full_image_tokens"] / 1e6,
        first_model["all_ocr_tokens"] / 1e6,
    ]
    colors = ["#e74c3c", "#f39c12"]
    labels = ["Full Image", "All OCR"]

    for model_id, data in results.items():
        values.append(data["selected_tokens"] / 1e6)
        colors.append(data["color"])
        labels.append(data["label"])

    x = np.arange(len(values))
    bars = ax.bar(x, values, color=colors, edgecolor="white")

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{val:.2f}M",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_ylabel("Total Tokens (Millions)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def plot_iou_by_category_box(
    results: dict, output_name: str = "iou_by_category_box.png"
):
    """Box plot showing IoU distribution by category for each model."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Sort categories by mean IoU of ColQwen3-4B (descending) to match Table 4
    sort_model = results.get("colqwen3-4b", list(results.values())[0])
    sorted_cats = sorted(
        CATEGORY_ORDER,
        key=lambda c: sort_model["categories"].get(c, {}).get("mean_iou", 0),
        reverse=True,
    )

    n_models = len(results)
    n_cats = len(sorted_cats)
    positions = []
    colors_list = []
    data = []
    labels = []

    # Build data for box plots
    width = 0.25
    for i, cat in enumerate(sorted_cats):
        for j, (model_id, model_data) in enumerate(results.items()):
            cat_data = model_data["categories"].get(cat, {})
            iou_values = cat_data.get("iou_values", [])
            if iou_values:
                pos = i * (n_models + 1) * width + j * width
                positions.append(pos)
                data.append(iou_values)
                colors_list.append(model_data["color"])
                labels.append(model_data["label"])

    # Create box plots
    bp = ax.boxplot(
        data,
        positions=positions,
        widths=width * 0.8,
        patch_artist=True,
        showfliers=True,
        flierprops=dict(marker="o", markersize=3, alpha=0.5),
    )

    # Color the boxes
    for patch, color in zip(bp["boxes"], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Set x-axis
    tick_positions = [
        i * (n_models + 1) * width + (n_models - 1) * width / 2 for i in range(n_cats)
    ]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([CATEGORY_LABELS[c] for c in sorted_cats])

    # Legend
    legend_handles = [
        mpatches.Rectangle((0, 0), 1, 1, facecolor=model_data["color"], alpha=0.7)
        for model_data in results.values()
    ]
    legend_labels = [data["label"] for data in results.values()]
    ax.legend(legend_handles, legend_labels, loc="upper right")

    ax.set_xlabel("Document Category", fontsize=12)
    ax.set_ylabel("IoU", fontsize=12)
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def plot_radar_comparison(results: dict, output_name: str = "radar_comparison.png"):
    """Radar/spider chart comparing models across multiple dimensions."""
    categories = ["Mean IoU", "IoU@0.25", "IoU@0.5", "IoU@0.7", "Token Savings"]
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for model_id, data in results.items():
        token_savings = 100 * (1 - data["selected_tokens"] / data["full_image_tokens"])
        values = [
            data["mean_iou"] * 100,  # Scale to percentage for consistency
            data["iou_25"],
            data["iou_50"],
            data["iou_70"],
            token_savings,
        ]
        values += values[:1]

        ax.plot(
            angles, values, "o-", linewidth=2, label=data["label"], color=data["color"]
        )
        ax.fill(angles, values, alpha=0.25, color=data["color"])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_name}")


def main():
    print("Loading benchmark results...")
    results = load_all_models()

    if len(results) < 2:
        print("Warning: Need at least 2 models for comparison charts")
        return

    print(f"\nGenerating charts for {len(results)} models...")

    # Generate all charts
    plot_iou_thresholds_comparison(results, "iou_thresholds_comparison.png")
    plot_token_comparison(results, "token_comparison.png")
    plot_radar_comparison(results, "radar_comparison.png")
    plot_iou_by_category_box(results, "iou_by_category_box.png")

    print("\nDone! Charts saved to:", FIGURES_DIR)


if __name__ == "__main__":
    main()
