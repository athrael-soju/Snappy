# Snappy Backend – FastAPI Service ✨

This FastAPI application handles PDF ingestion, page-level retrieval, runtime configuration, OCR workflows, and system maintenance for Snappy. Routers live under `backend/api/routers/` (`meta`, `retrieval`, `indexing`, `maintenance`, `config`, `ocr`) and are wired together inside `backend/api/app.py:create_app()`.

---

## Prerequisites

- **Python 3.11+**
- **Poppler** on your `PATH` (`pdftoppm` is required for PDF rasterisation)
- **Docker + Docker Compose** (optional, recommended for local services)

---

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

Copy the environment template and customise as needed:

```bash
cp .env.example .env
```

Key settings:
- **ColPali**: `COLPALI_URL`, `COLPALI_API_TIMEOUT`
- **DeepSeek OCR**: `DEEPSEEK_OCR_ENABLED`, `DEEPSEEK_OCR_URL`, `DEEPSEEK_OCR_API_TIMEOUT`, `DEEPSEEK_OCR_MAX_WORKERS`, `DEEPSEEK_OCR_POOL_SIZE`, `DEEPSEEK_OCR_MODE`, `DEEPSEEK_OCR_TASK`, `DEEPSEEK_OCR_INCLUDE_GROUNDING`, `DEEPSEEK_OCR_INCLUDE_IMAGES`
- **DuckDB**: `DUCKDB_ENABLED`, `DUCKDB_URL`, `DUCKDB_API_TIMEOUT`
- **Qdrant**: `QDRANT_EMBEDDED`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, quantisation toggles
- **MinIO**: `MINIO_URL`, `MINIO_PUBLIC_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- **Uploads**: `UPLOAD_ALLOWED_FILE_TYPES` (PDF-only by default), `UPLOAD_MAX_FILE_SIZE_MB`, `UPLOAD_MAX_FILES`, `UPLOAD_CHUNK_SIZE_MBYTES`
- **Job Cancellation**: `JOB_CANCELLATION_RESTART_SERVICES_ENABLED`, `JOB_CANCELLATION_SERVICE_RESTART_TIMEOUT`, `JOB_CANCELLATION_WAIT_FOR_RESTART`

Defaults assume local services at:
- Qdrant → `http://localhost:6333`
- MinIO → `http://localhost:9000`
- ColPali → `http://localhost:7000`
- DeepSeek OCR → `http://localhost:8200` (optional)

When the backend runs inside Docker Compose, keep `COLPALI_URL=http://colpali:7000` and `DEEPSEEK_OCR_URL=http://deepseek-ocr:8200` so the containers communicate via the Compose network.



Check `backend/docs/configuration.md` for the complete reference.

---

## Run the API

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

or

```bash
python backend/main.py
```

Interactive docs live at http://localhost:8000/docs.

---

## Docker Compose

### Standalone Development

Run backend with minimal dependencies (Qdrant + MinIO):

```bash
cd backend
docker compose up -d --build
```

This starts:
- Backend API at `http://localhost:8000`
- Qdrant at `http://localhost:6333`
- MinIO at `http://localhost:9000`

ML services (ColPali, DeepSeek OCR, DuckDB) are disabled by default for faster startup.

### As Part of Full Stack

From the project root, use the Makefile with profiles:

```bash
# Minimal - ColPali only (works on any hardware)
make up-minimal

# ML - ColPali + DeepSeek OCR (requires NVIDIA GPU)
make up-ml

# Full - All services including DuckDB
make up-full
```

Or use the legacy approach:

```bash
docker compose up -d --build
```

**Service Communication:**
- Inside Docker: Services use container names (`http://colpali:7000`, `http://deepseek-ocr:8200`)
- From host: Services use `localhost` (`http://localhost:7000`, `http://localhost:8200`)
- `.env` files use `localhost` URLs by default; docker-compose.yml overrides with service names

**Hardware Configuration:**
- ColPali: Automatically detects NVIDIA GPU → Apple Silicon MPS → CPU
- DeepSeek OCR: Requires NVIDIA GPU (set `DEEPSEEK_OCR_ENABLED=false` if unavailable)
- DuckDB: Optional analytics service (set `DUCKDB_ENABLED=false` to disable)

---

## API Surface

### Meta
- `GET /health` – Overall health including ColPali, MinIO, Qdrant

### Retrieval
- `GET /search?q=...&k=5` – Vision-first search (defaults to 10 results when `k` omitted)

### Indexing
- `POST /index` – Upload PDFs as `files[]`; work runs in the background
- `GET /progress/stream/{job_id}` – Server-Sent Events progress feed
- `GET /progress/{job_id}` – Poll job progress (alternative to SSE)
- `POST /index/cancel/{job_id}` – Cancel a running indexing job with comprehensive cleanup

### OCR
- `POST /ocr/process-page` - OCR a single indexed page (DeepSeek OCR must be enabled)
- `POST /ocr/process-batch` - Run OCR across multiple page numbers in parallel
- `POST /ocr/process-document` - Launch a background OCR job for every page in a document
- `GET /ocr/progress/{job_id}` / `/ocr/progress/stream/{job_id}` - Poll or stream OCR job status updates
- `POST /ocr/cancel/{job_id}` - Cancel a running OCR job with comprehensive cleanup
- `GET /ocr/health` - Health check for the OCR client/service

**OCR Retrieval Modes:**
- When `DUCKDB_ENABLED=True`: OCR data retrieved inline from DuckDB (1 HTTP request)
- When `DUCKDB_ENABLED=False`: OCR URLs pre-computed and stored in Qdrant payload; frontend fetches from MinIO (2 HTTP requests)

### Maintenance
- `GET /status` – Collection and bucket statistics (includes DuckDB document count when enabled)
- `POST /initialize` – Provision collection + bucket (run this once on a new stack)
- `DELETE /delete` – Tear everything down (Qdrant, MinIO, DuckDB)
- `POST /clear/qdrant` – Clear vector database only
- `POST /clear/minio` – Clear object storage only
- `POST /clear/duckdb` – Clear analytics database only (when enabled)
- `POST /clear/all` – Clear all data across all services

### DuckDB Analytics (Optional)
- `POST /duckdb/query` - Execute SQL query against OCR analytics database
- `GET /duckdb/health` - Health check for DuckDB service

### Configuration
- `GET /config/schema`, `GET /config/values` – Inspect current settings
- `POST /config/update`, `POST /config/reset` – Update or reset runtime configuration

Runtime updates are temporary—persist changes in `.env` for restarts.

---

## Job Cancellation

Job cancellation provides comprehensive cleanup when indexing or OCR operations are cancelled or fail.

### How It Works

When you cancel a job via `POST /index/cancel/{job_id}` or `POST /ocr/cancel/{job_id}`, the cancellation service:

1. **Optionally Restarts Services (0-75%)**:
   - Sends restart requests to ColPali and DeepSeek OCR services
   - Services exit immediately and restart via Docker policy
   - Stops any ongoing batch embedding or OCR processing
   - Configurable via `JOB_CANCELLATION_RESTART_SERVICES_ENABLED`

2. **Cleans Qdrant (75-81%)**:
   - Deletes all vector points for the document
   - Removes embeddings and metadata from the collection

3. **Cleans MinIO (81-87%)**:
   - Deletes all objects under `{filename}/` prefix
   - Removes page images, OCR JSON, region crops

4. **Cleans DuckDB (87-93%)**:
   - Deletes document record and cascading pages/regions
   - Only runs if DuckDB is enabled

5. **Cleans Temp Files (93-100%)**:
   - Removes PDF conversion artifacts from `/tmp`

### Configuration

Control cancellation behavior via environment variables:

```bash
# Enable/disable service restart on cancellation
JOB_CANCELLATION_RESTART_SERVICES_ENABLED=true

# Wait for services to come back online (default: true)
JOB_CANCELLATION_WAIT_FOR_RESTART=true

# Service restart timeout in seconds (default: 30)
JOB_CANCELLATION_SERVICE_RESTART_TIMEOUT=30
```

### Progress Tracking

Cancellation progress is reported via SSE at `/progress/stream/{job_id}`:
- Service restart status (if enabled)
- Cleanup progress for each service
- Success/failure messages
- Detailed error reporting

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

---

## Additional Documentation

- **`docs/architecture.md`** - System architecture and data flows
- **`docs/configuration.md`** - Complete configuration reference
- **`docs/analysis.md`** - Vision vs. text RAG comparison
- **`docs/pipeline.md`** - Pipeline processing architecture (vector DB agnostic)
- **`CONFIGURATION_GUIDE.md`** - Configuration implementation details

