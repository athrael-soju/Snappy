# Spatial Grounding in Snappy

## Overview

Snappy implements **spatially-grounded document retrieval**, preserving spatial layout information throughout the entire retrieval pipeline—from PDF pages to visual embeddings to region-level filtering. This approach enables Snappy to understand not just *what* content matches a query, but precisely *where* on the page that content appears.

## Why Spatial Grounding Matters

Traditional text-based RAG systems lose spatial context during extraction. When you search for "total revenue," you get text snippets but no understanding of whether they came from a table header, chart label, or footnote.

Snappy's spatial grounding solves this by:
- **Preserving layout semantics**: Headers, tables, charts, and annotations maintain their spatial relationships
- **Enabling region-level precision**: Return only the parts of a page relevant to the query
- **Supporting visual understanding**: Handwriting, diagrams, and complex layouts remain searchable
- **Query-focused filtering**: Use attention-based interpretability to identify which regions matter

## The Spatial Pipeline

### 1. PDF → Rasterized Images (Pixel Space)

Each PDF page is rasterized to a high-resolution image:
```
PDF Page → PNG Image (e.g., 2048 × 1536 pixels)
```

Spatial coordinates at this stage are in **pixel space**: `(x, y)` coordinates where `(0, 0)` is the top-left corner.

**Implementation**: [`backend/domain/pipeline/stages/pdf_rasterizer.py`](../domain/pipeline/stages/pdf_rasterizer.py)

---

### 2. Images → Patch Grid (Patch Space)

ColPali divides each image into a grid of **patches** (typically 16×16 pixels each):

```
Image (2048 × 1536 px) → Patch Grid (128 × 96 patches)
```

Each patch becomes a token in the vision transformer. The spatial transformation is:
```python
patch_x = pixel_x / patch_width   # e.g., 1024 / 16 = 64
patch_y = pixel_y / patch_height  # e.g., 768 / 16 = 48
```

**Key insight**: Spatial information is now encoded in the **position** of each patch token in the embedding sequence.

**Implementation**: [`colpali/app/services/embedding_processor.py`](../../colpali/app/services/embedding_processor.py)

---

### 3. Patches → Multi-Vector Embeddings (Embedding Space)

ColPali generates a **multi-vector embedding** for each page—one vector per patch:

```
Patch Grid (128 × 96) → Embedding Tensor (12,288 × 128 dimensions)
```

Each patch embedding captures:
- **Visual features**: Colors, textures, shapes in that patch
- **Semantic features**: What content appears (text, table, chart, etc.)
- **Spatial context**: Relationships to neighboring patches via self-attention

The embeddings preserve spatial structure because:
1. Each vector corresponds to a specific patch location
2. Patch positions are maintained in the sequence
3. Attention mechanisms learn spatial relationships

**Storage**: Embeddings are stored in Qdrant with metadata linking back to pixel coordinates:
```json
{
  "embedding": [[0.23, -0.45, ...], ...],  // Multi-vector
  "page_width_px": 2048,
  "page_height_px": 1536
}
```

**Implementation**: [`backend/clients/colpali.py`](../clients/colpali.py), [`backend/clients/qdrant/indexing/points.py`](../clients/qdrant/indexing/points.py)

---

### 4. Query → Interpretability Maps (Similarity Space)

When a user searches, ColPali generates **interpretability maps** showing which patches are most relevant:

```
Query: "total revenue"
      ↓
Query Embedding (N tokens × 128 dimensions)
      ↓
Token-wise Similarity Computation
      ↓
Interpretability Maps (one per query token)
Each map: 2D grid (96 × 128) of similarity scores
```

**Example**:
- Query token "total" → Similarity map highlighting table headers
- Query token "revenue" → Similarity map highlighting the revenue column

Each similarity score indicates how much that patch contributes to matching that query token.

**Implementation**: [`colpali/app/services/embedding_processor.py:generate_interpretability_maps`](../../colpali/app/services/embedding_processor.py), [`backend/api/routers/interpretability.py`](../api/routers/interpretability.py)

---

### 5. Interpretability Maps → Region Filtering (Region Space)

For documents with OCR, Snappy can filter regions based on query relevance:

```
OCR Regions (pixel coordinates) + Interpretability Maps (patch coordinates)
      ↓
Coordinate Transformation
      ↓
Region Relevance Scores
      ↓
Filtered Regions (only relevant to query)
```

**The Algorithm** ([`backend/domain/region_relevance.py`](../domain/region_relevance.py)):

1. **Get OCR bounding boxes** in pixel space:
   ```python
   bbox = [x1, y1, x2, y2]  # e.g., [512, 768, 1024, 896]
   ```

2. **Transform to patch space**:
   ```python
   patch_x1 = int(x1 / patch_width)   # 512 / 16 = 32
   patch_y1 = int(y1 / patch_height)  # 768 / 16 = 48
   patch_x2 = int(x2 / patch_width)   # 1024 / 16 = 64
   patch_y2 = int(y2 / patch_height)  # 896 / 16 = 56
   ```

3. **Extract similarity values** for patches overlapping this region:
   ```python
   for token_map in similarity_maps:
       region_similarities = token_map[patch_y1:patch_y2, patch_x1:patch_x2]
       token_score = max(region_similarities)  # Highest similarity in region
   ```

4. **Aggregate across query tokens**:
   ```python
   relevance_score = max(token_scores)  # or mean/sum
   ```

5. **Filter and rank**:
   ```python
   if relevance_score >= threshold:  # e.g., 0.3
       keep_region()
   ```

**Result**: Only OCR regions with high attention scores are returned, reducing noise and improving precision.

**Implementation**: [`backend/domain/region_relevance.py`](../domain/region_relevance.py), [`backend/domain/retrieval.py:_filter_regions_by_interpretability`](../domain/retrieval.py)

---

## Coordinate System Transformations

### Visual Summary
```
┌─────────────────────────────────────────────────────────────┐
│                     SPATIAL PIPELINE                         │
└─────────────────────────────────────────────────────────────┘

PDF Page
   ↓
Rasterize
   ↓
┌──────────────────────────┐
│  PIXEL SPACE             │  Image: 2048 × 1536 px
│  (x, y) coordinates      │  OCR bboxes: [x1, y1, x2, y2]
└──────────────────────────┘
   ↓
Patchify (16×16)
   ↓
┌──────────────────────────┐
│  PATCH SPACE             │  Grid: 128 × 96 patches
│  (patch_x, patch_y)      │  patch_x = x / 16
└──────────────────────────┘
   ↓
Vision Transformer
   ↓
┌──────────────────────────┐
│  EMBEDDING SPACE         │  Multi-vector: 12,288 × 128D
│  Position-encoded        │  Each vector ↔ one patch
└──────────────────────────┘
   ↓
Query Matching
   ↓
┌──────────────────────────┐
│  SIMILARITY SPACE        │  Interpretability: 96 × 128 scores
│  Per-token heatmaps      │  High score = relevant patch
└──────────────────────────┘
   ↓
Region Filtering
   ↓
┌──────────────────────────┐
│  REGION SPACE            │  Filtered OCR regions
│  Relevance-scored        │  bbox + relevance_score
└──────────────────────────┘
```

### Transformation Functions

**Pixel → Patch**:
```python
def pixel_to_patch(x_px: int, y_px: int, patch_size: int = 16) -> tuple:
    return (x_px // patch_size, y_px // patch_size)
```

**Patch → Embedding Index**:
```python
def patch_to_index(patch_x: int, patch_y: int, grid_width: int) -> int:
    return patch_y * grid_width + patch_x
```

**Region Bbox → Patch Range**:
```python
def bbox_to_patch_range(bbox: list, patch_width: float, patch_height: float) -> tuple:
    x1, y1, x2, y2 = bbox
    return (
        int(x1 / patch_width),   # patch_x1
        int(y1 / patch_height),  # patch_y1
        int(ceil(x2 / patch_width)),   # patch_x2
        int(ceil(y2 / patch_height)),  # patch_y2
    )
```

---

## Configuration

Region-level retrieval using spatial grounding is controlled by these settings ([`backend/config/schema/retrieval.py`](../config/schema/retrieval.py)):

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_REGION_LEVEL_RETRIEVAL` | `false` | Enable query-focused region filtering using interpretability maps |
| `REGION_RELEVANCE_THRESHOLD` | `0.3` | Minimum relevance score (0.0-1.0) to include a region |
| `REGION_TOP_K` | `0` | Max regions per page (0 = no limit) |
| `REGION_SCORE_AGGREGATION` | `"max"` | How to combine token scores: `max`, `mean`, or `sum` |

### Choosing Threshold Values

- **0.1 - 0.3 (inclusive)**: Returns more regions, including marginally relevant ones. Good for exploratory search.
- **0.3 - 0.5 (balanced)**: Default range. Filters noise while retaining relevant content.
- **0.5 - 0.7 (strict)**: Only highly relevant regions. May miss peripheral content.
- **0.7+ (very strict)**: Extreme precision. Risk of missing valid matches.

### Aggregation Strategies

- **`max`** (default): Best for OR-style queries. Region included if *any* query token matches strongly.
- **`mean`**: Balanced approach. Region must match multiple tokens reasonably well.
- **`sum`**: Favors regions matching many tokens. Good for long, specific queries.

---

## Use Cases

### 1. Financial Documents
**Scenario**: Search for "Q4 revenue" in a 50-page financial report.

**Without spatial grounding**:
- Returns all pages mentioning "Q4" or "revenue"
- Returns entire pages, including irrelevant sections

**With spatial grounding**:
- Returns only the table cells or chart regions showing Q4 revenue figures
- Filters out footnotes, disclaimers, and unrelated mentions

### 2. Scientific Papers
**Scenario**: Find figures about "protein structure" in a research paper.

**Without spatial grounding**:
- Text extraction misses figure content
- Returns paragraphs mentioning proteins, but not the actual diagrams

**With spatial grounding**:
- Identifies figure regions with high visual similarity to query
- Returns bounding boxes of relevant diagrams and captions

### 3. Forms and Invoices
**Scenario**: Extract "total amount" from scanned invoices.

**Without spatial grounding**:
- OCR returns all text in reading order
- Hard to distinguish "subtotal" from "total"

**With spatial grounding**:
- Spatial context identifies the "total" row in the table
- Returns only the region containing the final amount

---

## Performance Considerations

**Computational Cost**:
- **Interpretability map generation**: ~100-200ms per page per query
- **Region filtering**: ~5-10ms (numpy operations)
- **Total overhead**: ~100-210ms per page with OCR

**When to Enable**:
- ✅ Text-heavy documents with many OCR regions
- ✅ Complex layouts (tables, forms, multi-column)
- ✅ Need high precision (reduce false positives)
- ❌ Simple documents with minimal text
- ❌ Latency-critical applications (<100ms required)
- ❌ Vision-only mode (no OCR regions to filter)

**Optimization Tips**:
1. Cache interpretability maps for repeated queries on same documents
2. Use `REGION_TOP_K` to limit per-page processing
3. Increase `REGION_RELEVANCE_THRESHOLD` to reduce computation on low-scoring regions

---

## API Reference

### Generate Interpretability Maps
```http
POST /api/interpretability
Content-Type: multipart/form-data

query: "revenue analysis"
file: <image binary>
```

**Response**:
```json
{
  "query": "revenue analysis",
  "tokens": ["revenue", "analysis"],
  "similarity_maps": [
    {
      "token": "revenue",
      "similarity_map": [[0.12, 0.45, ...], ...]  // 96 × 128 grid
    },
    {
      "token": "analysis",
      "similarity_map": [[0.23, 0.34, ...], ...]
    }
  ],
  "n_patches_x": 128,
  "n_patches_y": 96,
  "image_width": 2048,
  "image_height": 1536
}
```

### Search with Region Filtering
Region filtering is applied automatically during search when:
1. `ENABLE_REGION_LEVEL_RETRIEVAL=true`
2. `include_ocr=true` in search request
3. OCR data exists for the result pages

The filtered regions are returned in the `ocr_regions` field with added `relevance_score`:
```json
{
  "results": [
    {
      "page_id": "doc123_page1",
      "score": 0.89,
      "ocr_regions": [
        {
          "content": "Total Revenue: $1.2M",
          "bbox": [512, 768, 1024, 896],
          "label": "table_cell",
          "relevance_score": 0.87
        }
      ]
    }
  ]
}
```

---

## Implementation Details

### Key Files
- **Region relevance scoring**: [`backend/domain/region_relevance.py`](../domain/region_relevance.py)
- **Search integration**: [`backend/domain/retrieval.py:_filter_regions_by_interpretability`](../domain/retrieval.py)
- **Configuration schema**: [`backend/config/schema/retrieval.py`](../config/schema/retrieval.py)
- **Interpretability API**: [`backend/api/routers/interpretability.py`](../api/routers/interpretability.py)
- **ColPali integration**: [`colpali/app/services/embedding_processor.py`](../../colpali/app/services/embedding_processor.py)

### Testing
To test region-level retrieval:
1. Upload a document with OCR enabled (`DEEPSEEK_OCR_ENABLED=true`)
2. Enable region filtering in Configuration UI or `.env`:
   ```bash
   ENABLE_REGION_LEVEL_RETRIEVAL=true
   REGION_RELEVANCE_THRESHOLD=0.3
   ```
3. Perform a search with `include_ocr=true`
4. Inspect the `relevance_score` field in returned regions

---

## Future Enhancements

Potential improvements to spatial grounding:
1. **Caching interpretability maps** for repeated queries
2. **Multi-scale patch grids** for better resolution
3. **Region clustering** to merge adjacent high-relevance patches
4. **Spatial metadata in embeddings** (explicit position encoding)
5. **Adaptive thresholding** based on query complexity
6. **Cross-page spatial relationships** for multi-page tables

---

## References

- **ColPali paper**: "ColPali: Efficient Document Retrieval with Vision Language Models"
- **Vision transformers**: "An Image is Worth 16x16 Words" (ViT paper)
- **Late interaction**: "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction"
- **Interpretability**: Derived from attention mechanisms in vision-language models

---

## Related Documentation
- [Late Interaction Mechanism](late_interaction.md) - Multi-vector retrieval explained
- [Architecture Overview](architecture.md) - System design
- [Configuration Reference](configuration.md) - All settings
- [Analysis: Vision vs Text RAG](analysis.md) - When to use spatial grounding
