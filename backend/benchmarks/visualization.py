"""
Visualization utilities for benchmark analysis.

Provides tools for visualizing:
- Predicted vs ground truth bounding boxes
- Patch similarity heatmaps
- Score distributions
- Per-category/type performance breakdowns
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional imports for visualization
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("PIL not available - visualization disabled")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available - plotting disabled")


def draw_bboxes_on_image(
    image: "Image.Image",
    pred_bboxes: List[List[int]],
    gt_bboxes: List[List[int]],
    pred_color: str = "red",
    gt_color: str = "green",
    line_width: int = 3,
    show_labels: bool = True,
) -> "Image.Image":
    """
    Draw predicted and ground truth bounding boxes on an image.

    Args:
        image: PIL Image
        pred_bboxes: List of predicted bboxes [x1, y1, x2, y2]
        gt_bboxes: List of ground truth bboxes
        pred_color: Color for predicted boxes
        gt_color: Color for ground truth boxes
        line_width: Width of bbox lines
        show_labels: Whether to show P/GT labels

    Returns:
        Image with bboxes drawn
    """
    if not HAS_PIL:
        raise ImportError("PIL required for visualization")

    # Create a copy to avoid modifying original
    result = image.copy()
    draw = ImageDraw.Draw(result)

    # Draw ground truth boxes first (underneath)
    for i, bbox in enumerate(gt_bboxes):
        draw.rectangle(bbox, outline=gt_color, width=line_width)
        if show_labels:
            draw.text((bbox[0], bbox[1] - 15), f"GT{i+1}", fill=gt_color)

    # Draw predicted boxes on top
    for i, bbox in enumerate(pred_bboxes):
        draw.rectangle(bbox, outline=pred_color, width=line_width)
        if show_labels:
            draw.text((bbox[0], bbox[1] - 15), f"P{i+1}", fill=pred_color)

    return result


def visualize_similarity_heatmap(
    image: "Image.Image",
    similarity_map: np.ndarray,
    alpha: float = 0.5,
    cmap: str = "hot",
) -> "Image.Image":
    """
    Overlay a similarity heatmap on an image.

    Args:
        image: PIL Image
        similarity_map: 2D array of similarity scores (e.g., 32x32)
        alpha: Transparency of the overlay
        cmap: Matplotlib colormap name

    Returns:
        Image with heatmap overlay
    """
    if not HAS_PIL or not HAS_MATPLOTLIB:
        raise ImportError("PIL and matplotlib required for heatmap visualization")

    # Normalize similarity map to [0, 1]
    sim_normalized = (similarity_map - similarity_map.min()) / (
        similarity_map.max() - similarity_map.min() + 1e-8
    )

    # Resize to image dimensions
    sim_resized = np.array(
        Image.fromarray((sim_normalized * 255).astype(np.uint8)).resize(
            image.size, Image.Resampling.BILINEAR
        )
    )

    # Apply colormap
    colormap = plt.get_cmap(cmap)
    heatmap = colormap(sim_resized / 255.0)
    heatmap = (heatmap[:, :, :3] * 255).astype(np.uint8)
    heatmap_img = Image.fromarray(heatmap)

    # Blend with original image
    result = Image.blend(image.convert("RGB"), heatmap_img, alpha)
    return result


def plot_score_distribution(
    scores: List[float],
    threshold: Optional[float] = None,
    title: str = "Region Score Distribution",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot histogram of region scores.

    Args:
        scores: List of region relevance scores
        threshold: Optional threshold line to draw
        title: Plot title
        save_path: Optional path to save figure
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for plotting")

    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=50, edgecolor="black", alpha=0.7)
    plt.xlabel("Relevance Score")
    plt.ylabel("Count")
    plt.title(title)

    if threshold is not None:
        plt.axvline(x=threshold, color="red", linestyle="--", label=f"Threshold: {threshold:.2f}")
        plt.legend()

    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved score distribution plot to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_performance_by_category(
    results: Dict[str, Dict[str, float]],
    metric: str = "f1",
    title: str = "Performance by Category",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot performance metrics by category.

    Args:
        results: Dict mapping category to metrics dict
        metric: Which metric to plot (f1, mean_iou, precision, recall)
        title: Plot title
        save_path: Optional path to save figure
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for plotting")

    categories = list(results.keys())
    values = [results[cat].get(metric, 0) for cat in categories]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(categories, values, color="steelblue", edgecolor="black")
    plt.xlabel("Category")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.xticks(rotation=45, ha="right")

    # Add value labels on bars
    for bar, val in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved category performance plot to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_strategy_comparison(
    strategy_results: Dict[str, Dict[str, float]],
    metrics: List[str] = ["mean_iou", "precision", "recall", "f1"],
    title: str = "Strategy Comparison",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot comparison of different filtering strategies.

    Args:
        strategy_results: Dict mapping strategy name to metrics dict
        metrics: List of metrics to compare
        title: Plot title
        save_path: Optional path to save figure
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for plotting")

    strategies = list(strategy_results.keys())
    x = np.arange(len(strategies))
    width = 0.8 / len(metrics)

    fig, ax = plt.subplots(figsize=(14, 7))

    for i, metric in enumerate(metrics):
        values = [strategy_results[s].get(metric, 0) for s in strategies]
        offset = (i - len(metrics) / 2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=metric.replace("_", " ").title())

    ax.set_xlabel("Strategy")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(strategies, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved strategy comparison plot to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_iou_histogram(
    ious: List[float],
    thresholds: List[float] = [0.5, 0.7],
    title: str = "IoU Distribution",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot histogram of IoU scores with threshold markers.

    Args:
        ious: List of IoU scores
        thresholds: Threshold values to mark
        title: Plot title
        save_path: Optional path to save figure
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for plotting")

    plt.figure(figsize=(10, 6))
    plt.hist(ious, bins=50, edgecolor="black", alpha=0.7, color="steelblue")

    colors = ["red", "orange", "purple"]
    for i, thresh in enumerate(thresholds):
        color = colors[i % len(colors)]
        plt.axvline(
            x=thresh,
            color=color,
            linestyle="--",
            linewidth=2,
            label=f"IoU@{thresh}: {sum(1 for x in ious if x >= thresh) / len(ious) * 100:.1f}%",
        )

    plt.xlabel("IoU Score")
    plt.ylabel("Count")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved IoU histogram to {save_path}")
    else:
        plt.show()

    plt.close()


def create_evaluation_report(
    results: Dict[str, Any],
    output_dir: str,
    include_visualizations: bool = True,
) -> None:
    """
    Create a comprehensive evaluation report with visualizations.

    Args:
        results: Benchmark results dictionary
        output_dir: Directory to save report files
        include_visualizations: Whether to generate plots
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate summary text report
    report_lines = [
        "=" * 60,
        "BBox-DocVQA Benchmark Evaluation Report",
        "=" * 60,
        "",
        "Overall Results:",
        "-" * 40,
    ]

    if "overall" in results:
        overall = results["overall"]
        report_lines.extend([
            f"  Mean IoU:    {overall.get('mean_iou', 0):.4f}",
            f"  IoU@0.5:     {overall.get('iou@0.5', 0):.4f}",
            f"  IoU@0.7:     {overall.get('iou@0.7', 0):.4f}",
            f"  Precision:   {overall.get('precision', 0):.4f}",
            f"  Recall:      {overall.get('recall', 0):.4f}",
            f"  F1 Score:    {overall.get('f1', 0):.4f}",
            "",
        ])

    # Results by instance type
    if "by_instance_type" in results:
        report_lines.extend([
            "Results by Instance Type:",
            "-" * 40,
        ])
        for inst_type, metrics in results["by_instance_type"].items():
            report_lines.append(
                f"  {inst_type}: F1={metrics.get('f1', 0):.4f}, "
                f"mIoU={metrics.get('mean_iou', 0):.4f}"
            )
        report_lines.append("")

    # Results by category
    if "by_category" in results:
        report_lines.extend([
            "Results by Category:",
            "-" * 40,
        ])
        for cat, metrics in results["by_category"].items():
            report_lines.append(
                f"  {cat}: F1={metrics.get('f1', 0):.4f}, "
                f"mIoU={metrics.get('mean_iou', 0):.4f}"
            )
        report_lines.append("")

    report_lines.extend([
        "=" * 60,
        f"Total Samples: {results.get('total_samples', 'N/A')}",
        f"Failed Samples: {results.get('failed_samples', 'N/A')}",
        "=" * 60,
    ])

    # Write text report
    report_path = output_path / "evaluation_report.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    logger.info(f"Saved text report to {report_path}")

    # Generate visualizations if requested
    if include_visualizations and HAS_MATPLOTLIB:
        # IoU distribution
        if "per_sample_ious" in results:
            plot_iou_histogram(
                results["per_sample_ious"],
                save_path=str(output_path / "iou_distribution.png"),
            )

        # Performance by category
        if "by_category" in results:
            plot_performance_by_category(
                results["by_category"],
                metric="f1",
                save_path=str(output_path / "performance_by_category.png"),
            )

    logger.info(f"Evaluation report saved to {output_path}")
