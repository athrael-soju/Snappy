# Vision RAG Backend (FastAPI)

A modular FastAPI service that exposes endpoints for indexing PDFs, search, and maintenance.

- Routers in `backend/api/routers/`: `meta`, `retrieval`, `indexing`, `maintenance`
- App factory: `backend/api/app.py:create_app()`
- Entrypoints: `backend/backend.py` (used by Docker) and `backend/main.py` (alt local entry)

## Requirements
- Python 3.10+
- Poppler installed and on PATH (for `pdf2image`)
- Optional: Docker + Docker Compose

## Setup (local)
```bash
# From repo root (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r backend/requirements.txt
```

## Environment
- Copy and edit the root env template:
```bash
# From repo root
copy .env.example .env
```
- Key variables (see `backend/config.py` and `.env.example`):
  - ColPali: `COLPALI_MODE`, `COLPALI_CPU_URL`, `COLPALI_GPU_URL`, or `COLPALI_API_BASE_URL`
  - Qdrant: `QDRANT_URL`
  - MinIO: `MINIO_URL`, `MINIO_PUBLIC_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- Local defaults expect services at:
  - Qdrant: `http://localhost:6333`
  - MinIO: `http://localhost:9000`
  - ColPali: `http://localhost:7001` (CPU) or `http://localhost:7002` (GPU)

## Run (local dev)
```bash
# Option A: recommended (matches Docker CMD)
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

# Option B: run the small launcher
python backend/main.py
```
- OpenAPI docs: http://localhost:8000/docs

## Docker/Compose
- The repo root `docker-compose.yml` provides `qdrant`, `minio`, `backend`, and `frontend` services.
- `backend` is started with:
  - `COLPALI_CPU_URL=http://host.docker.internal:7001`
  - `COLPALI_GPU_URL=http://host.docker.internal:7002`
  - `QDRANT_URL=http://qdrant:6333`
  - `MINIO_URL=http://minio:9000`
  - `MINIO_PUBLIC_URL=http://localhost:9000`

Bring everything up:
```bash
# From repo root
docker compose up -d --build
```

## Key Endpoints
- `GET /health`
- `GET /search?q=...&k=5`
- `POST /index` (multipart files[])
- `POST /clear/qdrant`, `/clear/minio`, `/clear/all`

## Chat and visual citations (context)

The chat streaming endpoint is implemented in the frontend at `frontend/app/api/chat/route.ts` using the OpenAI Responses API. It may perform document search via this backend's `GET /search` and, when images are used, the frontend emits a custom SSE event `kb.images` to the browser. The UI shows a glowing "Visual citations included" chip and an image gallery when such events are received.
