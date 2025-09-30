# Architecture

A concise view of the Vision RAG template and its main data flows.

```mermaid
---
config:
  theme: neutral
  layout: elk
  look: neo
---
flowchart TB
 subgraph Services["🛠 Services"]
        BACKEND[["⚙️ Backend API"]]
        NXCHAT[["💬 Chat Service API"]]
  end
 subgraph External["🌐 External Integrations"]
        QD[("💾 Qdrant Vector DB")]
        MN[("🗄 MinIO Storage")]
        CQ(["☁️ ColPali Embedding API"])
        OA(["☁️ OpenAI API"])
  end
    U["🖥 User Browser"] <--> NEXT["🎨 Next.js Frontend"]
    NEXT -- 📤 Upload PDF(s) --> BACKEND
    NEXT -- 🔎 Search Query --> BACKEND
    BACKEND --> MN & CQ & QD
    NEXT -- 💬 Ask Question --> NXCHAT
    NXCHAT <--> OA
    NXCHAT -- 📡 Streamed Reply --> U

```

Below is the high-level component architecture of the Vision RAG template.
See the architecture diagram in [backend/docs/architecture.md](backend/docs/architecture.md). It focuses on the core indexing and retrieval flows for clarity.

- __`api/app.py`__ and `api/routers/*`__: Modular FastAPI application (routers: `meta`, `retrieval`, `indexing`, `maintenance`).
- __`backend.py`__: Thin entrypoint that boots `api.app.create_app()`.
- __`services/qdrant/`__: Refactored package with separation of concerns:
  - `service.py`: `QdrantService` main orchestrator
  - `collection.py`: Collection management and schema creation
  - `embedding.py`: Embedding processor with parallel pooling operations
  - `indexing.py`: Document indexing with pipelined processing
  - `search.py`: Search operations with MUVERA and multi-vector reranking
- __`services/minio.py`__: `MinioService` for image storage/retrieval with batch operations and public-read policy.
- __`services/colpali.py`__: HTTP client for a ColPali-style embedding API (queries, images, patch metadata).
- __`config.py`__: Centralized configuration via environment variables.

Additionally:

- __`api/utils.py`__: Shared helpers for the API (e.g., PDF→image conversion used by the indexing route).

__Indexing flow__:

1) PDF -> images via `pdf2image.convert_from_path`
2) Images -> embeddings via external ColPali API
3) Images saved to MinIO (public URL)
4) Embeddings (original + mean-pooled rows/cols) upserted to Qdrant with payload metadata

__Retrieval flow__:

1) Query -> embedding (ColPali API)
2) Qdrant multivector prefetch (rows/cols) + re-ranking using `using="original"`; if MUVERA is enabled, the service performs a first-stage search on `muvera_fde` and prefetches multivectors for rerank
3) Fetch images from MinIO for top-k pages
4) Frontend chat API streams OpenAI Responses with multimodal context (retrieved page images)

Notes

- __Server entrypoint__: `main.py` (or `backend.py`) boots `api.app.create_app()` and serves the modular routers.
- __Frontends__: Next.js app under `frontend/app/*` is the primary and only UI.
- __Indexing__: The API `/index` route (`api/routers/indexing.py`) converts PDFs to page images (see `api/utils.py::convert_pdf_paths_to_images()`), then starts a background indexing job. `DocumentIndexer` (in `services/qdrant/indexing.py`) uses a pipelined architecture with separate thread pools for batch processing and Qdrant upserts, maximizing throughput by overlapping embedding (slow), MinIO uploads (I/O-bound, internally parallelized with `MINIO_WORKERS` threads), and Qdrant upserts (I/O-bound). The `EmbeddingProcessor` (in `services/qdrant/embedding.py`) gets embeddings from the ColPali API, mean-pools rows/cols with parallel processing for high-core systems, and the indexer upserts multivectors to Qdrant concurrently. Progress is tracked in-memory and streamed via `GET /progress/stream/{job_id}` (SSE).
- __Retrieval__: `SearchManager` (in `services/qdrant/search.py`) embeds the query via ColPali, runs multivector search on Qdrant (optionally MUVERA-first stage when enabled), and returns metadata with image URLs (images are NOT fetched from MinIO during search to optimize latency). The frontend uses URLs directly for display. The frontend Chat API route (`frontend/app/api/chat/route.ts`) calls OpenAI with the user text + images and streams the answer to the browser. The `/search` route (`api/routers/retrieval.py`) returns structured results with URLs.
- The diagram intentionally omits lower-level details (e.g., prefetch limits, comparator settings) to stay readable.

## Next.js frontend integration

- __App location__: `frontend/app/*` with pages:
  - `frontend/app/chat/page.tsx` → retrieves images via backend `/search` and streams chat from `frontend/app/api/chat/route.ts`.
  - `frontend/app/search/page.tsx` → calls `/search` via `RetrievalService` and renders image results with labels/scores.
  - `frontend/app/upload/page.tsx` → calls `/index` (starts background job) and subscribes to `/progress/stream/{job_id}` (SSE) for real-time progress.
  - `frontend/app/page.tsx` → landing page.
- __API client base URL__: `frontend/lib/api/client.ts` sets `OpenAPI.BASE` from `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`).
- __Images__: `frontend/next.config.ts` allows remote images from MinIO at `http://localhost:9000/**` and (inside Docker) `http://minio:9000/**` for Next/Image compatibility.

## Backend API surface used by the frontend

- `/` → root listing (see `api/routers/meta.py`).
- `/health` → service health (ColPali, MinIO, Qdrant).
- `/index` (POST multipart) → start background indexing job; responds with `{ status, job_id, total }`.
- `/progress/stream/{job_id}` (GET) → push indexing status via Server‑Sent Events.
- `/search` (GET q, k) → semantic search results (see `api/routers/retrieval.py`).
- `/clear/qdrant`, `/clear/minio`, `/clear/all` → maintenance endpoints.

Chat streaming is not proxied by the backend. It is implemented in the Next.js API route at `frontend/app/api/chat/route.ts`, which calls OpenAI's Responses API and streams Server-Sent Events (SSE) to the browser.

## OpenAPI and client generation

- __Spec location__: `frontend/docs/openapi.json` (current file in repo).
- __Codegen scripts__: see `frontend/package.json` `gen:sdk` and `gen:zod`.
  - They already point to `./docs/openapi.json` (when run from `frontend/`). If you relocate the spec, update these paths accordingly.
- __Generated clients__: emitted to `frontend/lib/api/generated` and `frontend/lib/api/zod` and consumed by pages via `ChatService`, `RetrievalService`, `IndexingService`.

## CORS and connectivity

- `api/app.py` enables permissive CORS for development: `allow_origins=["*"]` and `allow_methods/headers=["*"]`.
- Configure the frontend to reach the backend by setting `NEXT_PUBLIC_API_BASE_URL` (e.g., `http://localhost:8000`).


## ColPali service (`colpali/`) and why it is separate

- **What it is**: A standalone FastAPI service that serves ColQwen2.5 embeddings and patch utilities. Code lives in `colpali/`.
- **Endpoints** (see `colpali/app.py`):
  - `GET /health`, `GET /info`
  - `POST /patches` → returns patch grid counts for given image dimensions
  - `POST /embed/queries` → query embeddings
  - `POST /embed/images` → image embeddings with image-token boundaries
- **How backend uses it**:
  - `backend/services/colpali.py` calls the above endpoints.
  - Base URL configured in `backend/config.py` via `COLPALI_API_BASE_URL` or `COLPALI_MODE` (`cpu|gpu`) selecting `COLPALI_CPU_URL` (default `http://localhost:7001`) or `COLPALI_GPU_URL` (default `http://localhost:7002`).
  - Timeout via `COLPALI_API_TIMEOUT`.
- **Deployment (ports and Docker)**:
  - `colpali/docker-compose.yml` exposes two services:
    - CPU: external `7001` → container `7000` (`api-cpu`, `Dockerfile.cpu`)
    - GPU: external `7002` → container `7000` (`api-gpu`, `Dockerfile.gpu`, `gpus: all`)
  - Both mount a shared Hugging Face cache volume (`hf-cache`) for faster cold starts.
- **Why it is separate from the backend**:
  - Resource isolation: GPU scheduling and heavy ML deps are kept out of the web API container.
  - Scalability: scale the embedding service independently from the API, pick CPU or GPU per environment.
  - Operational flexibility: roll/upgrade models without redeploying the backend; can be hosted remotely.
  - Security and stability: stricter attack surface for the backend; isolating large frameworks reduces blast radius.
- **How to wire it up**:
  - Run either the CPU or GPU service from `colpali/` (see `docker-compose.yml`).
  - Point the backend to it via `COLPALI_API_BASE_URL` or set `COLPALI_MODE=cpu|gpu` and ensure `COLPALI_CPU_URL`/`COLPALI_GPU_URL` match your deployed ports.

