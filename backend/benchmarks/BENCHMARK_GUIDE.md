# ColPali Patch-Level Similarity Scores as Spatial Relevance Filters: Implementation Guide

Vision-language document retrieval has reached an inflection point where **ColPali's patch-level embeddings can now spatially filter OCR regions** at inference time without additional training. This guide formalizes the mathematical framework for mapping ColPali's 32×32 patch grid to arbitrary OCR bounding boxes, validates the core algorithms, and designs a benchmark suite using BBox-DocVQA. The approach achieves region-level retrieval precision while preserving semantic grounding—enabling RAG systems to return specific paragraphs rather than entire pages.

## ColPali's Late Interaction mechanism enables per-patch relevance scoring

ColPali (Faysse et al., ICLR 2025) extends the ColBERT late interaction paradigm to document images. The architecture processes documents through PaliGemma-3B, which combines a **SigLIP-So400m/14 vision encoder** with a Gemma-2B language model. Each document page produces **1,030 embeddings**: 1,024 from the 32×32 patch grid (448×448 pixels ÷ 14×14 patch size), plus 6 special tokens.

The core scoring mechanism follows MaxSim aggregation:

```
S(q, d) = Σᵢ maxⱼ (eᵢᵍ · eⱼᵈ)
```

Where `eᵢᵍ` represents the i-th query token embedding and `eⱼᵈ` the j-th document patch embedding, both projected to **128 dimensions**. Critically, the intermediate similarity matrix `sim(eᵢᵍ, eⱼᵈ)` for each query-patch pair is accessible before aggregation—this is the foundation for spatial filtering.

**Mathematical validation note**: The formula is mathematically sound. With L2-normalized embeddings, the dot product equals cosine similarity. The MaxSim operation finds the best-matching patch for each query token, then sums across tokens. This produces per-patch relevance scores that can be reshaped to a 32×32 spatial grid.

## Step 1: Patch-to-region score propagation requires coordinate mapping

The fundamental challenge is mapping ColPali's discrete patch grid to continuous OCR bounding box coordinates. The Snappy system (arXiv:2512.02660) formalizes this as an IoU-weighted intersection problem.

### Patch coordinate computation

For a patch at index `k` in the flattened sequence (row-major order):

```python
def patch_to_pixel_bbox(k, image_size=448, patch_size=14):
    grid_size = image_size // patch_size  # 32 for standard ColPali
    row = k // grid_size
    col = k % grid_size
    return {
        'x_min': col * patch_size,
        'y_min': row * patch_size,
        'x_max': (col + 1) * patch_size,
        'y_max': (row + 1) * patch_size
    }
```

### Finding overlapping patches for an OCR region

Given an OCR bounding box `R = (x₁, y₁, x₂, y₂)`, identify all patches that overlap:

```python
def get_overlapping_patches(ocr_bbox, image_size=448, patch_size=14):
    grid_size = image_size // patch_size
    x1, y1, x2, y2 = ocr_bbox
    
    # Convert pixel coords to patch indices (inclusive range)
    col_start = max(0, x1 // patch_size)
    col_end = min(grid_size - 1, (x2 - 1) // patch_size)
    row_start = max(0, y1 // patch_size)
    row_end = min(grid_size - 1, (y2 - 1) // patch_size)
    
    patches = []
    for row in range(row_start, row_end + 1):
        for col in range(col_start, col_end + 1):
            patch_idx = row * grid_size + col
            patch_bbox = patch_to_pixel_bbox(patch_idx, image_size, patch_size)
            overlap = compute_intersection_area(patch_bbox, ocr_bbox)
            if overlap > 0:
                patches.append((patch_idx, overlap))
    return patches
```

### Score aggregation strategies

Three aggregation methods map patch similarity scores to region relevance:

| Strategy | Formula | Use Case |
|----------|---------|----------|
| **Max Pooling** | `R_score = max(sₖ)` for k ∈ overlapping patches | Captures peak relevance; sensitive to single high-scoring patch |
| **Mean Pooling** | `R_score = (Σ sₖ · wₖ) / (Σ wₖ)` where wₖ = overlap area | Balanced; smooths noise but may dilute strong signals |
| **Area-Normalized Sum** | `R_score = Σ (sₖ · overlapₖ) / region_area` | Proportional contribution; handles variable region sizes |

**Implementation recommendation**: Use **IoU-weighted mean pooling** as the default, where `wₖ = IoU(patch_k, region)`:

```python
def aggregate_region_score(patch_scores, overlapping_patches, ocr_bbox):
    ocr_area = (ocr_bbox[2] - ocr_bbox[0]) * (ocr_bbox[3] - ocr_bbox[1])
    
    weighted_sum = 0
    weight_total = 0
    
    for patch_idx, overlap_area in overlapping_patches:
        patch_area = 14 * 14  # patch_size^2
        union = patch_area + ocr_area - overlap_area
        iou = overlap_area / union if union > 0 else 0
        
        weighted_sum += patch_scores[patch_idx] * iou
        weight_total += iou
    
    return weighted_sum / weight_total if weight_total > 0 else 0
```

### Critical assumption flagged: Resolution alignment

⚠️ **Assumption**: OCR bounding boxes are in the same coordinate space as the processed image (448×448 pixels for standard ColPali). If the original document was higher resolution, coordinates must be scaled:

```python
scale_x = 448 / original_width
scale_y = 448 / original_height
scaled_bbox = (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)
```

This scaling introduces quantization error—small OCR regions (<35×35 pixels at original resolution) may map to single patches, losing spatial discrimination.

## Step 2: Region filtering strategies balance recall and precision

### Threshold-based filtering

The simplest approach applies a fixed relevance threshold:

```python
def filter_by_threshold(regions, scores, threshold=0.3):
    return [r for r, s in zip(regions, scores) if s >= threshold]
```

**Threshold selection guidance**: Snappy uses `REGION_RELEVANCE_THRESHOLD=0.3` as default. Optimal thresholds depend on:
- Score distribution (normalize to [0,1] using min-max across all regions)
- Downstream task tolerance for false positives vs. false negatives
- Average region count per page (higher → stricter threshold)

### Top-k selection

Returns the k highest-scoring regions regardless of absolute score:

```python
def filter_topk(regions, scores, k=5):
    ranked = sorted(zip(regions, scores), key=lambda x: x[1], reverse=True)
    return [r for r, s in ranked[:k]]
```

**Issue**: Fixed k ignores query specificity. A query about "table 3" needs one region; "all methods discussed" may need many.

### Adaptive filtering using score distribution

More sophisticated: use statistical properties of the score distribution:

```python
def adaptive_filter(regions, scores, z_threshold=1.0):
    """Keep regions scoring > mean + z_threshold * std"""
    import numpy as np
    scores_arr = np.array(scores)
    mean_score = scores_arr.mean()
    std_score = scores_arr.std()
    
    threshold = mean_score + z_threshold * std_score
    return [r for r, s in zip(regions, scores) if s >= threshold]
```

**Variant**: Knee detection on the sorted score curve identifies the natural cutoff point:

```python
def knee_filter(regions, scores):
    """Uses elbow method to find natural score cutoff"""
    sorted_scores = sorted(scores, reverse=True)
    n = len(sorted_scores)
    
    # Vector from first to last point
    p1 = np.array([0, sorted_scores[0]])
    p2 = np.array([n-1, sorted_scores[-1]])
    
    # Find point with maximum perpendicular distance
    max_dist = 0
    knee_idx = 0
    for i, s in enumerate(sorted_scores):
        point = np.array([i, s])
        dist = np.abs(np.cross(p2-p1, p1-point)) / np.linalg.norm(p2-p1)
        if dist > max_dist:
            max_dist = dist
            knee_idx = i
    
    threshold = sorted_scores[knee_idx]
    return [r for r, s in zip(regions, scores) if s >= threshold]
```

### Two-stage retrieval pipeline

Snappy implements an efficient two-stage approach:

1. **Stage 1** (Candidate retrieval): Mean-pooled page embeddings for fast approximate search
2. **Stage 2** (Region reranking): Full patch-level scoring on top-k candidate pages, then region filtering

```python
def two_stage_retrieval(query, pages, k1=100, k2=10):
    # Stage 1: Coarse page ranking
    page_scores = [(p, mean_pooled_score(query, p)) for p in pages]
    candidates = sorted(page_scores, key=lambda x: x[1], reverse=True)[:k1]
    
    # Stage 2: Fine-grained region scoring
    all_regions = []
    for page, _ in candidates:
        patch_scores = compute_patch_similarities(query, page)
        for region in page.ocr_regions:
            r_score = aggregate_region_score(patch_scores, region)
            all_regions.append((region, r_score))
    
    # Return top-k2 regions
    return sorted(all_regions, key=lambda x: x[1], reverse=True)[:k2]
```

## Step 3: Spatial grounding benchmark on BBox-DocVQA

BBox-DocVQA (Yu et al., November 2025) provides **32,000 QA pairs across 3,600 documents** with ground-truth evidence bounding boxes. Three instance types test different complexity levels:

| Type | Description | Benchmark % |
|------|-------------|-------------|
| SPSBB | Single-Page Single-BBox | 46.15% |
| SPMBB | Single-Page Multi-BBox | 34.26% |
| MPMBB | Multi-Page Multi-BBox | 19.59% |

### IoU computation for evaluation

```python
def compute_iou(pred_bbox, gt_bbox):
    """
    Both boxes: (x_min, y_min, x_max, y_max)
    Returns IoU in [0, 1]
    """
    # Intersection
    xi1 = max(pred_bbox[0], gt_bbox[0])
    yi1 = max(pred_bbox[1], gt_bbox[1])
    xi2 = min(pred_bbox[2], gt_bbox[2])
    yi2 = min(pred_bbox[3], gt_bbox[3])
    
    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    intersection = inter_width * inter_height
    
    # Union
    area_pred = (pred_bbox[2] - pred_bbox[0]) * (pred_bbox[3] - pred_bbox[1])
    area_gt = (gt_bbox[2] - gt_bbox[0]) * (gt_bbox[3] - gt_bbox[1])
    union = area_pred + area_gt - intersection
    
    return intersection / union if union > 0 else 0
```

### Multi-region evaluation

For SPMBB/MPMBB cases with multiple ground-truth regions, use set-based metrics:

```python
def evaluate_multi_region(pred_regions, gt_regions, iou_threshold=0.5):
    """
    Computes precision, recall, F1 at given IoU threshold
    """
    matched_gt = set()
    true_positives = 0
    
    for pred in pred_regions:
        best_iou = 0
        best_gt_idx = -1
        for i, gt in enumerate(gt_regions):
            if i in matched_gt:
                continue
            iou = compute_iou(pred, gt)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = i
        
        if best_iou >= iou_threshold and best_gt_idx >= 0:
            true_positives += 1
            matched_gt.add(best_gt_idx)
    
    precision = true_positives / len(pred_regions) if pred_regions else 0
    recall = true_positives / len(gt_regions) if gt_regions else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {'precision': precision, 'recall': recall, 'f1': f1}
```

### Benchmark suite design

```python
class SpatialGroundingBenchmark:
    """Evaluates ColPali patch-to-region filtering on BBox-DocVQA"""
    
    def __init__(self, dataset_path, colpali_model, ocr_engine):
        self.dataset = load_bbox_docvqa(dataset_path)
        self.colpali = colpali_model
        self.ocr = ocr_engine
        
    def run_evaluation(self, filtering_strategy, params):
        results = {
            'SPSBB': [], 'SPMBB': [], 'MPMBB': [],
            'iou_scores': [], 'mean_iou': 0
        }
        
        for sample in self.dataset:
            # 1. Get OCR regions for document
            ocr_regions = self.ocr.extract(sample['image'])
            
            # 2. Compute patch-level similarities
            patch_scores = self.colpali.get_patch_similarities(
                sample['question'], sample['image']
            )
            
            # 3. Propagate to regions
            region_scores = []
            for region in ocr_regions:
                score = aggregate_region_score(
                    patch_scores, 
                    get_overlapping_patches(region['bbox']),
                    region['bbox']
                )
                region_scores.append((region, score))
            
            # 4. Apply filtering strategy
            pred_regions = filtering_strategy(
                [r for r, s in region_scores],
                [s for r, s in region_scores],
                **params
            )
            
            # 5. Evaluate against ground truth
            metrics = evaluate_multi_region(
                [r['bbox'] for r in pred_regions],
                sample['gt_bboxes']
            )
            
            results[sample['type']].append(metrics)
            results['iou_scores'].append(
                max([compute_iou(p['bbox'], g) 
                     for p in pred_regions for g in sample['gt_bboxes']] or [0])
            )
        
        # Aggregate results
        results['mean_iou'] = np.mean(results['iou_scores'])
        for qtype in ['SPSBB', 'SPMBB', 'MPMBB']:
            results[f'{qtype}_f1'] = np.mean([m['f1'] for m in results[qtype]])
        
        return results
```

### Recommended evaluation metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Mean IoU** | Average IoU across all predictions | Primary spatial accuracy |
| **IoU@0.5** | % predictions with IoU ≥ 0.5 | Standard detection threshold |
| **IoU@0.7** | % predictions with IoU ≥ 0.7 | Stricter localization |
| **Recall@k** | % GT regions matched by top-k predictions | Coverage metric |
| **Context Reduction** | 1 - (filtered_tokens / page_tokens) | Efficiency gain |

## Critical issues and assumptions to validate

### Issue 1: Granularity mismatch

ColPali patches are 14×14 pixels. At 448×448 input resolution, this provides **~0.1% of page area per patch**. OCR regions vary from single characters (~10×15px) to full paragraphs (~400×100px).

**Impact**: Regions smaller than ~35×35 pixels (2.5× patch size) achieve <50% localization precision—the patch-to-region mapping becomes dominated by surrounding content.

**Mitigation**: Use PaliGemma at 896×896 resolution (4,096 patches) for fine-grained applications, accepting 4× computational cost.

### Issue 2: Similarity map reliability

Recent research (AAAI 2025) warns that **ColPali similarity maps can be "fragile and misleading"** for interpretability. The MaxSim operation optimizes for page-level retrieval, not pixel-level localization.

**Validation approach**: Cross-check high-scoring patches against OCR text content. If patches over whitespace consistently score high, this indicates "register" behavior where patches store global information rather than local semantics.

### Issue 3: Coordinate system misalignment

Three coordinate systems must align:
1. Original document pixels
2. ColPali processed resolution (448×448)
3. OCR bounding box coordinates

**Assumption check**: Verify OCR coordinates are normalized consistently. Some OCR engines output normalized [0,1] coordinates; others use absolute pixels at varying resolutions.

```python
def normalize_bbox(bbox, source_width, source_height, target_size=448):
    """Standardize to ColPali coordinate space"""
    x1, y1, x2, y2 = bbox
    return (
        x1 * target_size / source_width,
        y1 * target_size / source_height,
        x2 * target_size / source_width,
        y2 * target_size / source_height
    )
```

### Issue 4: Query token contribution asymmetry

MaxSim aggregates maximum patch scores per query token, then sums. This means:
- Stopwords ("the", "a") contribute equally to content words
- Multi-word queries have higher absolute scores than single-word queries

**Normalization recommendation**: Divide final region score by number of query tokens for comparability:

```python
normalized_score = region_score / num_query_tokens
```

### Issue 5: BBox-DocVQA ground truth granularity

BBox-DocVQA uses SAM-generated regions, which are semantically coherent (paragraphs, tables, figures) but may not match OCR segmentation boundaries exactly. OCR typically produces word-level or line-level boxes.

**Benchmark adjustment**: Merge adjacent OCR boxes into semantic regions before evaluation, or evaluate at the "answer span" level rather than exact bbox match.

## Complete implementation pseudocode

```python
class ColPaliSpatialFilter:
    def __init__(self, model_name="vidore/colpali", image_size=448, patch_size=14):
        self.model = load_colpali(model_name)
        self.image_size = image_size
        self.patch_size = patch_size
        self.grid_size = image_size // patch_size  # 32
        
    def get_patch_similarity_map(self, query: str, image: Image) -> np.ndarray:
        """Returns (num_query_tokens, grid_size, grid_size) similarity tensor"""
        query_emb = self.model.encode_query(query)  # (K, 128)
        patch_emb = self.model.encode_image(image)  # (1024, 128)
        
        # Compute all pairwise similarities
        sim_matrix = query_emb @ patch_emb.T  # (K, 1024)
        
        # Reshape to spatial grid
        sim_maps = sim_matrix.reshape(-1, self.grid_size, self.grid_size)
        return sim_maps
    
    def aggregate_per_region(self, sim_maps: np.ndarray, 
                              ocr_regions: List[Dict],
                              strategy: str = 'iou_weighted') -> List[Tuple[Dict, float]]:
        """
        Propagate patch scores to OCR regions.
        Returns list of (region, score) tuples.
        """
        # Aggregate across query tokens (max per patch, then we'll aggregate to regions)
        patch_scores = sim_maps.max(axis=0)  # (32, 32) - best query token per patch
        
        results = []
        for region in ocr_regions:
            bbox = self.normalize_bbox(region['bbox'])
            overlaps = self.get_overlapping_patches(bbox)
            
            if strategy == 'max':
                score = max(patch_scores[r, c] for _, r, c in overlaps)
            elif strategy == 'iou_weighted':
                weighted_sum = sum(
                    patch_scores[r, c] * iou for iou, r, c in overlaps
                )
                weight_total = sum(iou for iou, _, _ in overlaps)
                score = weighted_sum / weight_total if weight_total > 0 else 0
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            results.append((region, score))
        
        return results
    
    def filter_regions(self, scored_regions: List[Tuple[Dict, float]],
                       method: str = 'adaptive',
                       threshold: float = 0.3,
                       k: int = 5) -> List[Dict]:
        """Apply filtering strategy to scored regions."""
        
        regions = [r for r, s in scored_regions]
        scores = [s for r, s in scored_regions]
        
        if method == 'threshold':
            return [r for r, s in scored_regions if s >= threshold]
        elif method == 'topk':
            ranked = sorted(scored_regions, key=lambda x: x[1], reverse=True)
            return [r for r, s in ranked[:k]]
        elif method == 'adaptive':
            mean_s = np.mean(scores)
            std_s = np.std(scores)
            adaptive_threshold = mean_s + std_s
            return [r for r, s in scored_regions if s >= adaptive_threshold]
        elif method == 'knee':
            return self.knee_detection_filter(scored_regions)
        else:
            raise ValueError(f"Unknown method: {method}")
```

## Conclusion: Three key insights for implementation

**First**, the mathematical foundation is sound but resolution-constrained. ColPali's 14×14 patches provide ~1K spatial bins per page—sufficient for paragraph-level localization but inadequate for character-level precision. Implementers should expect **~35-50% mean IoU** on BBox-DocVQA based on current SOTA performance (Qwen2.5VL-72B achieves 35.2%).

**Second**, score aggregation strategy significantly impacts results. IoU-weighted mean pooling provides the best balance between noise robustness and signal preservation. Max pooling works well when queries target specific visual elements; mean pooling is preferable for text-heavy regions spanning multiple patches.

**Third**, the benchmark design must account for granularity mismatch between SAM-generated ground truth (semantic regions) and OCR segmentation (lexical spans). Consider evaluating "answer containment" rather than strict IoU when OCR produces finer-grained boxes than the ground truth annotations.

The Snappy implementation demonstrates practical viability with its two-stage retrieval pipeline. Region-level filtering achieves meaningful context reduction (typically 60-80% fewer tokens passed to LLM) while maintaining recall, directly improving RAG answer quality through reduced noise.