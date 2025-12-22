"""
Analyze ground-truth region characteristics vs achieved IoU.

This script analyzes what factors predict localization success:
1. Region size (area, width, height)
2. Aspect ratio
3. Category
4. Position on page
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


@dataclass
class RegionAnalysis:
    """Analysis results for a single sample."""

    sample_id: int
    doc_name: str
    category: str
    gt_width: float
    gt_height: float
    gt_area: float
    aspect_ratio: float  # width / height
    gt_center_x: float  # normalized 0-1
    gt_center_y: float  # normalized 0-1
    achieved_iou: float
    num_pred_regions: int
    pred_area: float  # total area of predicted regions
    area_ratio: float  # pred_area / gt_area
    tokens_selected: int
    tokens_all_ocr: int
    token_savings_pct: float  # savings vs all OCR


def analyze_sample(sample: dict) -> RegionAnalysis | None:
    """Analyze a single sample."""
    if sample.get("failed") or not sample.get("gt_bboxes"):
        return None

    # Use the first ground-truth bbox (most samples have one)
    gt_bbox = sample["gt_bboxes"][0]
    x1, y1, x2, y2 = gt_bbox

    w = x2 - x1
    h = y2 - y1

    if w <= 0 or h <= 0:
        return None

    # Compute characteristics (in original image coords - relative metrics still valid)
    area = w * h
    aspect_ratio = w / h if h > 0 else 1.0

    # Estimate page size from bbox (assume A4-ish proportions)
    # We normalize center position to 0-1 range assuming typical page dimensions
    page_width_est = 2480  # typical arXiv render width
    page_height_est = 3508  # typical arXiv render height
    center_x = ((x1 + x2) / 2) / page_width_est
    center_y = ((y1 + y2) / 2) / page_height_est

    achieved_iou = sample.get("mean_iou", 0.0)

    # Compute predicted region statistics
    pred_bboxes = sample.get("pred_bboxes", [])
    num_pred_regions = len(pred_bboxes)

    # Total area of all predicted regions
    pred_area = 0.0
    for bbox in pred_bboxes:
        px1, py1, px2, py2 = bbox
        pred_area += (px2 - px1) * (py2 - py1)

    area_ratio = pred_area / area if area > 0 else 0.0

    # Token statistics
    tokens_selected = sample.get("tokens_selected", 0)
    tokens_all_ocr = sample.get("tokens_all_ocr", 0)
    token_savings_pct = (
        (1 - tokens_selected / tokens_all_ocr) * 100 if tokens_all_ocr > 0 else 0.0
    )

    return RegionAnalysis(
        sample_id=sample["sample_id"],
        doc_name=sample.get("doc_name", "unknown"),
        category=sample.get("category", "unknown"),
        gt_width=w,
        gt_height=h,
        gt_area=area,
        aspect_ratio=aspect_ratio,
        gt_center_x=center_x,
        gt_center_y=center_y,
        achieved_iou=achieved_iou,
        num_pred_regions=num_pred_regions,
        pred_area=pred_area,
        area_ratio=area_ratio,
        tokens_selected=tokens_selected,
        tokens_all_ocr=tokens_all_ocr,
        token_savings_pct=token_savings_pct,
    )


def main():
    # Find the most recent complete benchmark run
    runs_dir = Path(__file__).parent.parent.parent / "backend" / "benchmarks" / "runs"

    # Use ColQwen3-4B complete run
    summary_path = runs_dir / "6. colqwen3-4b complete" / "summary.json"

    if not summary_path.exists():
        print(f"Summary file not found: {summary_path}")
        sys.exit(1)

    print(f"Loading {summary_path}...")
    with open(summary_path) as f:
        data = json.load(f)

    samples = data.get("sample_results", [])
    print(f"Analyzing {len(samples)} samples...")

    # Analyze all samples
    results: list[RegionAnalysis] = []
    for sample in samples:
        analysis = analyze_sample(sample)
        if analysis:
            results.append(analysis)

    print(f"Successfully analyzed {len(results)} samples")

    # Aggregate by category
    categories = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    # Print summary
    print("\n" + "=" * 80)
    print("REGION CHARACTERISTICS VS LOCALIZATION ACCURACY")
    print("=" * 80)

    # Extract arrays for correlation analysis
    areas = np.array([r.gt_area for r in results])
    widths = np.array([r.gt_width for r in results])
    heights = np.array([r.gt_height for r in results])
    aspect_ratios = np.array([r.aspect_ratio for r in results])
    center_xs = np.array([r.gt_center_x for r in results])
    center_ys = np.array([r.gt_center_y for r in results])
    ious = np.array([r.achieved_iou for r in results])

    # New metrics
    num_pred_regions = np.array([r.num_pred_regions for r in results])
    pred_areas = np.array([r.pred_area for r in results])
    area_ratios = np.array([r.area_ratio for r in results])
    token_savings = np.array([r.token_savings_pct for r in results])
    tokens_selected = np.array([r.tokens_selected for r in results])

    # Log-transform area for better correlation (area spans orders of magnitude)
    log_areas = np.log10(areas + 1)
    log_pred_areas = np.log10(pred_areas + 1)

    print("\n## Correlation Analysis (Pearson r, p-value)\n")

    print("### Ground-Truth Region Characteristics")
    correlations = {}
    for name, values in [
        ("Area", areas),
        ("Log10(Area)", log_areas),
        ("Width", widths),
        ("Height", heights),
        ("Aspect Ratio", aspect_ratios),
        ("Center X", center_xs),
        ("Center Y", center_ys),
    ]:
        r, p = stats.pearsonr(values, ious)
        correlations[name] = {"r": r, "p": p}
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"{name:<20}: r = {r:+.3f}, p = {p:.2e} {sig}")

    print("\n### Prediction Characteristics")
    for name, values in [
        ("Num Pred Regions", num_pred_regions),
        ("Pred Area", pred_areas),
        ("Log10(Pred Area)", log_pred_areas),
        ("Area Ratio", area_ratios),
        ("Tokens Selected", tokens_selected),
        ("Token Savings %", token_savings),
    ]:
        r, p = stats.pearsonr(values, ious)
        correlations[name] = {"r": r, "p": p}
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"{name:<20}: r = {r:+.3f}, p = {p:.2e} {sig}")

    print("\n## By Category\n")
    print(
        f"{'Category':<10} {'N':>5} {'Mean IoU':>9} {'Mean Area':>12} {'Mean W':>8} {'Mean H':>8} {'Aspect':>8}"
    )
    print("-" * 70)

    for cat in sorted(
        categories.keys(),
        key=lambda c: -np.mean([r.achieved_iou for r in categories[c]]),
    ):
        cat_results = categories[cat]
        n = len(cat_results)
        iou_mean = np.mean([r.achieved_iou for r in cat_results])
        area_mean = np.mean([r.gt_area for r in cat_results])
        w_mean = np.mean([r.gt_width for r in cat_results])
        h_mean = np.mean([r.gt_height for r in cat_results])
        ar_mean = np.mean([r.aspect_ratio for r in cat_results])

        print(
            f"{cat:<10} {n:>5} {iou_mean:>9.3f} {area_mean:>12.0f} {w_mean:>8.0f} {h_mean:>8.0f} {ar_mean:>8.2f}"
        )

    # Size quartile analysis
    print("\n## Performance by Region Size Quartile\n")

    quartiles = np.percentile(areas, [25, 50, 75])
    q_labels = [
        f"Q1 (< {quartiles[0]:.0f})",
        f"Q2 ({quartiles[0]:.0f}-{quartiles[1]:.0f})",
        f"Q3 ({quartiles[1]:.0f}-{quartiles[2]:.0f})",
        f"Q4 (> {quartiles[2]:.0f})",
    ]

    for i, (label, subset) in enumerate(
        [
            (q_labels[0], [r for r in results if r.gt_area < quartiles[0]]),
            (
                q_labels[1],
                [r for r in results if quartiles[0] <= r.gt_area < quartiles[1]],
            ),
            (
                q_labels[2],
                [r for r in results if quartiles[1] <= r.gt_area < quartiles[2]],
            ),
            (q_labels[3], [r for r in results if r.gt_area >= quartiles[2]]),
        ]
    ):
        if subset:
            iou_mean = np.mean([r.achieved_iou for r in subset])
            iou_std = np.std([r.achieved_iou for r in subset])
            print(
                f"{label:<25}: N={len(subset):>4}, Mean IoU = {iou_mean:.3f} +/- {iou_std:.3f}"
            )

    # Within-document consistency analysis
    print("\n## Within-Document Consistency\n")

    # Group by document
    docs = {}
    for r in results:
        if r.doc_name not in docs:
            docs[r.doc_name] = []
        docs[r.doc_name].append(r)

    # Only analyze docs with multiple samples
    multi_sample_docs = {k: v for k, v in docs.items() if len(v) >= 2}
    print(f"Documents with 2+ samples: {len(multi_sample_docs)}")

    # Compute within-doc IoU variance
    within_doc_stds = []
    within_doc_ranges = []
    doc_stats = []

    for doc_name, doc_results in multi_sample_docs.items():
        doc_ious = [r.achieved_iou for r in doc_results]
        doc_std = np.std(doc_ious)
        doc_range = max(doc_ious) - min(doc_ious)
        doc_mean = np.mean(doc_ious)
        doc_cat = doc_results[0].category

        within_doc_stds.append(doc_std)
        within_doc_ranges.append(doc_range)
        doc_stats.append(
            {
                "doc": doc_name,
                "n": len(doc_results),
                "mean": doc_mean,
                "std": doc_std,
                "range": doc_range,
                "cat": doc_cat,
            }
        )

    if within_doc_stds:
        print(f"Mean within-doc IoU std:   {np.mean(within_doc_stds):.3f}")
        print(f"Mean within-doc IoU range: {np.mean(within_doc_ranges):.3f}")
        print(f"Overall IoU std:           {np.std(ious):.3f}")

        # Ratio: high ratio means most variance is within documents, not between
        overall_var = np.var(ious)
        within_var = np.mean([s**2 for s in within_doc_stds])
        between_var = overall_var - within_var if overall_var > within_var else 0
        print(f"\nVariance decomposition:")
        print(f"  Overall variance:  {overall_var:.4f}")
        print(
            f"  Within-doc variance: {within_var:.4f} ({100*within_var/overall_var:.1f}%)"
        )
        print(
            f"  Between-doc variance: {between_var:.4f} ({100*between_var/overall_var:.1f}%)"
        )

        # Show most consistent and inconsistent docs
        doc_stats_sorted = sorted(doc_stats, key=lambda x: x["std"])
        print("\n### Most Consistent Documents (lowest IoU variance)")
        for d in doc_stats_sorted[:5]:
            print(
                f"  {d['doc']:<15} ({d['cat']:<8}): n={d['n']:>2}, mean={d['mean']:.3f}, std={d['std']:.3f}"
            )

        print("\n### Most Inconsistent Documents (highest IoU variance)")
        for d in doc_stats_sorted[-5:]:
            print(
                f"  {d['doc']:<15} ({d['cat']:<8}): n={d['n']:>2}, mean={d['mean']:.3f}, std={d['std']:.3f}"
            )

    # Generate plots (only those used in paper.tex)
    output_dir = Path(__file__).parent.parent / "figures"
    output_dir.mkdir(exist_ok=True)

    cat_colors = {
        "cs": "C0",
        "econ": "C1",
        "eess": "C2",
        "math": "C3",
        "physics": "C4",
        "q-bio": "C5",
        "q-fin": "C6",
        "stat": "C7",
    }

    # Box plot by category (used in paper as Figure: iou_by_category_box.png)
    fig, ax = plt.subplots(figsize=(10, 5))

    cat_order = sorted(
        categories.keys(),
        key=lambda c: -np.mean([r.achieved_iou for r in categories[c]]),
    )
    positions = range(len(cat_order))

    ious_by_cat = [[r.achieved_iou for r in categories[cat]] for cat in cat_order]
    bp = ax.boxplot(ious_by_cat, positions=positions, widths=0.6, patch_artist=True)

    # Color boxes
    for patch, cat in zip(bp["boxes"], cat_order):
        patch.set_facecolor(cat_colors.get(cat, "gray"))
        patch.set_alpha(0.6)

    ax.set_xticks(positions)
    ax.set_xticklabels(cat_order)
    ax.set_xlabel("Category")
    ax.set_ylabel("Achieved IoU")
    ax.set_title("Localization Accuracy by Document Category")
    ax.set_ylim(0, 1)

    plt.tight_layout()
    box_path = output_dir / "iou_by_category_box.png"
    plt.savefig(box_path, dpi=150)
    print(f"\nSaved box plot to {box_path}")

    # Save raw data
    output_data = {
        "correlations": {
            k: {"r": float(v["r"]), "p": float(v["p"])} for k, v in correlations.items()
        },
        "by_category": {
            cat: {
                "n": len(cat_results),
                "mean_iou": float(np.mean([r.achieved_iou for r in cat_results])),
                "std_iou": float(np.std([r.achieved_iou for r in cat_results])),
                "mean_area": float(np.mean([r.gt_area for r in cat_results])),
                "mean_width": float(np.mean([r.gt_width for r in cat_results])),
                "mean_height": float(np.mean([r.gt_height for r in cat_results])),
                "mean_aspect_ratio": float(
                    np.mean([r.aspect_ratio for r in cat_results])
                ),
                "mean_num_pred_regions": float(
                    np.mean([r.num_pred_regions for r in cat_results])
                ),
                "mean_token_savings_pct": float(
                    np.mean([r.token_savings_pct for r in cat_results])
                ),
                "mean_area_ratio": float(np.mean([r.area_ratio for r in cat_results])),
            }
            for cat, cat_results in categories.items()
        },
        "quartiles": {
            "area_25": float(quartiles[0]),
            "area_50": float(quartiles[1]),
            "area_75": float(quartiles[2]),
        },
        "within_document": {
            "num_multi_sample_docs": len(multi_sample_docs),
            "mean_within_doc_std": (
                float(np.mean(within_doc_stds)) if within_doc_stds else None
            ),
            "mean_within_doc_range": (
                float(np.mean(within_doc_ranges)) if within_doc_ranges else None
            ),
            "overall_std": float(np.std(ious)),
            "variance_decomposition": (
                {
                    "overall": float(overall_var) if within_doc_stds else None,
                    "within_doc": float(within_var) if within_doc_stds else None,
                    "between_doc": float(between_var) if within_doc_stds else None,
                }
                if within_doc_stds
                else None
            ),
        },
    }

    data_path = output_dir / "region_analysis_data.json"
    with open(data_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved analysis data to {data_path}")

    plt.close("all")
    print("\nDone!")


if __name__ == "__main__":
    main()
