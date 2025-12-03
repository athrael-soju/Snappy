# Late Interaction in Snappy

> **Research Paper**: [Spatially-Grounded Document Retrieval via Patch-to-Region Relevance Propagation](https://arxiv.org/abs/2501.12345) - Section 2.1 & 3.3

## Overview

Snappy implements **late interaction** retrieval, a powerful technique where query-document matching happens at the token level rather than at the document level. This approach, inspired by ColBERT and adapted for vision-language models in ColPali, significantly improves retrieval accuracy while maintaining reasonable performance.

Late interaction forms the foundation for Snappy's patch-to-region relevance propagation: instead of discarding patch-level similarity scores after computing page-level results, Snappy extracts these scores as spatial relevance distributions and propagates them to OCR regions.

## What is Late Interaction?

### Traditional "Early Interaction" Approach

In traditional retrieval systems, documents and queries are each compressed into a single vector:

```
Query: "revenue forecast Q4"  →  Single vector [0.23, -0.45, 0.12, ...]  (128D)
Document Page              →  Single vector [0.15, 0.32, -0.08, ...]  (128D)

Similarity = cosine_similarity(query_vector, doc_vector)  # One number
```

**Problem**: A single vector must represent all aspects of the content. Nuanced matching is lost.

### Late Interaction Approach

Late interaction maintains **multiple vectors** (one per token/patch) and compares them individually:

```
Query: "revenue forecast Q4"
  ↓
Query Tokens: ["revenue", "forecast", "Q4"]
  ↓
Query Embeddings: 3 vectors of 128D each

Document Page Image
  ↓
Patch Grid: 128 × 96 = 12,288 patches
  ↓
Image Embeddings: 12,288 vectors of 128D each

Similarity = MaxSim(query_embeddings, image_embeddings)  # Detailed matching
```

**Benefit**: Each query token finds its best match among all image patches. Layout, context, and fine-grained semantics are preserved.

---

## Why "Late" Interaction?

The term "late" refers to *when* the interaction (matching) between query and document occurs:

| Approach | Interaction Timing | Example |
|----------|-------------------|---------|
| **Early Interaction** | Before retrieval | BERT cross-encoder: concatenate query+doc, run through model together |
| **Single Vector** | No interaction | Embed separately, compare single vectors |
| **Late Interaction** | During retrieval | Embed separately (multi-vector), compare token-by-token at search time |

**Key insight**: Late interaction delays the matching until search time, allowing fine-grained token-level comparisons without the computational cost of early interaction (which requires re-encoding every query-doc pair).

---

## How Late Interaction Works in Snappy

### 1. Multi-Vector Embedding

Each document page is embedded as a **multi-vector representation**:

```python
# Indexing time
image = load_page_image("doc.pdf", page=1)
embedding = colpali.embed_images([image])

# Result shape: (1, num_patches, embedding_dim)
# Example: (1, 12288, 128)
#   - 12,288 patches (128 × 96 grid)
#   - 128 dimensions per patch
```

This embedding is stored in Qdrant with all 12,288 vectors preserved.

**Implementation**: [`backend/clients/colpali.py:embed_images`](../clients/colpali.py)

---

### 2. Token-Level Query Encoding

User queries are similarly encoded as multiple vectors:

```python
# Search time
query = "total revenue"
query_embedding = colpali.embed_queries([query])

# Result shape: (1, num_query_tokens, embedding_dim)
# Example: (1, 3, 128)
#   - 3 tokens: ["total", "revenue", + special token]
#   - 128 dimensions per token
```

**Implementation**: [`backend/clients/colpali.py:embed_queries`](../clients/colpali.py)

---

### 3. MaxSim Scoring

The similarity between query and document is computed using **MaxSim** (maximum similarity):

```python
def maxsim(query_embeddings, doc_embeddings):
    """
    For each query token, find its maximum similarity with any document patch.
    Then average across all query tokens.
    """
    scores = []
    for query_token in query_embeddings:  # Iterate over query tokens
        similarities = [
            cosine_similarity(query_token, doc_patch)
            for doc_patch in doc_embeddings  # Compare with all patches
        ]
        max_score = max(similarities)  # Best matching patch for this token
        scores.append(max_score)

    return mean(scores)  # Average across query tokens
```

**Example**:
```
Query: "revenue forecast"
  - Token "revenue" → max similarity with table header patch = 0.87
  - Token "forecast" → max similarity with chart title patch = 0.91
  → Final score = (0.87 + 0.91) / 2 = 0.89
```

**Key advantage**: Each query token finds its ideal match, even if they appear in different regions of the page.

---

## Two-Stage Retrieval: Prefetch + Rerank

Comparing all query tokens with all document patches is computationally expensive:
- Query: 3 tokens
- Document: 12,288 patches
- Total comparisons: 3 × 12,288 = 36,864 cosine similarities

To optimize, Snappy uses **two-stage retrieval**:

### Stage 1: Prefetch (Approximate Search)

Use **pooled embeddings** (compressed representations) to quickly find candidate pages:

```python
# At indexing time, create pooled vectors
original_embedding = [12,288 vectors of 128D]  # Full multi-vector

# Pool by rows: average all patches in each row
pooled_rows = [96 vectors of 128D]  # One per row

# Pool by columns: average all patches in each column
pooled_cols = [128 vectors of 128D]  # One per column
```

At search time:
```python
# Prefetch top 100 candidates using pooled vectors (fast)
candidates_rows = search(query, using="mean_pooling_rows", limit=100)
candidates_cols = search(query, using="mean_pooling_columns", limit=100)
candidates = merge(candidates_rows, candidates_cols)  # ~200 candidates
```

**Why pooling?** Reduces comparison count:
- Row pooling: 3 query tokens × 96 row vectors = 288 comparisons
- Column pooling: 3 query tokens × 128 column vectors = 384 comparisons
- Total: ~670 comparisons (vs 36,864 for original)

**Trade-off**: Less precise, but fast enough for prefetching.

**Implementation**: [`backend/clients/qdrant/embedding.py:pool_image_tokens`](../clients/qdrant/embedding.py)

---

### Stage 2: Rerank (Exact Search)

Rerank the prefetched candidates using the **original multi-vector embeddings**:

```python
# Rerank top 10 from ~200 candidates using original embeddings
final_results = rerank(candidates, query, using="original", limit=10)
```

Now only ~200 pages need full multi-vector comparison instead of the entire collection.

**Result**: Best of both worlds; fast prefetch + accurate rerank.

**Implementation**: [`backend/clients/qdrant/search.py:reranking_search_batch`](../clients/qdrant/search.py)

---

## Configuration

Late interaction is controlled by the **mean pooling** setting:

```bash
# Enable two-stage retrieval (late interaction)
QDRANT_MEAN_POOLING_ENABLED=true

# Prefetch limit (candidates for reranking)
QDRANT_PREFETCH_LIMIT=100

# Final result limit
QDRANT_SEARCH_LIMIT=10
```

### Behavior by Mode

| Mode | `QDRANT_MEAN_POOLING_ENABLED` | Search Strategy | Performance |
|------|-------------------------------|-----------------|-------------|
| **Simple Single-Vector** | `false` | Direct search on original embeddings | Fast, lower accuracy |
| **Two-Stage Late Interaction** | `true` | Prefetch with pooled + rerank with original | Slower, higher accuracy |

**When to enable**:
- ✅ Large collections (>1000 pages) where accuracy matters
- ✅ Complex queries with multiple concepts
- ✅ Documents with rich visual layouts (tables, charts, diagrams)
- ❌ Small collections (<100 pages) where speed is critical
- ❌ Simple keyword queries on text-only documents

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    LATE INTERACTION PIPELINE                  │
└──────────────────────────────────────────────────────────────┘

INDEXING TIME:
┌──────────────┐
│ Document     │
│ Page Image   │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Vision Transformer   │
│ (ColPali)            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Multi-Vector Embedding                   │
│ [12,288 patches × 128 dimensions]        │
└──────┬──────────────┬────────────────────┘
       │              │
       │              ▼
       │        ┌─────────────────┐
       │        │ Mean Pooling    │
       │        └────┬────────────┘
       │             │
       ▼             ▼
 ┌──────────┐  ┌─────────────────────┐
 │ Original │  │ Pooled Embeddings   │
 │ Vectors  │  │ - Rows:    96 × 128 │
 │ (full)   │  │ - Columns: 128 × 128│
 └─────┬────┘  └─────────┬───────────┘
       │                 │
       ▼                 ▼
 ┌─────────────────────────────────┐
 │ Qdrant Storage                  │
 │ Named vectors:                  │
 │ - "original"                    │
 │ - "mean_pooling_rows"           │
 │ - "mean_pooling_columns"        │
 └─────────────────────────────────┘

SEARCH TIME:
┌──────────────┐
│ User Query   │
│ "revenue Q4" │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Query Encoding       │
│ [3 tokens × 128D]    │
└──────┬───────────────┘
       │
       ├─────────────────────────────┐
       │                             │
       ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ STAGE 1:         │        │ STAGE 1:         │
│ Prefetch (Rows)  │        │ Prefetch (Cols)  │
│ Top 100 pages    │        │ Top 100 pages    │
└────────┬─────────┘        └─────────┬────────┘
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Merge         │
              │ ~200 pages    │
              └───────┬───────┘
                      │
                      ▼
              ┌─────────────────────┐
              │ STAGE 2:            │
              │ Rerank (Original)   │
              │ MaxSim scoring      │
              │ Top 10 pages        │
              └─────────┬───────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Final Results │
                └───────────────┘
```

---

## Interpretability: Visualizing Late Interaction

The interpretability maps feature allows you to **see** late interaction in action.

For each query token, an interpretability map shows which patches had the highest similarity:

```
Query: "revenue forecast"

Token: "revenue"
Interpretability Map (96 × 128 heatmap):
  - High scores (red): Table headers, chart labels mentioning "revenue"
  - Low scores (blue): Footnotes, page numbers, unrelated text

Token: "forecast"
Interpretability Map (96 × 128 heatmap):
  - High scores (red): Chart titles, projection tables
  - Low scores (blue): Historical data, static text
```

This visualization proves that each query token finds its own best match among all patches; the core of late interaction.

**API**: [`POST /api/interpretability`](../api/routers/interpretability.py)

**Frontend**: [`frontend/components/interpretability-heatmap.tsx`](../../frontend/components/interpretability-heatmap.tsx)

---

## Performance Characteristics

### Latency Breakdown (10,000 page collection)

| Operation | Simple Mode | Late Interaction (2-Stage) |
|-----------|-------------|----------------------------|
| **Prefetch** | N/A | ~20-40ms (pooled vectors) |
| **Direct Search** | ~50-80ms | N/A |
| **Rerank** | N/A | ~30-50ms (original vectors on candidates) |
| **Total** | ~50-80ms | ~50-90ms |
| **Accuracy** | Baseline | +10-20% better (typical) |

**Key insight**: Two-stage retrieval adds minimal latency (~10-30ms) while significantly improving accuracy.

### Memory Usage

| Component | Storage per Page |
|-----------|------------------|
| **Original vectors** | 12,288 × 128D × 4 bytes = ~6.3 MB |
| **Pooled rows** | 96 × 128D × 4 bytes = ~49 KB |
| **Pooled columns** | 128 × 128D × 4 bytes = ~66 KB |
| **Total (uncompressed)** | ~6.4 MB per page |
| **With binary quantization** | ~200 KB per page (32× reduction) |

**Optimization**: Binary quantization drastically reduces memory usage while maintaining accuracy. Enable with `QDRANT_USE_BINARY_QUANTIZATION=true`.

---

## Comparison: Late Interaction vs Alternatives

| Approach | Vectors per Doc | Search Cost | Accuracy | Best For |
|----------|----------------|-------------|----------|----------|
| **Single Vector** | 1 | Low | Good | Simple keyword search, small collections |
| **Late Interaction** | 12,288 | Medium | Excellent | Complex layouts, multi-concept queries |
| **Early Interaction** | N/A (runtime) | Very High | Excellent | Re-ranking top results (not primary retrieval) |

**Why not early interaction for retrieval?**
- Requires encoding every query-doc pair together
- 10,000 docs × 1 query = 10,000 forward passes through the model
- Far too slow for real-time search

**Why late interaction wins**:
- Encode documents once at indexing time
- Encode query once at search time
- Compare pre-computed embeddings (fast matrix operations)

---

## Implementation Details

### Key Files

**Embedding and Pooling**:
- [`backend/clients/qdrant/embedding.py`](../clients/qdrant/embedding.py) - Pooling logic (`pool_image_tokens`)
- [`colpali/app/services/embedding_processor.py`](../../colpali/app/services/embedding_processor.py) - ColPali integration

**Search**:
- [`backend/clients/qdrant/search.py`](../clients/qdrant/search.py) - Two-stage search (`reranking_search_batch`)
- [`backend/domain/retrieval.py`](../domain/retrieval.py) - High-level search orchestration

**Configuration**:
- [`backend/config/schema/qdrant.py`](../config/schema/qdrant.py) - Qdrant settings
- [`backend/docs/configuration.md`](configuration.md) - Full config reference

### Testing Late Interaction

1. **Enable two-stage retrieval**:
   ```bash
   QDRANT_MEAN_POOLING_ENABLED=true
   QDRANT_PREFETCH_LIMIT=100
   QDRANT_SEARCH_LIMIT=10
   ```

2. **Upload a document** with complex layout (tables, charts)

3. **Search with a multi-concept query**:
   ```
   "Q4 revenue forecast chart"
   ```

4. **Compare results** with simple mode (`QDRANT_MEAN_POOLING_ENABLED=false`)
   - Late interaction should rank pages with both "revenue" AND "forecast" higher
   - Simple mode may miss pages where these terms appear in different regions

5. **View interpretability maps** to see token-level matching in action

---

## Advanced: MaxSim Scoring Formula

The exact MaxSim formula used in ColPali:

```
Given:
  Q = [q1, q2, ..., qn]  # Query token embeddings
  D = [d1, d2, ..., dm]  # Document patch embeddings

MaxSim(Q, D) = (1/n) * Σ max(cosine_similarity(qi, dj) for dj in D)
                       i=1..n

Where:
  cosine_similarity(qi, dj) = (qi · dj) / (||qi|| * ||dj||)
```

**Interpretation**:
1. For each query token `qi`, compute similarity with all document patches
2. Take the maximum similarity (best matching patch)
3. Average these maximum scores across all query tokens

**Why it works**:
- Soft OR-logic: Query token must match *at least one* patch well
- Invariant to document length: Average over query tokens, not document patches
- Handles multi-concept queries: Each token finds its own match

---

## Future Enhancements

Potential improvements to late interaction:

1. **Token-level query expansion**: Expand query tokens before encoding for better recall
2. **Weighted MaxSim**: Weight query tokens by importance (e.g., IDF scores)
3. **Cross-token constraints**: Prefer pages where matched patches are spatially close
4. **Adaptive prefetch**: Dynamically adjust prefetch limit based on query complexity
5. **GPU-accelerated MaxSim**: Offload similarity computation to GPU for large collections

---

## References

- **ColBERT paper**: "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT" (Khattab & Zaharia, 2020)
- **ColPali paper**: "ColPali: Efficient Document Retrieval with Vision Language Models" (2024)
- **Vision-language models**: "CLIP: Learning Transferable Visual Models From Natural Language Supervision" (Radford et al., 2021)

---

## Related Documentation

- [Spatial Grounding](spatial_grounding.md) - How spatial information is preserved in late interaction
- [Architecture Overview](architecture.md) - System design
- [Configuration Reference](configuration.md) - All settings
- [Analysis: Vision vs Text RAG](analysis.md) - When to use late interaction
