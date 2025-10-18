# Snappy System Analysis - Vision vs. Text RAG 🔬

Let's dive deep into what makes Snappy tick and how it stacks up against traditional text-based RAG systems!

## The Big Picture 🖼️

**What Makes Snappy Different**:
- 👁️ **Vision-First**: Retrieves actual page images, not extracted text
- 🧱 **Multivector Magic**: Stores patch-level embeddings (original + pooled variants) per page
- 🎯 **Smart Retrieval**: Two-stage Qdrant search with prefetch + reranking, then feeds top-k images to multimodal LLM
- ⚖️ **Trade-offs**: Perfect for scanned PDFs, forms, charts, and layout-heavy docs. Not the best for pure text corpora (no OCR/chunking)

---

## Snappy's Architecture Breakdown 🏛️

**The Backend** 🚀:
- **API Server**: `main.py` boots `api.app.create_app()` with modular routers (`meta`, `retrieval`, `indexing`, `maintenance`)

**Vector Storage** (`services/qdrant/`):
- `service.py` – Main `QdrantService` orchestrator
- `collection.py` – Manages multivector collections: `original`, `mean_pooling_rows`, `mean_pooling_columns` with `MAX_SIM` comparator
- `search.py` – Two-stage search magic: prefetch on pooled vectors, final ranking on originals
- `embedding.py` – Parallel embedding and pooling wizardry
- `indexing.py` – Pipelined document indexing with concurrent batching

**The Vision Brain** (`services/colpali.py`):
- Connects to external ColPali API for embeddings, patches, and model info

**Image Storage** (`services/minio.py`):
- Smart batch uploads with retries, auto-sized workers, and public-read policy

**Chat Interface** (`frontend/app/api/chat/route.ts`):
- Streams OpenAI responses via SSE with retrieved images as data URLs or links

---

## Indexing Pipeline (What Happens on Upload)

- __PDF to images__: The API route uses `api/utils.py::convert_pdf_paths_to_images(...)` (via the `/index` endpoint). Each page becomes one PIL image with payload metadata: `filename`, `pdf_page_index`, `page_width_px`, `page_height_px`, etc.
- __Pipelined processing__: `DocumentIndexer._index_documents_pipelined(...)` (in `services/qdrant/indexing.py`, when `ENABLE_PIPELINE_INDEXING=True`)
  - Uses dual thread pools: one for batch processing (embedding + MinIO upload), one for Qdrant upserts
  - Concurrency is derived from hardware via `config.get_pipeline_max_concurrency()`
  - Allows embedding, MinIO uploads, and Qdrant upserts to overlap for maximum throughput
- __Embeddings__: `EmbeddingProcessor` (in `services/qdrant/embedding.py`)
  - Calls `ColPaliService.embed_images(...)` to get image patch embeddings (image encoding parallelized for high-CPU systems)
  - Calls `ColPaliService.get_patches(...)` to obtain the patch grid (`n_patches_x`, `n_patches_y`)
  - Mean-pools the image patch tokens into two variants: by rows and by columns, preserving prefix/postfix tokens via parallelized pooling operations
  - Produces three multivectors per page: `original`, `mean_pooling_rows`, `mean_pooling_columns`
- __Image persistence__: `MinioService.store_images_batch(...)` uploads images concurrently with an internal thread pool (`MINIO_WORKERS` threads). Worker counts and retry attempts are auto-sized based on CPU cores and pipeline concurrency.
- __Upsert to Qdrant__: Non-blocking upserts submitted to separate executor, allowing next batch to start embedding immediately. The `/index` route starts this as a background job and you can poll `/progress/{job_id}` for status.

Notes:
- Collection schema is created on startup in `QdrantService._create_collection_if_not_exists()` using model dimension from `/info`.
- Images are stored under an S3-like path (`images/<uuid>.<ext>`), publicly readable by default.
- Sequential mode (`ENABLE_PIPELINE_INDEXING=False`) processes one batch fully before starting the next.

---

## Retrieval Pipeline (What Happens on Query)

- __Query embedding__: `EmbeddingProcessor.batch_embed_query(...)` (in `services/qdrant/embedding.py`) calls `/embed/queries` and returns per-token embeddings
- __Two-stage search__: `SearchManager._reranking_search_batch(...)` (in `services/qdrant/search.py`, optionally MUVERA-first stage when enabled)
  - Prefetch against `mean_pooling_columns` and `mean_pooling_rows` with `prefetch_limit`
  - Final rank against `original` with `search_limit`, `with_payload=True`
- __Result assembly__:
  - `SearchManager.search_with_metadata(...)` returns metadata with image URLs without fetching actual images (optimized for latency)
  - The API `/search` route (`api/routers/retrieval.py`) formats and returns structured results with URLs
- __Multimodal answer__:
  - The frontend chat API route (`frontend/app/api/chat/route.ts`) sends the user text and retrieved images to OpenAI's Responses API and streams tokens back to the UI via SSE

---

## Multivector Design and Why It Matters

- __Patch-aware__: Image embedding returns patch-level tokens. Retrieval uses `MAX_SIM` across tokens to mimic ColPali-style maximum patch similarity.
- __Row/Column pooling__: `mean_pooling_rows` and `mean_pooling_columns` preserve coarse spatial structure, often improving recall on layout-heavy pages.
- __Two-stage retrieval__: Prefetch with pooled vectors broadens candidate coverage; final scoring on `original` improves precision.

---

## The Showdown: Snappy vs. Traditional Text RAG 🥊

**Data Modality** 🖼️🆚️📝:
- **Snappy (Vision RAG)**: Works with actual page images; no OCR needed! Handles scans, stamps, tables, and charts like a champ
- **Traditional RAG**: Relies on extracted text chunks. Struggles with graphics-heavy or poorly scanned content

**Representation** 🧱:
- **Snappy**: Multivectors per page (patch tokens + pooled variants), stored in Qdrant with MAX_SIM scoring
- **Traditional RAG**: Single vector per text chunk (512-1k tokens), often with overlapping chunks for context

**Indexing Cost** 💰:
- **Snappy**: PDF rasterization + image embedding + S3 storage = higher per-page cost, larger payloads
- **Traditional RAG**: Text extraction + embedding = cheaper per token, smaller storage footprint

**Retrieval Quality** 🎯:
- **Snappy**: Excels at layout understanding, handwriting, scans, and visual elements. Perfect when OCR fails!
- **Traditional RAG**: Dominates on clean text corpora with semantic understanding of language

**Latency** ⏱️:
- **Snappy**: Text embedding is fast, but multivector ranking + image loading + large multimodal prompts add overhead
- **Traditional RAG**: Lean vector lookups + compact text contexts = speedy responses

**Context Assembly** 📝:
- **Snappy**: Sends actual images to multimodal LLM; answers grounded in visual proof!
- **Traditional RAG**: Concatenates text chunks; answers based on extracted text

- __Reranking__
  - Vision RAG: multivector `prefetch` + final `using="original"` scoring; MAX_SIM emphasizes best-matching patch.
  - Traditional RAG: often uses cross-encoder or LLM re-ranking on top of ANN results.

**Storage Requirements** 🗄️:
- **Snappy**: MinIO (images) + Qdrant (multivectors), public-read by default (configurable)
- **Traditional RAG**: Vector DB only (optional blob storage for source docs)

- __Failure modes__
  - Vision RAG: if the image encoder misses tiny text or fine semantics, answers may be shallow; sending many images to LLM can be costly.
  - Traditional RAG: OCR errors, chunk boundary issues, and loss of layout can hurt grounding and factuality.

- __Cost profile__
  - Vision RAG: higher storage (images + multivectors) and prompt costs (image inputs); good ROI when OCR is unreliable or visuals dominate.
  - Traditional RAG: lower storage and prompt costs; ideal when content is mostly text and extractable.

**When to Choose What** 🤔:
- **Choose Snappy**: Scanned PDFs, invoices, forms, heavy tables/figures, diagrams, handwritten notes
- **Choose Traditional RAG**: Clean text corpora, codebases, documentation with reliable text extraction

---

## Future Enhancements - Making Snappy Even Snappier! 🚀

**Hybrid Power** 🔋: Add text extraction + chunking alongside vision for best-of-both-worlds retrieval

**Smarter Reranking** 🧠: Deploy cross-encoders or LLM judges for ultimate precision

**Precise Citations** 🎯: Add bounding boxes and highlight specific regions in the gallery

**Security & Privacy** 🔒: Switch to signed URLs, add authentication layers

**Observability** 📈: Full query logging, latency metrics, evaluation harnesses, and benchmarks

**Performance Tuning** ⚙️: Fine-tune HNSW configs, quantization per field, prefetch limits for optimal speed/recall balance

---

## Implementation Pointers (for this repo)

- __Indexing paths__: `api/utils.py::convert_pdf_paths_to_images()`, `DocumentIndexer.index_documents()` (in `services/qdrant/indexing.py`)
- __Collection schema__: `CollectionManager.create_collection_if_not_exists()` (in `services/qdrant/collection.py`)
- __Pooling logic__: `EmbeddingProcessor._pool_image_tokens()` (in `services/qdrant/embedding.py`)
- __Two-stage query__: `SearchManager._reranking_search_batch()` (in `services/qdrant/search.py`)
- __MinIO URLs__: `MinioService._get_image_url()` and `_extract_object_name_from_url()`
- __Chat streaming__: `frontend/app/api/chat/route.ts` (SSE) and `frontend/lib/api/chat.ts` (helpers for request and stream parsing)

---

## Caveats Noted from Code

 - The ColPali image embedding API is expected to return per-image embeddings with token boundaries, which are processed by `EmbeddingProcessor` in `services/qdrant/embedding.py`. The current implementation in `ColPaliService.embed_images(...)` returns embeddings in the expected format.
 - The default OpenAI model for chat is configured on the frontend via `OPENAI_MODEL` (default `gpt-5-nano`) in `frontend/.env.local`. The backend does not manage chat or OpenAI client configuration.
