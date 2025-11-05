# Snappy Architecture 🏗️

This document outlines how the major components in Snappy work together to deliver vision-grounded document search.

```mermaid
---
config:
  theme: neutral
  layout: elk
---
flowchart TB
  subgraph Frontend["Frontend"]
    NEXT["Next.js App"]
    CHAT["Next.js Chat API"]
  end

  subgraph Backend["FastAPI Backend"]
    API["REST Routers"]
  end

  subgraph Services["External Services"]
    QDRANT["Qdrant"]
    MINIO["MinIO"]
    COLPALI["ColPali API"]
    OPENAI["OpenAI API"]
  end

  USER["Browser"] <--> NEXT
  NEXT -- Upload/Search Requests --> API
  API --> QDRANT
  API --> MINIO
  API --> COLPALI
  CHAT --> API
  CHAT --> OPENAI
  CHAT -- SSE Stream --> USER
```

---

## Components

- **FastAPI application** (`backend/api/app.py`) wires the routers for health, retrieval, indexing, maintenance, configuration, and OCR endpoints.
- **Qdrant integration** (`backend/services/qdrant/`) manages vector collections, search, and MUVERA post-processing. The database writer in `indexing/qdrant_indexer.py` builds on the shared pipeline package.
- **Pipeline package** (`backend/services/pipeline/`) hosts the database-agnostic `DocumentIndexer`, batch processor, progress tracking, and storage helpers used during ingestion.
- **MinIO service** (`backend/services/minio.py`) stores page images with concurrent uploads and retry handling.
- **ColPali client** (`backend/services/colpali.py`) communicates with the embedding service for both queries and images.
- **DeepSeek OCR service** (`backend/services/ocr/`) handles OCR requests, integrates with MinIO, and surfaces batch/background helpers for the OCR router.
- **Configuration layer** (`backend/config.py`, `backend/config_schema.py`) keeps runtime settings consistent across the API and UI.
- **Support modules**
  - `backend/api/utils.py` – PDF-to-image conversion
  - `backend/api/progress.py` – Job state tracking for SSE
  - `backend/api/dependencies.py` – Cached service instances and cache invalidation

---

## Indexing Flow

1. `POST /index` receives one or more PDFs and starts a background task.
2. `convert_pdf_paths_to_images` rasterises each page.
3. `DocumentIndexer` (`services/pipeline/document_indexer.py`) handles batching, embedding, image uploads, optional OCR callbacks, and delegates upserts via `services/qdrant/indexing/qdrant_indexer.py`.
4. When DeepSeek OCR is enabled the batch processor invokes `services/ocr` helpers in parallel, storing JSON outputs alongside page images in MinIO.
5. When `ENABLE_PIPELINE_INDEXING=True`, dual executors overlap embedding, storage, OCR, and upserts based on `get_pipeline_max_concurrency()`.
6. `/progress/stream/{job_id}` streams progress updates so the UI can reflect status in real time.

---

## Search Flow

1. `GET /search` embeds the incoming query via ColPali.
2. `SearchManager` (`services/qdrant/search.py`) performs two-stage retrieval:
   - Optional MUVERA first-stage vector for quick prefiltering.
   - Prefetch via pooled vectors when mean pooling is enabled.
   - Final rerank on the original multivectors.
3. Results include metadata and public image URLs; the frontend decides how to display them.

## OCR Flow (Optional)

1. `/ocr/process-page` and `/ocr/process-batch` use `services/ocr` to fetch page images from MinIO and submit them to the DeepSeek OCR microservice.
2. OCR responses (markdown, text, regions, extracted crops) are persisted in MinIO via `services/ocr/storage.py` so future calls can reuse cached outputs.
3. `/ocr/process-document` launches a background job that iterates every page discovered via Qdrant metadata and reports progress through `api/progress`.
4. `/ocr/progress/{job_id}` and `/ocr/progress/stream/{job_id}` expose job status for polling or SSE streaming, mirroring the indexing progress APIs.
5. `/ocr/cancel/{job_id}` stops long-running jobs, while `/ocr/health` verifies that the OCR client can reach the external service.

---

## Frontend Integration

- Pages live under `frontend/app/*` (`/upload`, `/search`, `/chat`, `/configuration`, `/maintenance`, etc.).
- `frontend/lib/api/client.ts` wraps the generated OpenAPI client using `NEXT_PUBLIC_API_BASE_URL`.
- `frontend/app/api/chat/route.ts` runs in the Edge runtime, calls `GET /search`, invokes the OpenAI Responses API, and streams events (`text-delta`, `kb.images`) back to the browser.

---

## ColPali Service

Located in `colpali/`, this FastAPI app powers embeddings.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health`, `/info` | Health and model metadata |
| `POST` | `/patches` | Patch grid estimation |
| `POST` | `/embed/queries` | Text → embeddings |
| `POST` | `/embed/images` | Images → embeddings + token boundaries |

Docker Compose profiles are provided for CPU and GPU deployments, each sharing a Hugging Face cache volume.

---

## Configuration Lifecycle

1. **Schema** – `config_schema.py` defines defaults, metadata, and critical keys.
2. **Runtime store** – Values load from `.env` into `runtime_config`.
3. **Access** – `config.py` exposes typed getters and computed defaults.
4. **API/UI** – `/config/*` endpoints feed the configuration UI; updates trigger cache invalidation for dependent services.

See `backend/docs/configuration.md` and `backend/CONFIGURATION_GUIDE.md` for details.
