# Snappy System Analysis – Vision vs. Text RAG 🔬

This note explains how Snappy approaches document retrieval and how it compares with text-only RAG systems.

---

## Overview

**What sets Snappy apart**
- 👁️ Vision-first: works with page images instead of extracted text.
- 🧱 Multivector embeddings: stores patch-level tokens plus pooled variants for each page.
- 🎯 Two-stage retrieval: pooled vectors prefetch, original vectors rerank.
- ⚖️ Trade-offs: excels on scans, forms, charts, and layout-heavy docs; pure text corpora are usually better served by classic RAG.

---

## Backend Architecture

- **API server** – `backend/main.py` boots `api.app.create_app()` with routers for `meta`, `retrieval`, `indexing`, `maintenance`, `config`, `ocr`, and `duckdb`.
- **Vector storage** (`clients/qdrant/`)
  - `collection.py` – manages multivector schemas (`original`, `mean_pooling_rows`, `mean_pooling_columns`)
  - `search.py` – two-stage search (prefetch + rerank)
  - `embedding.py` – handles ColPali calls and pooling
  - `indexing/qdrant_indexer.py` – Qdrant-specific storage built on the shared ingestion pipeline
- **Pipeline package** (`domain/pipeline/`) – reusable `DocumentIndexer`, batch processor, storage, progress tracking, and cancellation service (used by Qdrant integration)
- **ColPali client** (`clients/colpali.py`) – talks to the embedding service for images, patches, and queries.
- **MinIO client** (`clients/minio.py`) – uploads images with auto-sized worker pools and retries.
- **DeepSeek OCR client** (`clients/ocr/`) – optional OCR client with UUID-based storage and batch/background processing.
- **DuckDB client** (`clients/duckdb.py`) – optional analytics database for document deduplication and OCR metadata storage.
- **Chat interface** (`frontend/app/api/chat/route.ts`) – streams OpenAI responses with page citations.

---

## Indexing Pipeline

1. **Upload** – `POST /index` schedules a background job.
2. **Deduplication** – When DuckDB is enabled, checks for duplicate documents using content-based fingerprinting.
3. **PDF → images** – `api/utils.py::convert_pdf_paths_to_images` rasterises each page via `pdf2image`.
4. **Batch processing** – `DocumentIndexer` in `domain/pipeline/document_indexer.py`
   - Splits pages into batches (`BATCH_SIZE`)
   - Embeds via `ColPaliClient` (original + pooled vectors)
   - Stores images in MinIO with hierarchical structure: `{filename}/{page_number}/`
   - Upserts vectors into Qdrant via `clients/qdrant/indexing/qdrant_indexer.py`
   - Runs optional OCR callbacks when `clients/ocr` instance is supplied with UUID-based result naming
   - Stores document metadata in DuckDB when enabled
5. **Pipeline mode** – The system automatically uses concurrent pipeline processing where embedding, storage, OCR, and upserts overlap using dual thread pools sized from `config.get_pipeline_max_concurrency()`.
6. **Progress** – `/progress/stream/{job_id}` streams status updates over SSE.
7. **Cancellation** – `/index/cancel/{job_id}` triggers comprehensive cleanup across all services with optional service restart.

Collection schemas come from the model dimension reported by `/info`. Images use UUID-based naming within filename-organized folders. Pipeline concurrency is automatically optimized based on CPU cores and batch size.

---

## Retrieval Pipeline

1. **Query embedding** – `EmbeddingProcessor.batch_embed_query` calls `/embed/queries`.
2. **Two-stage search** – `SearchManager._reranking_search_batch`
   - Prefetch against pooled vectors (mean pooling is always enabled)
   - Final rerank with original vectors (`with_payload=True`)
3. **Response assembly** – `SearchManager.search_with_metadata` returns metadata and image URLs; `/search` formats the API response.
4. **Multimodal answer** – The frontend chat route streams OpenAI responses and emits `kb.images` events for the UI gallery.

---

## Multivector Design

- Patch-aware scoring uses `MAX_SIM` across tokens to mirror ColPali search behaviour.
- Row/column pooling preserves coarse layout information and often improves recall on complex pages.

---

## Vision RAG vs. Text RAG

| Aspect | Snappy (Vision) | Traditional Text RAG |
|--------|-----------------|----------------------|
| **Modality** | Works on page images; no OCR required. Handles scans, handwriting, diagrams. | Requires text extraction; struggles on low-quality scans or heavy layout. |
| **Representation** | Multivectors per page (patch tokens + pooled variants). | Single vector per text chunk, often with overlapping windows. |
| **Indexing cost** | Higher: rasterisation, image embeddings, object storage. | Lower: text extraction and embeddings only. |
| **Retrieval quality** | Strong on layout awareness and visual context. | Strong on semantic text understanding when OCR is clean. |
| **Latency** | Multivector search + multimodal prompts cost more. | Typically faster lookups and lighter prompts. |
| **Context delivery** | Sends images to multimodal LLM for grounded answers. | Sends text chunks; grounding depends on OCR fidelity. |
| **Failure modes** | Missing fine text, higher prompt costs. | OCR errors, chunk boundary issues, loss of layout. |
| **Best for** | Scanned PDFs, forms, tables, diagrams, handwritten notes. | Plain text corpora, code, documents with reliable OCR. |

---

## Possible Enhancements

- Hybrid vision/text pipeline combining OCR when it helps.
- Cross-encoder or LLM-based reranking for even tighter precision.
- Region-of-interest citations (bounding boxes and highlights).
- Signed URLs and authentication for production deployments.
- Telemetry, evaluation harnesses, and richer observability.
- Fine-tuned HNSW parameters and quantisation layouts for large collections.

---

## Implementation Pointers

- Indexing paths: `api/utils.py::convert_pdf_paths_to_images`, `DocumentIndexer.index_documents` in `services/pipeline/document_indexer.py`.
- Collection schema management: `CollectionManager.create_collection_if_not_exists` in `services/qdrant/collection.py`.
- Pooling logic: `EmbeddingProcessor._pool_image_tokens` in `services/qdrant/embedding.py`.
- Two-stage query: `SearchManager._reranking_search_batch` in `services/qdrant/search.py`.
- MinIO URLs: `MinioClient._get_image_url()` and `_extract_object_name_from_url()`.
- Chat streaming: `frontend/app/api/chat/route.ts` (SSE) and `frontend/lib/api/chat.ts`.

---

## Notes from the Code

- The ColPali API is expected to return embeddings with token boundaries; `ColPaliClient.embed_images` already matches that contract.
- The frontend controls the OpenAI model via `OPENAI_MODEL` (`frontend/.env.local`). The backend stays focused on retrieval and system duties.

