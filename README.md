<img width="80%" alt="image" src="https://github.com/user-attachments/assets/c1e3c300-93dd-401d-81f0-69772d8acc39" />


# Vision Rag Template

A lightweight, end-to-end template for page-level retrieval over PDFs using a ColPali-like approach:

- __Storage__: page images in MinIO, multivector embeddings in Qdrant
- __Retrieval__: two-stage reranking with pooled image-token vectors
- __Generation__: OpenAI chat completions with multimodal context (retrieved page images)
- __API__: FastAPI service exposing endpoints for indexing, search, chat, and maintenance

This repo is intended as a developer-friendly starting point for vision RAG systems.

## Architecture

Below is the high-level component architecture of the Vision RAG template.
See the architecture diagram in [docs/architecture.md](docs/architecture.md). It focuses on the core indexing and retrieval flows for clarity.

- __`api/app.py`__ and `api/routers/*`__: Modular FastAPI application (routers: `meta`, `retrieval`, `chat`, `indexing`, `maintenance`).
- __`fastapi_app.py`__: Thin entrypoint that boots `api.app.create_app()`.
- __`local_app.py`__ + `ui.py`__: Optional local Gradio UI (upload/index PDFs, chat, maintenance actions) separate from the FastAPI server.
- __`clients/qdrant.py`__: `QdrantService` manages collection, indexing, multivector retrieval, and MinIO integration.
- __`clients/minio.py`__: `MinioService` for image storage/retrieval with batch operations and public-read policy.
- __`clients/openai.py`__: Thin wrapper for OpenAI SDK (streaming completions, message construction).
- __`clients/colpali.py`__: HTTP client for a ColPali-style embedding API (queries, images, patch metadata).
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
2) Qdrant multivector prefetch (rows/cols) + re-ranking using `using="original"`
3) Fetch images from MinIO for top-k pages
4) Stream OpenAI answer conditioned on user text + page images

## Features

- __Page-level, multimodal RAG__: stores per-page images, uses image-token pooling for robust retrieval
- __FastAPI endpoints__: OpenAPI docs at `/docs`; endpoints for indexing, search, chat (streaming), and maintenance
- __Dockerized__: one `docker-compose up -d` brings up Qdrant, MinIO and the API
- __Configurable__: all knobs in `.env`/`config.py`

## Prerequisites

- Python 3.10+
- System dependency: Poppler (for `pdf2image`)
  - Linux: `apt-get install poppler-utils`
  - macOS: `brew install poppler`
  - Windows: install Poppler and add `bin/` to PATH (see "Troubleshooting" below)
- Optional but recommended: Docker + Docker Compose

## Quickstart (Docker Compose)

1) Copy env template and edit values:

```bash
cp .env.example .env
# Set OPENAI_API_KEY and OPENAI_MODEL.
# Choose COLPALI_MODE (cpu|gpu) and optionally adjust COLPALI_CPU_URL/COLPALI_GPU_URL.
# To force a single endpoint, set COLPALI_API_BASE_URL (takes precedence over mode URLs).
```

2) Start services:

```bash
docker compose up -d
```

This launches:

- Qdrant on http://localhost:6333
- MinIO on http://localhost:9000 (console: http://localhost:9001, user/pass: `minioadmin`/`minioadmin`)
- API on http://localhost:8000 (OpenAPI docs at http://localhost:8000/docs)

3) Open the API docs at http://localhost:8000/docs

## Local development (without Compose)

1) Install system deps (Poppler). Ensure `pdftoppm`/`pdftocairo` are in PATH.
2) Create venv and install Python deps:

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

3) Run Qdrant and MinIO separately (examples via Docker):

```bash
# Qdrant
docker run -p 6333:6333 -p 6334:6334 -v qdrant_data:/qdrant/storage --name qdrant qdrant/qdrant:latest
# MinIO
docker run -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -v minio_data:/data --name minio minio/minio:latest server /data --console-address ":9001"
```

4) Configure `.env` (or export vars) and run the API:

```bash
cp .env.example .env
# set OPENAI_API_KEY, OPENAI_MODEL, and ensure QDRANT_URL/MINIO_URL point to your services
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

## Optional local Gradio UI

For a local, interactive UI (separate from the FastAPI server):

```bash
python local_app.py
```

Defaults to `HOST=0.0.0.0` and `PORT=7860` unless overridden via environment variables.

## Environment variables

Most defaults are in `config.py`. Key variables:

- __Core__: `LOG_LEVEL` (INFO), `HOST` (0.0.0.0), `PORT` (8000)
- __OpenAI__: `OPENAI_API_KEY`, `OPENAI_MODEL`
  - Note: `clients/openai.py` uses `config.OPENAI_MODEL` (default `gpt-5-nano`). Both the API and local UI respect this unless overridden per request.
- __ColPali API__: Mode-based selection with optional explicit override:
  - `COLPALI_MODE` (cpu|gpu; default `cpu`)
  - `COLPALI_CPU_URL` (default `http://localhost:7001`)
  - `COLPALI_GPU_URL` (default `http://localhost:7002`)
  - `COLPALI_API_BASE_URL` (if set, overrides the above and is used as-is)
  - `COLPALI_API_TIMEOUT`
- __Qdrant__: `QDRANT_URL` (default http://localhost:6333), `QDRANT_COLLECTION_NAME` (documents), `QDRANT_SEARCH_LIMIT`, `QDRANT_PREFETCH_LIMIT`
- __MinIO__: `MINIO_URL` (default http://localhost:9000), `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME` (documents), `MINIO_WORKERS`, `MINIO_RETRIES`, `MINIO_FAIL_FAST`, `MINIO_IMAGE_FMT`
- __Processing__: `DEFAULT_TOP_K`, `BATCH_SIZE`, `WORKER_THREADS`, `MAX_TOKENS`

See `.env.example` for a minimal starting point. When using Compose, note:
- `vision-rag` service sets defaults `COLPALI_CPU_URL=http://host.docker.internal:7001` and `COLPALI_GPU_URL=http://host.docker.internal:7002`.
- `QDRANT_URL` and `MINIO_URL` are set to internal service addresses (`http://qdrant:6333`, `http://minio:9000`).

## Using the API

You can interact via the OpenAPI UI at `/docs` or with HTTP clients:

- `GET /health` — check dependencies status.
- `GET /search?q=...&k=5` — retrieve top-k results with payload metadata.
- `POST /index` (multipart files[]) — upload and index PDFs.
- `POST /chat` — JSON body with query and options; returns full text and retrieved pages.
- `POST /chat/stream` — same body; streams text/plain tokens.
- `POST /clear/qdrant` | `/clear/minio` | `/clear/all` — maintenance.

## API Examples

Example search:

```bash
curl "http://localhost:8000/search?q=What%20is%20the%20booking%20reference%3F&k=5"
```

Example chat:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What is the booking reference for case 002?",
    "k": 5,
    "ai_enabled": true
  }'
```

## ColPali API contract (expected)

`clients/qdrant.py` expects the embedding server to expose endpoints:

- `GET /health` -> `200` when healthy
- `GET /info` -> JSON including `{"dim": <int>}` for embedding dimension
- `POST /patches` with body `{ "dimensions": [{"width": W, "height": H}, ...] }` ->
  `{ "results": [{"n_patches_x": int, "n_patches_y": int}, ...] }`
- `POST /embed/queries` with `{ "queries": ["...", ...] }` -> `{ "embeddings": [[[...], ...]] }`
- `POST /embed/images` (multipart form) -> for each image, an object:
  ```json
  {
    "embedding": [[...], ...],
    "image_patch_start": <int>,
    "image_patch_len": <int>
  }
  ```

Note: the example `clients/colpali.py` is a thin starting client. Ensure it matches your server’s response shape (including `image_patch_start`/`image_patch_len`) to avoid runtime errors in `QdrantService._embed_and_mean_pool_batch(...)`.

## Data model in Qdrant

`clients/qdrant.py` creates a collection with three vectors per point:

- `original`: full token sequence
- `mean_pooling_rows`: pooled by rows
- `mean_pooling_columns`: pooled by columns

Each point has payload metadata like:

```json
{
  "index": 12,
  "page": "Page 3",
  "image_url": "http://localhost:9000/documents/images/<id>.png",
  "document_id": "<id>",
  "filename": "file.pdf",
  "file_size_bytes": 123456,
  "pdf_page_index": 3,
  "total_pages": 10,
  "page_width_px": 1654,
  "page_height_px": 2339,
  "indexed_at": "2025-01-01T00:00:00Z"
}
```

## Troubleshooting

- __OpenAI key/model__: If AI responses show an error, verify `OPENAI_API_KEY` and `OPENAI_MODEL`.
- __ColPali API health__: On start, `QdrantService` checks `GET /health`. Ensure your server is reachable at `COLPALI_API_BASE_URL`.
- __Patch metadata mismatch__: If you see an error like "embed_images() returned embeddings without image-token boundaries", update your embedding server/client to include `image_patch_start` and `image_patch_len` per image.
- __MinIO access__: The app sets a public-read bucket policy. For production, lock this down. If images fail to upload, check MinIO logs and credentials.
- __Poppler on Windows__: Install Poppler (e.g., download a release, extract, add `poppler-*/bin` to PATH). `pdf2image` must find `pdftoppm`.
- __Ports already in use__: Change `PORT` (app), `QDRANT_URL`, `MINIO_URL`, or Docker port mappings.

## Scripts and containers

- `Dockerfile`: Python 3.10-slim, installs system deps (`poppler-utils`, etc.), installs requirements, and runs `uvicorn fastapi_app:app` on port 8000.
- `docker-compose.yml`: brings up `qdrant`, `minio`, and the API (`vision-rag`) on 8000.
- `packages.txt`: system package hint for environments like Codespaces.

## Development notes

- FastAPI app is assembled by `api/app.py` (routers: meta, retrieval, chat, indexing, maintenance) and booted by `fastapi_app.py`.
- Local Gradio UI lives in `local_app.py` and `ui.py` (separate from the API).
- Replace OpenAI with another LLM by adapting `clients/openai.py` and the chat router in `api/routers/chat.py`.
- To filter search by metadata, see `QdrantService.search_with_metadata(...)`.

## License

MIT License. See `LICENSE`.

## Acknowledgements

Inspired by ColPali-style page-level retrieval and multivector search patterns. Uses Qdrant, MinIO, Gradio, pdf2image, and OpenAI.

## Citations

- ColPali — https://arxiv.org/abs/2407.01449
- Qdrant Optimizations
  - https://qdrant.tech/blog/colpali-qdrant-optimization/
  - https://qdrant.tech/articles/binary-quantization/
- PyTorch — https://pytorch.org/
