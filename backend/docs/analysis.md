# Vision RAG Template: System Analysis and Comparison to Traditional RAG

This document analyzes the current system implemented in this repository and compares it to a traditional text-centric RAG (Retrieval-Augmented Generation) approach.

## Summary

- __Modality__: This template is a vision-first RAG at page level, retrieving page images from PDFs and using a multimodal LLM for answers.
- __Representation__: It stores multivector embeddings per page (original + pooled variants) derived from image patch tokens.
- __Retrieval__: Two-stage Qdrant retrieval using multivector prefetch and final ranking on the original vectors, then sending top-k images to an LLM for multimodal reasoning.
- __Tradeoffs__: Excels on scanned PDFs, forms, charts, and layout-heavy docs. Lacks OCR/text chunking; pure text RAG can be cheaper and better for long-form textual corpora.

---

## Current System Overview

- __API server__: `main.py` boots `api.app.create_app()` which includes routers: `meta`, `retrieval`, `indexing`, `maintenance`.
- __Storage and retrieval__: `clients/qdrant.py`
  - Qdrant multivector collection with fields: `original`, `mean_pooling_rows`, `mean_pooling_columns` and comparator `MAX_SIM`.
  - Two-stage search via `query_batch_points` with `prefetch` on pooled vectors and final ranking `using="original"`.
  - Images stored/fetched via `MinioService`.
- __Embeddings__: `clients/colpali.py`
  - Talks to an external ColPali Embedding API: `/health`, `/info` (to get dim), `/patches`, `/embed/queries`, `/embed/images`.
- __Image storage__: `clients/minio.py`
  - Batch uploads with retries and public-read policy. URLs derived from `MINIO_URL` and bucket.
- __Frontend Chat__: `frontend/app/api/chat/route.ts`
  - Next.js route calls OpenAI Responses API and streams Server-Sent Events (SSE) to the browser. It sends user text plus retrieved image URLs or data URLs.

---

## Indexing Pipeline (What Happens on Upload)

- __PDF to images__: The API route uses `api/utils.py::convert_pdf_paths_to_images(...)` (via the `/index` endpoint). Each page becomes one PIL image with payload metadata: `filename`, `pdf_page_index`, `page_width_px`, `page_height_px`, etc.
- __Embeddings__: `QdrantService._embed_and_mean_pool_batch(...)`
  - Calls `ColPaliClient.embed_images(...)` to get image patch embeddings.
  - Calls `ColPaliClient.get_patches(...)` to obtain the patch grid (`n_patches_x`, `n_patches_y`).
  - Mean-pools the image patch tokens into two variants: by rows and by columns, preserving prefix/postfix tokens: `QdrantService._pool_image_tokens(...)`.
  - Produces three multivectors per page: `original`, `mean_pooling_rows`, `mean_pooling_columns`.
- __Image persistence__: `MinioService.store_images_batch(...)` uploads images and returns public URLs.
- __Upsert to Qdrant__: `QdrantService.index_documents(...)` calls `client.upload_collection(...)` with vectors and rich payload including `image_url` and page metadata.

Notes:
- Collection schema is created on startup in `QdrantService._create_collection_if_not_exists()` using model dimension from `/info`.
- Images are stored under an S3-like path (`images/<uuid>.<ext>`), publicly readable by default.

---

## Retrieval Pipeline (What Happens on Query)

- __Query embedding__: `QdrantService._batch_embed_query(...)` calls `/embed/queries` and returns per-token embeddings.
- __Two-stage search__: `QdrantService._reranking_search_batch(...)`
  - Prefetch against `mean_pooling_columns` and `mean_pooling_rows` with `prefetch_limit`.
  - Final rank against `original` with `search_limit`, `with_payload=True`.
- __Result assembly__:
  - `search_with_metadata(...)` fetches images back from MinIO by `image_url` and returns `[{"image": PIL.Image, 'payload': {...}}]`.
  - The API `/search` route (`api/routers/retrieval.py`) formats and returns structured results.
- __Multimodal answer__:
  - The frontend chat API route (`frontend/app/api/chat/route.ts`) sends the user text and retrieved images to OpenAI's Responses API and streams tokens back to the UI via SSE.

---

## Multivector Design and Why It Matters

- __Patch-aware__: Image embedding returns patch-level tokens. Retrieval uses `MAX_SIM` across tokens to mimic ColPali-style maximum patch similarity.
- __Row/Column pooling__: `mean_pooling_rows` and `mean_pooling_columns` preserve coarse spatial structure, often improving recall on layout-heavy pages.
- __Two-stage retrieval__: Prefetch with pooled vectors broadens candidate coverage; final scoring on `original` improves precision.

---

## Comparison: Vision RAG Template vs Traditional Text RAG

- __Data modality__
  - Vision RAG: page images; no OCR required; resilient to scans, stamps, tables, charts.
  - Traditional RAG: text chunks from OCR or native text; struggles with graphics-only content unless OCR/structure extraction is robust.

- __Representation__
  - Vision RAG: multivectors per page (patch tokens + pooled variants) in Qdrant; MAX_SIM over tokens.
  - Traditional RAG: one vector per chunk (e.g., 512–1k tokens) from a text encoder; sometimes multiple overlapping chunks.

- __Indexing cost__
  - Vision RAG: PDF rasterization + image embedding + S3 storage; higher per-page cost; larger vector payloads (multivectors).
  - Traditional RAG: OCR (when needed) + text embedding; typically cheaper per token and smaller vector storage.

- __Retrieval quality__
  - Vision RAG: strong on layout, handwriting, scans, and visual cues; robust when OCR is poor or absent.
  - Traditional RAG: strong on long-form textual content; benefits from dense chunking and semantic text encoders.

- __Latency__
  - Vision RAG: query requires only text embedding but ranking uses heavy multivectors; image download adds I/O; sending images to LLM increases prompt size.
  - Traditional RAG: lean vector lookup and small textual contexts; faster prompts to LLM.

- __Context assembly__
  - Vision RAG: sends images directly to a multimodal LLM; answers grounded in visual evidence.
  - Traditional RAG: concatenates top-k text chunks; answers grounded in extracted text spans.

- __Reranking__
  - Vision RAG: multivector `prefetch` + final `using="original"` scoring; MAX_SIM emphasizes best-matching patch.
  - Traditional RAG: often uses cross-encoder or LLM re-ranking on top of ANN results.

- __Storage__
  - Vision RAG: MinIO for images + Qdrant multivectors; public-read by default (configurable).
  - Traditional RAG: vector DB only; optional blob storage for originals.

- __Failure modes__
  - Vision RAG: if the image encoder misses tiny text or fine semantics, answers may be shallow; sending many images to LLM can be costly.
  - Traditional RAG: OCR errors, chunk boundary issues, and loss of layout can hurt grounding and factuality.

- __Cost profile__
  - Vision RAG: higher storage (images + multivectors) and prompt costs (image inputs); good ROI when OCR is unreliable or visuals dominate.
  - Traditional RAG: lower storage and prompt costs; ideal when content is mostly text and extractable.

- __When to use which__
  - Prefer Vision RAG for scanned PDFs, invoices, forms, reports with heavy tables/figures, diagrams.
  - Prefer Traditional RAG for large text corpora, codebases, and documents with reliable text extraction.

---

## Potential Enhancements

- __Hybrid retrieval__: Add a text channel by integrating OCR/text extraction, chunking, and a `text` vector field in Qdrant; blend scores or use staged fusion.
- __Better reranking__: Cross-encoder or LLM judge over candidates for final top-k.
- __Citations__: Include bounding boxes or page regions; overlay highlights in the gallery.
- __Auth and privacy__: Replace public-read MinIO with signed URLs; add auth to Qdrant/minio in `docker-compose.yml`.
- __Observability__: Log query/latency metrics and retrieval traces; add evaluation harness and reproducible benchmarks.
- __Resource tuning__: Adjust HNSW and quantization configs per vector field; right-size `prefetch_limit`/`search_limit`.

---

## Implementation Pointers (for this repo)

- __Indexing paths__: `api/utils.py::convert_pdf_paths_to_images()`, `QdrantService.index_documents()`
- __Collection schema__: `QdrantService._create_collection_if_not_exists()`
- __Pooling logic__: `QdrantService._pool_image_tokens()`
 - __Two-stage query__: `QdrantService._reranking_search_batch()`
 - __MinIO URLs__: `MinioService._get_image_url()` and `_extract_object_name_from_url()`
 - __Chat streaming__: `frontend/app/api/chat/route.ts` (SSE) and `frontend/lib/api/chat.ts` (helpers for request and stream parsing)

---

## Caveats Noted from Code

 - The ColPali image embedding path in `QdrantService._embed_and_mean_pool_batch()` expects per-image token boundaries (`image_patch_start`, `image_patch_len`), while `ColPaliClient.embed_images(...)` currently returns only `{"embeddings": ...}`. Ensure the API contract includes token boundary metadata or adjust the pooling logic accordingly.
 - The default OpenAI model for chat is configured on the frontend (default `gpt-5-nano`) in `frontend/.env.local`. The backend does not manage chat or OpenAI client configuration.
