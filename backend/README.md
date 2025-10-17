# Vision RAG Backend (FastAPI)

A FastAPI service that provides PDF ingestion, page-level retrieval, and system
maintenance APIs for the template. The backend exposes modular routers under
`backend/api/routers/` (`meta`, `retrieval`, `indexing`, `maintenance`,
`config`) and is bootstrapped via `backend/api/app.py:create_app()`.

## Requirements

- Python 3.10+
- Poppler available on `PATH` (`pdf2image` uses `pdftoppm`)
- Optional: Docker + Docker Compose
- Optional: `fastembed[postprocess]` if you plan to enable MUVERA

## Local setup

```bash
# From repo root (PowerShell example)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r backend/requirements.txt
```

## Environment

```bash
# From repo root
copy .env.example .env
```

Key backend variables (see `.env.example` and `backend/config.py`):

- ColPali: `COLPALI_MODE`, `COLPALI_CPU_URL`, `COLPALI_GPU_URL`,
  `COLPALI_API_TIMEOUT`
- Qdrant: `QDRANT_EMBEDDED`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`,
  quantisation toggles
- MinIO: `MINIO_URL`, `MINIO_PUBLIC_URL`,
  `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

Defaults assume:

- Qdrant at `http://localhost:6333`
- MinIO at `http://localhost:9000`
- ColPali CPU service at `http://localhost:7001`, GPU service at
  `http://localhost:7002`

See `backend/docs/configuration.md` for a full reference to every runtime
setting.

## Run locally

```bash
# Matches docker-compose
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

# Alternative launcher (uses HOST/PORT env vars)
python backend/main.py
```

Visit http://localhost:8000/docs for OpenAPI documentation.

## Docker Compose

The root `docker-compose.yml` starts `qdrant`, `minio`, `backend`, and
`frontend`. The backend container sets:

- `COLPALI_CPU_URL=http://host.docker.internal:7001`
- `COLPALI_GPU_URL=http://host.docker.internal:7002`
- `QDRANT_URL=http://qdrant:6333`
- `MINIO_URL=http://minio:9000`
- `MINIO_PUBLIC_URL=http://localhost:9000`

Bring up the stack:

```bash
docker compose up -d --build
```

## Key endpoints

### Meta

- `GET /health` – Dependency health summary (ColPali, MinIO, Qdrant)

### Retrieval

- `GET /search?q=...&k=5` – Visual search over indexed documents  
  (defaults to 10 results when `k` is omitted)

### Indexing

- `POST /index` (multipart `files[]`) – Start a background indexing job
- `GET /progress/stream/{job_id}` – Server-Sent Events stream with progress
- `POST /index/cancel/{job_id}` – Cancel an in-flight job

### Maintenance

- `GET /status` – Collection and bucket statistics
- `POST /initialize` – Create collection/bucket according to current config
- `DELETE /delete` – Remove collection and bucket
- `POST /clear/qdrant` – Clear Qdrant data
- `POST /clear/minio` – Clear MinIO objects
- `POST /clear/all` – Clear both stores

MinIO batch deletes return a structured report so failed objects can be
identified even when MinIO omits their names.

### Configuration

- `GET /config/schema` – Configuration schema (categories, defaults, metadata)
- `GET /config/values` – Current runtime values
- `POST /config/update` – Update a single value at runtime
- `POST /config/reset` – Reset everything to schema defaults
- `POST /config/optimize` – Apply hardware-driven tuning recommendations

Configuration changes apply immediately but do **not** modify your `.env` file.
Persist any important changes manually.

## Chat and visual citations

Chat streaming lives in the frontend at `frontend/app/api/chat/route.ts`. The
Next.js route calls the OpenAI Responses API, streams SSE to the browser, and
injects retrieved page images via a `kb.images` event. The backend is
responsible for document search (`GET /search`) and the supporting maintenance
APIs; it does not proxy chat requests.

## Configuration management UI

The `/configuration` page in the frontend talks to the `/config/*` API. It
surfaces the schema described above with typed inputs, validation, and runtime
updates. Critical changes invalidate cached
services (Qdrant/MinIO/ColPali) so the next API call observes the new values.
