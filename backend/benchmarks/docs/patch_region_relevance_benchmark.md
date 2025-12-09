# Patch-to-Region Relevance Propagation Benchmark

## Overview

This document summarizes the benchmark testing effort for the patch-to-region relevance propagation feature in Snappy. The goal is to use ColPali's interpretability maps to intelligently select relevant OCR regions, reducing token usage while maintaining answer coverage.

## Problem Statement

When processing document images, Snappy extracts OCR regions and sends them to Claude for question answering. Sending all regions is expensive (high token count). The hypothesis is that ColPali's patch-level attention maps can identify which regions are relevant to a query, allowing selective region filtering.

## Benchmark Dataset

**BBox_DocVQA** - A curated subset from DocVQA with bounding box annotations:
- Contains Image, Text, and Table region types
- Each sample has a question, ground truth answer, and answer bounding box
- Allows measuring whether selected regions overlap with ground truth

## Key Metrics

| Metric | Description |
|--------|-------------|
| **IoU@0.25** | Hit rate - does any selected region overlap GT with IoU >= 0.25? |
| **GT Coverage** | What percentage of GT bbox area is covered by selected regions? |
| **Selection Rate** | Percentage of OCR regions kept (lower = more selective) |
| **Token Savings** | Reduction vs full image baseline or all-OCR-regions baseline |

## Configuration Parameters

### Aggregation Methods

How to convert patch-level similarity scores to region-level scores:

| Method | Formula | Description |
|--------|---------|-------------|
| `max` | max(patch_scores) | Highest-scoring patch in region |
| `mean` | mean(patch_scores) | Average of all patches in region |
| `sum` | sum(patch_scores) | Sum of all patches (favors larger regions) |
| `iou_weighted` | Σ(IoU × score) | **Recommended** - Weighted sum by patch-region overlap |
| `iou_weighted_norm` | Σ(IoU × score) / Σ(IoU) | Normalized variant (removes size bias) |

### Selection Methods

How to filter regions based on their scores:

| Method | Description |
|--------|-------------|
| `top_k` | Select top K regions by score |
| `threshold` | Select regions above absolute score threshold |
| `relative` | Select regions above `threshold × max_score` |
| `otsu` | Automatic thresholding using Otsu's method |
| `elbow` | Find elbow point in sorted scores |

### Region Merging

Combines nearby high-scoring regions into larger regions:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--merge-regions` | false | Enable region merging |
| `--merge-max-area` | 0.25 | Maximum merged region area (fraction of image) |
| `--merge-method` | proximity | Merging strategy (proximity, overlap, hybrid) |
| `--no-merge-for-text` | - | Disable merging for Text regions |
| `--no-merge-for-table` | - | Disable merging for Table regions |

## Bugs Fixed During Testing

### 1. Coordinate Normalization Bug (Critical)

**File:** `backend/benchmarks/utils/coordinates.py`

**Problem:** DeepSeek OCR returns bounding boxes in 0-999 coordinate space. The normalization function incorrectly required `image_width is None` to detect this format, causing bboxes to be divided by pixel dimensions instead of 999.

**Before (buggy):**
```python
elif max_coord <= 999 and image_width is None:
    return (x1 / 999.0, y1 / 999.0, x2 / 999.0, y2 / 999.0)
```

**After (fixed):**
```python
elif max_coord <= 999:
    # DeepSeek-OCR format (0-999) - always use 999 divisor regardless of image dims
    return (x1 / 999.0, y1 / 999.0, x2 / 999.0, y2 / 999.0)
```

**Impact:** Regions were mapping to completely wrong locations on the heatmap.

### 2. Visualization Parameters

**File:** `backend/benchmarks/visualization.py`

**Problems:**
- Alpha too low (60 vs frontend's 180) - heatmaps nearly invisible
- Normalization strategy wrong (PERCENTILE vs MINMAX)

**Fixes:**
- Changed `alpha=60` to `alpha=180`
- Changed normalization from `PERCENTILE` to `MINMAX`

### 3. Token Counting for Merged Regions

**Files:** `backend/benchmarks/run_bbox_docvqa.py`, `backend/benchmarks/merging.py`

**Problem:** Initially, merged regions were counted as text tokens. Then fixed to use vision tokens, but used the UNION bbox which is much larger than the sum of individual regions.

**Fix (v1):** Changed token counting to use vision tokens for `label in ("image", "merged")`.

**Fix (v2):** Store source region info in `raw_region`:
```python
raw_region={
    "merged_from": [r.region_id for r in self.source_regions],
    "source_bboxes": [r.bbox for r in self.source_regions],
    "source_labels": [r.label for r in self.source_regions],
    "source_contents": [r.content for r in self.source_regions],
}
```

Token counting now iterates over source regions individually:
- Image sources → vision tokens based on bbox
- Text/table sources → text tokens based on content

This provides accurate token counts reflecting what Snappy actually sends (individual crops, not one union crop).

### 4. Missing CLI Arguments

**File:** `backend/benchmarks/run_bbox_docvqa.py`

Added missing CLI arguments:
- `--threshold` - Absolute score threshold for `threshold` selection method
- `--relative-threshold` - Fraction of max score for `relative` selection method

## Critical Finding: Image Crop Token Overhead

### The Problem

**Multiple image crops can cost MORE tokens than the full image!**

Each image sent to Claude has:
- **Base cost:** 85 tokens per image
- **Tile cost:** 170 tokens per 512×512 tile (with ceiling rounding)

Example calculation:
```
Full image (1500×1500):
  - Scaled to fit 1568×1568 → 1500×1500
  - Tiles: ceil(1500/512) × ceil(1500/512) = 3 × 3 = 9 tiles
  - Tokens: 9 × 170 + 85 = 1615 tokens

5 merged regions (each ~600×600):
  - Each: ceil(600/512) × ceil(600/512) = 2 × 2 = 4 tiles
  - Each: 4 × 170 + 85 = 765 tokens
  - Total: 5 × 765 = 3825 tokens (2.4× MORE than full image!)
```

### Solution

The benchmark now caps selected tokens at the full image cost:
```python
tokens_selected = min(tokens_selected_raw, tokens_full_image)
```

This reflects real-world behavior: if cropping costs more, just send the full image.

### Implications

For **Image-type documents**, region selection may not save tokens. The value instead is:
1. **Focusing attention** - Highlighting relevant regions even in full image
2. **Hybrid approach** - Send full image + text annotations for relevant regions
3. **Text extraction** - If OCR provides good image descriptions, send text instead

For **Text/Table documents**, token savings are still significant because we're filtering text content, not image crops.

## Experimental Results

### Best Configuration Results (20 samples)

**Command:**
```bash
python -m benchmarks.run_bbox_docvqa \
    --aggregation-methods iou_weighted \
    --selection-methods relative \
    --relative-threshold 0.7 \
    --merge-regions \
    --merge-max-area 0.25 \
    --no-merge-for-text \
    --no-merge-for-table
```

**Results:**

| Metric | Value |
|--------|-------|
| IoU@0.25 Hit Rate | **95%** (19/20) |
| GT Coverage | 78.7% |
| Selection Rate | 29% |

### Performance by Region Type

| Region Type | Merging | Selectivity | Notes |
|-------------|---------|-------------|-------|
| **Image** | Enabled | 42→4-6 regions | Token savings capped at full image |
| **Table** | Disabled | 10→7-10 regions | Moderate text token savings |
| **Text** | Disabled | 7-17→6-14 regions | Minimal filtering (uniform attention) |

### Baseline Comparison

| Method | IoU@0.25 | GT Coverage | Notes |
|--------|----------|-------------|-------|
| **Patch-based (ours)** | **95%** | **78.7%** | 29% selection rate |
| BM25 | 90% | 74.8% | 100% selection rate |
| Cosine | 90% | 74.8% | 100% selection rate |
| Random | 35% | 27.2% | Random selection |

## Recommended Configuration

```bash
python -m benchmarks.run_bbox_docvqa \
    --aggregation-methods iou_weighted \
    --selection-methods relative \
    --relative-threshold 0.7 \
    --merge-regions \
    --merge-max-area 0.25 \
    --no-merge-for-text \
    --no-merge-for-table
```

### Parameter Justification

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `aggregation` | iou_weighted | Best balance of accuracy and selectivity |
| `selection` | relative | Adapts to score distribution |
| `relative-threshold` | 0.7 | More selective while maintaining coverage |
| `merge-regions` | enabled | Combines fragmented high-attention areas |
| `merge-max-area` | 0.25 | Prevents overly large regions |
| `no-merge-for-text` | enabled | Text regions don't benefit from merging |
| `no-merge-for-table` | enabled | Table structure should be preserved |

## Token Counting

### Vision Token Formula (Claude)

```python
# Images resized to fit within 1568×1568
scale = min(1.0, 1568 / max(width, height))
scaled_w, scaled_h = width * scale, height * scale

# Tiled into 512×512 tiles (ceiling)
n_tiles_x = ceil(scaled_w / 512)
n_tiles_y = ceil(scaled_h / 512)
total_tiles = n_tiles_x * n_tiles_y

# Token cost
tokens = total_tiles * 170 + 85  # 170 per tile + 85 base
```

### When Cropping Saves Tokens

Cropping only saves tokens when:
1. **Single small region** - One region covering < 50% of image
2. **Text extraction** - Sending OCR text instead of image crops
3. **Text/Table documents** - Filtering text content, not images

## Files Modified

| File | Changes |
|------|---------|
| `benchmarks/utils/coordinates.py` | Fixed DeepSeek OCR bbox normalization |
| `benchmarks/visualization.py` | Fixed alpha and normalization strategy |
| `benchmarks/run_bbox_docvqa.py` | Added CLI args, fixed token counting with source region tracking |
| `benchmarks/merging.py` | Store source_bboxes, source_labels, source_contents in raw_region |
| `benchmarks/config.py` | Added `default_threshold` parameter |

## Limitations & Future Work

1. **Image crop overhead** - Multiple crops cost more than full image. Consider:
   - Sending full image with region annotations
   - VLM-generated descriptions instead of crops

2. **Text/Table filtering** - Relative threshold doesn't filter well (uniform attention)
   - Consider higher threshold or different method per region type

3. **Token counting** - Capped at full image, but real savings require text extraction

## Conclusion

The patch-to-region relevance propagation approach successfully:
- Achieves **95% hit rate** (higher than baselines)
- Identifies relevant regions with **29% selection rate**
- Works best for **Image regions** with distinct attention patterns

**Key insight:** For image-heavy documents, token savings come from intelligent attention guidance rather than reducing image area. True token savings require text extraction (OCR descriptions) instead of image crops.
