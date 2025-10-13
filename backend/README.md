# Vision RAG Backend (FastAPI)

A modular FastAPI service that exposes endpoints for indexing PDFs, search, and maintenance.

- Routers in `backend/api/routers/`: `meta`, `retrieval`, `indexing`, `maintenance`, `config`
- App factory: `backend/api/app.py:create_app()`
- Entrypoints: `backend/backend.py` (used by Docker) and `backend/main.py` (alt local entry)

## Requirements
- Python 3.10+
- Poppler installed and on PATH (for `pdf2image`)
- Optional: Docker + Docker Compose
- Optional: `fastembed[postprocess]` (only required when enabling the MUVERA post-processor)

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
  - Qdrant: `QDRANT_EMBEDDED`, `QDRANT_URL`
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

### Meta
- `GET /health` — Service health check with dependencies status

### Retrieval
- `GET /search?q=...&k=5` — Visual search over indexed documents (defaults to `DEFAULT_TOP_K` when `k` is omitted)

### Indexing
- `POST /index` (multipart files[]) — Start background indexing job
- `GET /progress/stream/{job_id}` — SSE stream for real-time indexing progress
- `POST /index/cancel/{job_id}` — Cancel an in-progress indexing job

### Maintenance
- `GET /status` — Get collection and bucket status with statistics (vector count, object count, exists flags)
- `POST /initialize` — Create/initialize collection and bucket based on current configuration
- `DELETE /delete` — Delete collection and bucket completely
- `POST /clear/qdrant` — Clear all data from Qdrant collection (data reset)
- `POST /clear/minio` — Clear all objects from MinIO bucket (data reset)
- `POST /clear/all` — Clear all data from both systems (complete data reset)

- MinIO batch deletes populate the result map with descriptive error strings even when the service omits an `object_name`, so failures can be mapped back to the requested URLs.

### Configuration
- `GET /config/schema` — Get configuration schema with categories and metadata
- `GET /config/values` — Get current runtime configuration values
- `POST /config/update` — Update a configuration value at runtime
- `POST /config/reset` — Reset all configuration to defaults

## Chat and Visual Citations (Context)

The chat streaming endpoint is implemented in the frontend at `frontend/app/api/chat/route.ts` using **Edge Runtime** for optimized streaming performance. The route calls OpenAI's Responses API and streams Server-Sent Events (SSE) to the browser.

- When tool calling is disabled, the backend performs document search unconditionally via `GET /search`
- When tool calling is enabled, the model may call the `document_search` tool
- The frontend emits a custom SSE event `kb.images` when visual citations are available
- The UI displays a "Visual citations included" chip and image gallery accordingly

## Configuration Management

The `/maintenance` page includes a **Configuration** tab providing a web-based interface for managing backend environment variables at runtime. See [backend/docs/configuration.md](docs/configuration.md) for detailed setting documentation and [backend/CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for system architecture details.

**Important Notes:**
- Configuration changes update the backend runtime environment immediately
- Changes are not persisted to the `.env` file and will be lost on container restart
- For permanent changes, manually update your `.env` file
- Critical settings (e.g., API URLs, collection settings) trigger service invalidation and re-initialization
