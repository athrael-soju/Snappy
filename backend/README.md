# Morty™ Backend – Where the Magic Happens

The Morty backend is a FastAPI service that powers PDF ingestion, page-level retrieval, and system maintenance. It is a direct continuation of the Snappy backend, delivered as part of a **pro-bono** collaboration with Vultr and the Morty™ mascot. All API routes, configuration schemas, and job orchestration remain compatible with existing Snappy deployments.

## Requirements

- Python 3.10 or newer  
- Poppler utilities (`pdftoppm` must be on `PATH`)  
- Docker and Docker Compose (optional but recommended for local parity)  
- Optional: `fastembed[postprocess]` for MUVERA acceleration

## Quick Start

```bash
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -U pip setuptools wheel
pip install -r backend/requirements.txt
```

Then configure your environment:

```bash
copy .env.example .env
```

Key variables (see `backend/config.py` for defaults):

- `COLPALI_MODE`, `COLPALI_CPU_URL`, `COLPALI_GPU_URL`, `COLPALI_API_TIMEOUT`  
- `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, `QDRANT_USE_BINARY`, `QDRANT_PREFETCH_LIMIT`  
- `MINIO_URL`, `MINIO_PUBLIC_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

## Run the Service

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

Prefer the legacy entry point?

```bash
python backend/main.py
```

Automatic OpenAPI docs are served at http://localhost:8000/docs.

## Docker Compose Workflow

The root `docker-compose.yml` brings up Qdrant, MinIO, the Morty backend, and the Morty frontend. Default container environment variables are configured for host-based ColPali services:

- `COLPALI_CPU_URL=http://host.docker.internal:7001`  
- `COLPALI_GPU_URL=http://host.docker.internal:7002`  
- `QDRANT_URL=http://qdrant:6333`  
- `MINIO_URL=http://minio:9000`  
- `MINIO_PUBLIC_URL=http://localhost:9000`

Launch everything with:

```bash
docker compose up -d --build
```

MinIO credentials remain mandatory; Morty continues to rely on object storage for generated page images.

## API Surface

### Meta
- `GET /health` – Check Morty’s dependency status.

### Retrieval
- `GET /search?q=...&k=5` – Perform page-level searches (defaults to 10 results when `k` is omitted).

### Indexing
- `POST /index` – Upload one or more PDFs for ingestion.  
- `GET /progress/stream/{job_id}` – Receive live Server-Sent Events while indexing.  
- `POST /index/cancel/{job_id}` – Cancel a running ingestion job.

### Maintenance
- `GET /status` – Inspect Qdrant and MinIO statistics.  
- `POST /initialize` – Provision the collection and bucket.  
- `DELETE /delete` – Remove both resources.  
- `POST /clear/qdrant`, `POST /clear/minio`, `POST /clear/all` – Perform targeted resets with audit details.

### Configuration
- `GET /config/schema`, `GET /config/values` – Review typed schema metadata and active values.  
- `POST /config/update`, `POST /config/reset`, `POST /config/optimize` – Tune runtime values, revert to defaults, or let Morty auto-tune based on detected hardware.

## Chat and Visual Citations

The Morty backend focuses on retrieval and system management. Chat streaming continues to live in `frontend/app/api/chat/route.ts`, which calls the backend search endpoint, forwards context to the OpenAI Responses API, and streams updates to the client.

## Configuration UI

The `/configuration` page in the Morty frontend interacts with the endpoints above to provide:

- Typed inputs with validation  
- Draft detection when browser overrides diverge from server state  
- Smart cache invalidation for configuration changes that affect search

Runtime changes remain ephemeral. Persist long-term adjustments in `.env`.

## Migration Notes

- No API signatures changed as part of the Morty rebrand. Client SDKs and automation scripts continue to operate.  
- Morty introduces new documentation (`MIGRATION.md`, `TRADEMARKS.md`) to explain the pro-bono collaboration and branding guidelines.  
- Review `LICENSES/SNAPPY_MIT_LICENSE.txt` to see the preserved upstream MIT License.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
