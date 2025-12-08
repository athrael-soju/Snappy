# Benchmark Suite Audit Report

**Generated:** 2025-12-08
**Suite:** `backend/benchmarks/`

---

## Executive Summary

This report identifies issues in the benchmarking suite across four categories:
1. **Silent Fallbacks** - 5 critical issues that could skew results
2. **Unused/Obsolete Code** - 8 items to clean up
3. **Duplicated Code** - 3 areas with potential consolidation
4. **Refactoring Opportunities** - 4 structural improvements

---

## 1. Silent Fallbacks (CRITICAL)

Silent fallbacks can corrupt benchmark results without warning. These must be addressed immediately.

### 1.1 Hungarian Matching Falls Back to Greedy Silently

**File:** [evaluation.py:441-447](evaluation.py#L441-L447)

```python
def _hungarian_matching(self, iou_matrix: np.ndarray) -> Tuple[float, int]:
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        logger.warning("scipy not available for Hungarian matching, using greedy")
        return self._greedy_matching(iou_matrix)
```

**Problem:** If scipy is not installed, the benchmark silently degrades to greedy matching. The warning only appears in logs and results are reported as "Hungarian" when they're actually greedy.

**Impact:** HIGH - Results labeled as "Hungarian matching" may actually be greedy matching, producing different IoU values.

**Fix:** Fail loudly if scipy is unavailable when Hungarian matching is requested, or clearly label results as "greedy_fallback" in the output.

---

### 1.2 Bbox Normalization Auto-Detection Can Misinterpret Coordinates

**File:** [aggregation.py:280-300](aggregation.py#L280-L300)

```python
def _normalize_bbox(self, bbox, image_width, image_height):
    max_coord = max(x1, y1, x2, y2)

    if max_coord <= 1.0:
        return (x1, y1, x2, y2)  # Already normalized
    elif max_coord <= 999 and image_width is None:
        return (x1 / 999.0, ...)  # DeepSeek format
    elif image_width is not None and image_height is not None:
        return (x1 / image_width, ...)  # Pixel coordinates
    else:
        return (x1 / 999.0, ...)  # SILENT FALLBACK to DeepSeek
```

**Problem:** When `max_coord > 999` and image dimensions aren't provided, it silently falls back to DeepSeek normalization (dividing by 999), which produces incorrect results for pixel coordinates.

**Impact:** HIGH - Ground truth boxes could be normalized incorrectly, producing misleading IoU scores.

**Fix:** Raise an error if coordinate system cannot be reliably determined, or require explicit format specification.

---

### 1.3 Duplicate Fallback in baselines.py

**File:** [baselines.py:509-518](baselines.py#L509-L518)

```python
def _normalize_bbox(self, bbox):
    max_coord = max(x1, y1, x2, y2)
    if max_coord <= 1.0:
        return (x1, y1, x2, y2)
    elif max_coord <= 999:
        return (x1 / 999.0, ...)
    else:
        # Assume large pixel values - normalize by max
        return (x1 / max_coord, y1 / max_coord, ...)  # BROKEN!
```

**Problem:** This "normalize by max" fallback is mathematically incorrect - it doesn't preserve aspect ratio and produces boxes that don't match the original coordinates.

**Impact:** CRITICAL - Baseline comparisons could be corrupted if any bbox has coordinates > 999.

**Fix:** Remove this fallback and require explicit coordinate specification.

---

### 1.4 Empty OCR Regions Silently Skipped in Baselines

**File:** [run_bbox_docvqa.py:585-589](run_bbox_docvqa.py#L585-L589)

```python
for sample in samples:
    ocr_regions = self._ocr_regions_cache.get(sample.sample_id, [])
    if not ocr_regions:
        logger.warning(f"No cached OCR regions for {sample.sample_id}, skipping")
        predictions.append([])
        continue
```

**Problem:** Samples with missing OCR regions are silently included with empty predictions. This dilutes baseline metrics without explicit tracking.

**Impact:** MEDIUM - Baseline metrics may be artificially lower due to empty predictions for skipped samples.

**Fix:** Track skipped samples separately and report the count in results, or exclude them from metric calculation.

---

### 1.5 Unknown Baseline Method Silently Continues

**File:** [run_bbox_docvqa.py:635-636](run_bbox_docvqa.py#L635-L636)

```python
elif baseline_name == "top_left_bias":
    result = self.baseline_generator.top_left_bias(ocr_regions)
    ...
else:
    continue  # SILENT SKIP
```

**Problem:** If a baseline name in `config.baselines.enabled` doesn't match any known method, it's silently skipped with no warning.

**Impact:** LOW - Configuration errors go unnoticed.

**Fix:** Log a warning or raise an error for unknown baseline names.

---

## 2. Unused/Obsolete Code

### 2.1 Unused Import: `Union` in visualization.py

**File:** [visualization.py:15](visualization.py#L15)

```python
from typing import Any, Dict, List, Optional, Tuple, Union
```

The `Union` type is only used in the convenience function `save_debug_overlay` which accepts `Union[Image.Image, np.ndarray, str]`. However, this function is never called within the benchmark runner - it appears to be for external debugging only.

**Recommendation:** Keep if useful for manual debugging, otherwise remove.

---

### 2.2 Unused Methods in selection.py

**File:** [selection.py:364-403](selection.py#L364-L403)

The `select_all_methods()` method is defined but never called. The benchmark runner iterates over methods manually instead.

```python
def select_all_methods(
    self,
    region_scores: List[RegionScore],
    k_values: Optional[List[int]] = None,
    relative_thresholds: Optional[List[float]] = None,
) -> Dict[str, SelectionResult]:
```

**Recommendation:** Remove if not planned for use, or integrate into the benchmark runner for cleaner code.

---

### 2.3 Unused Convenience Function in selection.py

**File:** [selection.py:406-424](selection.py#L406-L424)

```python
def select_relevant_regions(
    region_scores: List[RegionScore],
    method: str = "top_k",
    **kwargs,
) -> List[RegionScore]:
```

This function is never imported or called anywhere.

**Recommendation:** Remove.

---

### 2.4 Unused Convenience Function in aggregation.py

**File:** [aggregation.py:338-390](aggregation.py#L338-L390)

```python
def aggregate_patches_to_regions(
    similarity_maps: List[Dict[str, Any]],
    regions: List[Dict[str, Any]],
    ...
) -> List[RegionScore]:
```

This "compatibility function" for the Snappy interpretability response format is never called. The benchmark uses `PatchToRegionAggregator` directly.

**Recommendation:** Remove or move to a compatibility layer if needed for future integration.

---

### 2.5 Unused Method: compute_all_methods in aggregation.py

**File:** [aggregation.py:302-335](aggregation.py#L302-L335)

```python
def compute_all_methods(
    self,
    heatmap: np.ndarray,
    regions: List[Dict[str, Any]],
    ...
) -> Dict[AggregationMethod, List[RegionScore]]:
```

Never called - the runner iterates over methods manually.

**Recommendation:** Remove or integrate for cleaner ablation code.

---

### 2.6 Unused run_all_baselines in baselines.py

**File:** [baselines.py:520-544](baselines.py#L520-L544)

```python
def run_all_baselines(
    self,
    regions: List[Dict[str, Any]],
    query: str,
    k: int = 5,
) -> Dict[str, BaselineResult]:
```

Never called - `_run_baselines()` in the runner handles this manually.

**Recommendation:** Remove or integrate.

---

### 2.7 Unused Precision/Recall@K Functions in evaluation.py

**File:** [evaluation.py:620-683](evaluation.py#L620-L683)

```python
def compute_precision_at_k(...) -> float:
def compute_recall_at_k(...) -> float:
```

These standalone functions are never imported or called. The evaluator uses its internal `_compute_coverage()` method instead.

**Recommendation:** Remove.

---

### 2.8 Unused EXAMPLE_CONFIG_YAML and save_example_config

**File:** [config.py:369-460](config.py#L369-L460)

```python
EXAMPLE_CONFIG_YAML = """..."""

def save_example_config(path: str = "benchmark_config.yaml") -> None:
```

Never called. Example config is embedded but not used.

**Recommendation:** Remove or expose via CLI flag (`--generate-config`).

---

## 3. Duplicated Code

### 3.1 Bbox Normalization (3 implementations)

The same normalization logic exists in three places:

| File | Function | Lines |
|------|----------|-------|
| [aggregation.py](aggregation.py#L257-L300) | `_normalize_bbox()` | 257-300 |
| [baselines.py](baselines.py#L501-L518) | `_normalize_bbox()` | 501-518 |
| [utils/coordinates.py](utils/coordinates.py#L46-L86) | `normalize_ocr_bbox()`, `normalize_gt_bbox()` | 46-86 |

**Impact:** Code maintenance burden, risk of bugs if one is updated but not others.

**Recommendation:** Consolidate into a single `normalize_bbox()` function in `utils/coordinates.py` with explicit format parameter:

```python
def normalize_bbox(
    bbox: List[float],
    format: Literal["deepseek", "pixel", "auto"],
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> NormalizedBox:
```

---

### 3.2 Region Content Extraction (2 implementations)

Similar logic for extracting text content from OCR grounding markers:

| File | Function | Location |
|------|----------|----------|
| [clients.py](clients.py#L230-L273) | `_extract_region_content()` | 230-273 |
| Main backend: `clients/ocr/processor.py` | `_extract_region_content()` | ~347-390 |

**Recommendation:** The benchmark client should import and reuse the main backend's OCR processor, or a shared utility should be extracted.

---

### 3.3 Aggregation Logic Overlap

**Benchmark:** [aggregation.py](aggregation.py) - 5 methods (max, mean, sum, iou_weighted, iou_weighted_norm)

**Main Backend:** [domain/region_relevance.py](../domain/region_relevance.py) - Simple inline aggregation

The main backend has simpler aggregation that could benefit from the benchmark's more sophisticated methods.

**Recommendation:** Consider extracting `PatchToRegionAggregator` to a shared utils module for reuse in the main backend.

---

## 4. Refactoring Opportunities

### 4.1 run_bbox_docvqa.py is Too Large (1319 lines)

The main runner file handles too many responsibilities:
- CLI argument parsing (100+ lines)
- Configuration management
- Service health checks
- Sample processing
- Baseline execution
- Visualization generation
- Results serialization
- Summary printing

**Recommendation:** Split into:
- `cli.py` - Argument parsing and main entrypoint
- `runner.py` - Core BenchmarkRunner class
- `reporting.py` - Summary generation and printing
- `io.py` - Results saving and loading

---

### 4.2 Visualization Parameters Scattered Across Config

Visualization settings are split between:
- `VisualizationConfig` in config.py
- Hardcoded `COLORS` dict in visualization.py
- Hardcoded thresholds (e.g., `iou_threshold = 0.25` in visualization.py:147)

**Recommendation:** Consolidate all visualization parameters into `VisualizationConfig` and pass through properly.

---

### 4.3 Coordinate Utilities Should Be Promoted

The coordinate utilities in `utils/coordinates.py` are general-purpose and would be useful in the main Snappy backend:

- `compute_iou()` - Used for evaluation
- `get_overlapping_patches()` - Useful for region relevance
- `normalize_*_bbox()` - Useful everywhere

**Recommendation:** Promote to `backend/utils/coordinates.py` (new file in main utils) and import in benchmarks.

---

### 4.4 Missing Dependency Injection for Services

The `BenchmarkRunner` creates its own service clients internally:

```python
self.colpali_client = colpali_client or BenchmarkColPaliClient(...)
self.ocr_client = ocr_client or BenchmarkOcrClient(...)
```

**Recommendation:** Use proper dependency injection or a service factory for easier testing and configuration.

---

## Priority Action Items

### Immediate (Before Next Benchmark Run)

1. **Fix baselines.py normalize_bbox fallback** - The "divide by max" logic is mathematically wrong
2. **Add explicit format parameter to normalization** - Remove auto-detection that can misinterpret coordinates
3. **Fail loudly on missing scipy** - Don't silently fall back to greedy matching

### Short Term (Next Sprint)

4. Consolidate bbox normalization into single utility
5. Track and report skipped samples explicitly
6. Remove unused convenience functions
7. Add validation for unknown baseline names

### Medium Term (Technical Debt)

8. Split run_bbox_docvqa.py into smaller modules
9. Promote coordinate utilities to main backend
10. Consider reusing OCR processor from main backend

---

## Appendix: Files Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| run_bbox_docvqa.py | 1319 | Main benchmark runner |
| evaluation.py | 684 | Metrics and matching |
| aggregation.py | 391 | Patch-to-region scoring |
| selection.py | 425 | Region selection strategies |
| baselines.py | 545 | Baseline methods |
| clients.py | 274 | Service clients |
| visualization.py | 565 | Debug visualizations |
| config.py | 461 | Configuration |
| loaders/bbox_docvqa.py | 609 | Dataset loading |
| utils/coordinates.py | 256 | Coordinate utilities |
| **Total** | **5529** | |
