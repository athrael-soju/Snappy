# Snappy Backend - FastAPI Service

This FastAPI application handles PDF ingestion, page-level retrieval, runtime configuration, and system maintenance for Snappy. Routers live under `backend/api/routers/` (`meta`, `retrieval`, `indexing`, `maintenance`, `config`) and are wired together inside `backend/api/app.py:create_app()`.

---

## Prerequisites

- **Python 3.10+**
- **Poppler** on your `PATH` (`pdftoppm` is required for PDF rasterisation)
- **Docker + Docker Compose** (optional, recommended for local services)
- **`fastembed[postprocess]`** if you plan to enable MUVERA acceleration
- **NVIDIA GPU + drivers** when running the DeepSeek OCR service locally

---

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r backend/requirements.txt
```

Copy the environment template and customise as needed:

```bash
cp .env.example .env
```

Key settings:
- **ColPali**: `COLPALI_URL`, `COLPALI_API_TIMEOUT`
- **DeepSeek OCR**: `DEEPSEEK_OCR_URL`, `DEEPSEEK_OCR_TIMEOUT`, FlashAttention toggle (`DEEPSEEK_OCR_ENABLE_FLASH_ATTN`), profile & payload defaults (`DEEPSEEK_OCR_DEFAULT_*`, `DEEPSEEK_OCR_RETURN_*`)
- **Qdrant**: `QDRANT_EMBEDDED`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, quantisation toggles
- **MinIO**: `MINIO_URL`, `MINIO_PUBLIC_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- **Uploads**: `UPLOAD_ALLOWED_FILE_TYPES` (PDF-only by default), `UPLOAD_MAX_FILE_SIZE_MB`, `UPLOAD_MAX_FILES`, `UPLOAD_CHUNK_SIZE_BYTES`

Defaults assume local services at:
- Qdrant → `http://localhost:6333`
- MinIO → `http://localhost:9000`
- ColPali → `http://localhost:7000`
- DeepSeek OCR → `http://localhost:8200`

Check `backend/docs/configuration.md` for the complete reference.

---

## Run the API

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

or

```bash
python backend/main.py
```

Interactive docs live at http://localhost:8000/docs.

---

## Docker Compose

The root `docker-compose.yml` coordinates `qdrant`, `minio`, `backend`, and `frontend`. Environment values are pre-wired for container-to-container networking:

- `COLPALI_URL=http://host.docker.internal:7000`
- `DEEPSEEK_OCR_URL=http://deepseek-ocr:8200`
- `QDRANT_URL=http://qdrant:6333`
- `MINIO_URL=http://minio:9000`
- `MINIO_PUBLIC_URL=http://localhost:9000`

Start the optional OCR service with `docker compose --profile ocr up -d --build` when you want DeepSeek available.

Launch everything:

```bash
docker compose up -d --build
```

MinIO credentials must be provided; the backend stores page images in object storage and does not fall back to inline storage.

---

## API Surface

### Meta
- `GET /health` – Overall health including ColPali, MinIO, Qdrant

### Retrieval
- `GET /search?q=...&k=5` – Vision-first search (defaults to 10 results when `k` omitted)

### Indexing
- `POST /index` – Upload PDFs as `files[]`; work runs in the background
- `GET /progress/stream/{job_id}` – Server-Sent Events progress feed
- `POST /index/cancel/{job_id}` – Cancel a running job

### Maintenance
- `GET /status` – Collection and bucket statistics
- `POST /initialize` – Provision collection + bucket (run this once on a new stack)
- `DELETE /delete` – Tear everything down
- `POST /clear/qdrant`, `/clear/minio`, `/clear/all` – Data reset helpers

### OCR (DeepSeek)
- `GET /ocr/health` – Quick health probe for the DeepSeek OCR service
- `GET /ocr/info` / `GET /ocr/defaults` – Surface model metadata and backend defaults
- `GET /ocr/presets` – Expose available profile presets and task aliases
- `POST /ocr/infer` – Proxy OCR requests (profiles, markdown/figures, flash-attn metadata; requires `DEEPSEEK_OCR_ENABLED=True`)

### Configuration
- `GET /config/schema`, `GET /config/values` – Inspect current settings
- `POST /config/update`, `POST /config/reset` – Update or reset runtime configuration

Runtime updates are temporary—persist changes in `.env` for restarts.

---

## Chat and Visual Citations

Document search and maintenance live entirely in the backend. Chat streaming is implemented in `frontend/app/api/chat/route.ts`, which:

1. Calls `GET /search` to gather relevant pages
2. Invokes the OpenAI Responses API
3. Streams Server-Sent Events (including `kb.images` events) back to the browser

The backend does not proxy OpenAI traffic.

---

## Configuration UI

The `/configuration` frontend page consumes the `/config/*` APIs to provide:

- Typed inputs with validation
- Real-time value updates with draft detection
- "Save Changes" button to batch-apply all modifications
- "Reset section" and "Reset all" buttons to restore defaults (requires save to apply)
- Discard button to revert unsaved changes
- Automatic cache invalidation for critical settings (Qdrant, MinIO, ColPali) when changes are saved

For implementation details, see `backend/CONFIGURATION_GUIDE.md`.

