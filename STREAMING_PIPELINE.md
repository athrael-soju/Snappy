# Streaming Pipeline Architecture

## 📊 Visual Timeline Comparison

### Current Batch Pipeline (100-page PDF)
```
Time →
0s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ┌─────────────────────────────────────────────────────────────┐
   │ Rasterize ALL pages (1-100)                         60s     │ ← BLOCKING
   └─────────────────────────────────────────────────────────────┘

60s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ┌──────────────┐
    │ Batch 1      │ Embed → Store → OCR → Upsert (12s)
    └──────────────┘

72s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                   ┌──────────────┐
                   │ Batch 2      │ Embed → Store → OCR → Upsert (12s)
                   └──────────────┘

... (continues for 25 batches)

360s (6 minutes) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                             Done ✓

⚠️ Problems:
- First results: 72 seconds (user waits!)
- GPU idle for 60 seconds
- CPU idle during embedding
- Total time: 360 seconds
```

### New Streaming Pipeline (100-page PDF)
```
Time →
0s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Rasterize 1-4   ┐
                   │ → [Queue] → Embed 1-4        ┐
2s ━━━━━━━━━━━━━━━┘            Store 1-4  ┐      │
   Rasterize 5-8   ┐            OCR 1-4    │      │ → Upsert 1-4 ┐
                   │                        │      │              │
4s ━━━━━━━━━━━━━━━┘          → Embed 5-8   │      │              │
   Rasterize 9-12  ┐            Store 5-8  │      │              │
                   │            OCR 5-8    ┘      │              │
6s ━━━━━━━━━━━━━━━┘                              ┘              │
   Rasterize 13-16 ┐          → Embed 9-12                       │
                   │            Store 9-12                       │
8s ━━━━━━━━━━━━━━━┘            OCR 9-12     → Upsert 5-8        │
   ...                                                           │
                                                                 ┘
10s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ✅ FIRST RESULTS VISIBLE (pages 1-4 searchable!)

... (pipeline continues streaming)

60s ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                             Done ✓

✅ Benefits:
- First results: 10 seconds (7x faster!)
- All resources busy (GPU, CPU, I/O)
- Progressive feedback
- Total time: 60 seconds (6x faster!)
```

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PDF Document                                 │
│                      document_id: abc-123                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────────┐
        │  STAGE 1: PDF Rasterizer (Producer)           │
        │  Thread: Main thread                           │
        │  ┌──────────────────────────────────────────┐ │
        │  │ for page_batch in 1..100 (chunks of 4):  │ │
        │  │   convert_from_path()                     │ │
        │  │   rasterize_queue.put(batch)              │ │
        │  │   # Continues immediately!                │ │
        │  └──────────────────────────────────────────┘ │
        └────────────────┬───────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │   rasterize_queue            │ ← Bounded (max 8 batches)
          │   [batch1, batch2, batch3]   │   Provides backpressure
          └─────┬────────────────┬───────┘
                │                │
        ┌───────┘                └───────┬────────────────────┐
        │                                │                    │
        ▼                                ▼                    ▼
┌───────────────────┐      ┌──────────────────────┐  ┌──────────────────┐
│ STAGE 2a: Embed   │      │ STAGE 2b: Storage    │  │ STAGE 2c: OCR    │
│ Thread: embed-1   │      │ Thread: storage-1    │  │ Thread: ocr-1    │
│ ┌───────────────┐ │      │ ┌──────────────────┐ │  │ ┌──────────────┐ │
│ │ batch=queue.get│ │      │ │ batch=queue.get  │ │  │ │batch=queue.get│ │
│ │ embed(batch)  │ │      │ │ minio.store()    │ │  │ │ocr.process()  │ │
│ │ queue2.put()  │ │      │ │ (fail-fast)      │ │  │ │(fail-fast)    │ │
│ └───────────────┘ │      │ └──────────────────┘ │  │ └──────────────┘ │
└─────────┬─────────┘      └──────────────────────┘  └────────────────┘
          │                   (Parallel)                 (Parallel)
          ▼
┌─────────────────┐
│ embedding_queue │
│ [emb1, emb2]    │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Upsert Stage (only waits for embeddings)                │
│  Thread: upsert-1                                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ embedded_batch = queue.get()  # Only waits for embeddings    │ │
│  │ urls = generate_urls(doc_id, page_ids)  # Dynamic generation │ │
│  │ ocr_urls = generate_ocr_urls(doc_id, page_nums)  # Dynamic   │ │
│  │ points = build_points(embeddings, urls, ocr_urls)            │ │
│  │ qdrant.upsert(points)                                        │ │
│  │ update_progress()                                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Example

**Single Batch Journey** (document_id: `doc-123`, batch_id: `0`, pages 1-4):

```
T=0s:  Rasterizer produces PageBatch
       → {doc_id: "doc-123", batch_id: 0, images: [img1, img2, img3, img4]}
       → Pushes to rasterize_queue

T=0s:  THREE consumers pull from rasterize_queue simultaneously:

       ┌─ Embed Stage:   Gets batch → embeds → produces EmbeddedBatch
       │                 → {doc_id: "doc-123", batch_id: 0, embeddings: [...]}
       │                 → Pushes to embedding_queue
       │
       ├─ Storage Stage: Gets batch → stores in MinIO (fails-fast on error)
       │                 → Uploads images to minio/doc-123/1/image/uuid1.jpg, etc.
       │
       └─ OCR Stage:     Gets batch → processes OCR → stores in MinIO (fails-fast on error)
                         → Stores OCR JSON at minio/doc-123/1/ocr.json, etc.

T=5s:  Embedding complete

T=5s:  Upsert Stage:    Gets EmbeddedBatch from embedding_queue
                        → Generates URLs dynamically from metadata
                        → image_urls = ["http://minio/doc-123/1/image/uuid1.jpg", ...]
                        → ocr_urls = ["http://minio/doc-123/1/ocr.json", ...]
                        → Builds Qdrant points with embeddings and URLs
                        → Upserts to Qdrant
                        → Updates progress

T=6s:  ✅ Pages 1-4 are searchable!

Note: All stages run in parallel. Any failure stops the pipeline to ensure data consistency.
```

**Key Insight**: All stages run **independently in parallel** with dedicated queues - URLs are generated dynamically!

## 💻 Usage Example

```python
from domain.pipeline.streaming_pipeline import StreamingPipeline
from api.dependencies import (
    get_colpali_client,
    get_minio_service,
    get_ocr_service,
    get_qdrant_service,
)
from clients.qdrant.indexing.points import PointFactory

# Initialize services
embedding_processor = get_qdrant_service().embedding_processor
image_store = get_qdrant_service()._pipeline._batch_processor.image_store
ocr_service = get_ocr_service()
point_factory = PointFactory()
qdrant_service = get_qdrant_service().service
collection_name = config.QDRANT_COLLECTION_NAME

# Create streaming pipeline
pipeline = StreamingPipeline(
    embedding_processor=embedding_processor,
    image_store=image_store,
    ocr_service=ocr_service,
    point_factory=point_factory,
    qdrant_service=qdrant_service,
    collection_name=collection_name,
    batch_size=4,
    max_queue_size=8,  # Backpressure: max 8 batches in queue
)

# Start consumer threads
pipeline.start()

# Process PDF (rasterizer feeds the pipeline)
total_pages = pipeline.process_pdf(
    pdf_path="/tmp/document.pdf",
    filename="document.pdf",
    progress_callback=lambda current, total: print(f"{current}/{total}"),
    cancellation_check=lambda: check_if_cancelled(),
)

# Wait for pipeline to finish processing
pipeline.wait_for_completion()

# Clean up
pipeline.stop()

print(f"Processed {total_pages} pages")
```

## ⚡ Performance Characteristics

### Throughput Analysis

**Current Batch Pipeline**:
- Batch processing time: 12 seconds/batch
- Throughput: 4 pages / 12 seconds = **0.33 pages/second**
- 100 pages: ~6 minutes
- 1000 pages: ~60 minutes

**Streaming Pipeline** (4 concurrent stages):
- First batch: 10 seconds (startup latency)
- Steady state: 4 pages / 2 seconds = **2 pages/second** (6x faster!)
- 100 pages: ~60 seconds (includes 10s startup)
- 1000 pages: ~510 seconds (~8.5 minutes, 7x faster!)

### Resource Utilization

**Current Pipeline**:
```
CPU:    █████_____  (50% - idle during GPU ops)
GPU:    _____█████  (50% - idle during PDF conversion)
I/O:    ___███____  (30% - sporadic)
Memory: ███_______  (30% - spikes during batch load)
```

**Streaming Pipeline**:
```
CPU:    ██████████  (95% - always rasterizing)
GPU:    ██████████  (95% - always embedding/OCR)
I/O:    ██████████  (95% - continuous uploads)
Memory: ██████____  (60% - bounded queues prevent overflow)
```

## 🎛️ Tuning Parameters

### Queue Size (Backpressure Control)
```python
max_queue_size=8  # Default

# Small documents (<50 pages): 4
# Medium documents (50-200 pages): 8
# Large documents (200+ pages): 16
# Very large (1000+ pages): 32

# Trade-off: Larger queues = more memory, more parallelism
```

### Batch Size
```python
batch_size=4  # Default

# High-memory GPUs: 8
# Low-memory GPUs: 2
# CPU-only: 1

# Trade-off: Larger batches = better GPU utilization, more memory
```

### Worker Threads
```python
# PDF rasterization
worker_threads = os.cpu_count()  # Default: all cores

# OCR parallelism per batch
DEEPSEEK_OCR_MAX_WORKERS = 2  # Reduced to prevent GPU contention

# MinIO upload parallelism
MINIO_WORKERS = 8  # Moderate to prevent connection exhaustion
```

## 🐛 Error Handling

### Stage Failures

**Embedding Stage Fails**:
- Pipeline stops (critical - can't proceed without embeddings)
- Already-processed batches remain in Qdrant

**Storage Stage Fails**:
- Pipeline stops (critical - cannot generate valid image URLs)
- Prevents creation of Qdrant points with broken image references

**OCR Stage Fails**:
- If OCR is enabled: Pipeline stops (critical - OCR was explicitly requested)
- If OCR is disabled: Stage doesn't run at all
- No silent fallbacks - failures are explicit

**Upsert Stage Fails**:
- Pipeline stops (critical - embeddings must be stored)
- Can retry from scratch (no caching needed)

### Cancellation

```python
def cancellation_check():
    if progress_manager.is_cancelled(job_id):
        raise CancellationError("Job cancelled")

pipeline.process_pdf(
    pdf_path=path,
    filename=filename,
    cancellation_check=cancellation_check,  # Check before each batch
)
```

When cancelled:
- Rasterizer stops immediately
- In-flight batches complete
- Queues drain gracefully
- Partial results remain in Qdrant (by design)

## 📈 Monitoring

### Queue Depth
```python
# Add to progress callback
progress_callback(
    current=pages_processed,
    message={
        "rasterize_queue": pipeline.rasterize_queue.qsize(),
        "embedding_queue": pipeline.embedding_queue.qsize(),
    }
)
```

### Stage Timing
```python
# All stages use @log_execution_time decorator
# Logs appear as:
# [INFO] Embedding batch 5 completed in 4.2s
# [INFO] Storage batch 5 completed in 1.1s
# [INFO] OCR batch 5 completed in 6.8s
# [INFO] Upsert batch 5 completed in 0.9s
```

### Bottleneck Detection
```
If rasterize_queue is always empty:
  → Rasterization is bottleneck (increase worker_threads)

If rasterize_queue is always full:
  → Downstream stages are bottleneck (reduce batch_size or add workers)

If embedding_queue is always full:
  → Upsert is bottleneck (increase buffer_size for batched upserts)
```

## 🔄 Migration Path

### Phase 1: Testing (1-2 days)
1. Deploy streaming pipeline alongside existing pipeline
2. Test with small documents (10-50 pages)
3. Compare results with existing pipeline
4. Validate: embeddings, URLs, OCR all correct

### Phase 2: Gradual Rollout (3-5 days)
1. Add feature flag: `USE_STREAMING_PIPELINE=true/false`
2. Route 10% of traffic to streaming pipeline
3. Monitor errors, performance
4. Gradually increase to 100%

### Phase 3: Cleanup (1 day)
1. Remove old batch pipeline code
2. Remove feature flag
3. Update documentation

## 🚀 Next Optimizations

After streaming pipeline is stable:

1. **Async HTTP Clients**: Replace `requests` with `httpx.AsyncClient`
2. **Process Pool for PDF**: Offload rasterization to separate processes
3. **Distributed Queue**: Replace in-memory queues with Redis for multi-instance support
4. **Adaptive Batch Sizing**: Dynamically adjust based on GPU memory usage
5. **Result Streaming**: WebSocket updates to frontend as pages complete
