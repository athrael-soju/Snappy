# Snappy - FastAPI x Next.js visual RAG template

Snappy gives you a ready-to-run multimodal retrieval stack. Drop in PDFs or image-heavy docs, and you get ingestion, visual search, and chat with page previews. The goal: ship an approachable developer experience without wrestling gradients or bespoke UI chrome.

- **Backend** - FastAPI with pipelined ingestion, Qdrant search, MinIO optional for image storage.
- **Frontend** - Next.js 15, Tailwind v4, shadcn, and Framer Motion for lightweight interactions.
- **Embeddings** - ColQwen2.5 (a ColPali-style model) so Snappy understands layout, charts, and screenshots.

Repository layout:

- `backend/` - FastAPI app, config schema, services
- `frontend/` - Next.js App Router UI
- `colpali/` - ColQwen2.5 embedding service (CPU/GPU docker-compose)
- `image/` - Reference assets (optional)
- `docker-compose.yml`

---
## Highlights

- **Simple UI** - shadcn components, Tailwind tokens, no animated gradients. Focus on clarity and responsive layouts.
- **Upload flow** - drag & drop, SSE progress, cancel support.
- **Visual search** - natural language + layout-aware retrieval, inline previews.
- **Chat** - streaming answers with the relevant page thumbnails, adjustable `k`, top-k, and tool calling.
- **Maintenance tab** - initialise collections/buckets, reset data, and edit backend config from the browser.

---

## Quick start

### 1. Backend (FastAPI)

Prereqs: Python 3.11+, [Poppler](https://poppler.freedesktop.org/) for `pdf2image`.

```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1  # or source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (Next.js)

```powershell
cd frontend
yarn install --frozen-lockfile
yarn dev
# open http://localhost:3000
```

If you prefer npm:

```powershell
npm install
npm run dev
```

Configure the API base URL in `frontend/.env.local` (defaults to `http://localhost:8000`):

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Embedding service

Snappy talks to a ColQwen2.5 service for visual embeddings. You can run the provided docker compose (CPU or GPU):

```powershell
cd colpali
docker compose up -d
```

Set backend env vars if you expose the service elsewhere:

```
COLPALI_MODE=cpu          # or gpu
COLPALI_CPU_URL=http://localhost:7001
COLPALI_GPU_URL=http://localhost:7002
```

---

## Docker workflow

Run everything with one command from the repository root:

```powershell
docker compose up -d --build
```

The compose file spins up Qdrant, MinIO, backend, frontend, and the ColPali service. Supply OpenAI credentials to the frontend container if you plan to use chat streaming:

```yaml
services:
  frontend:
    environment:
      - OPENAI_API_KEY=sk-your-key
      - OPENAI_MODEL=gpt-5-mini
      - OPENAI_TEMPERATURE=1
      - OPENAI_MAX_TOKENS=1500
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
```

`OPENAI_*` are read server-side by the Next.js API route (`frontend/app/api/chat/route.ts`).

---

## Frontend checklist

| Path | Purpose |
|------|---------|
| `/` | Landing with quick CTAs for upload, search, chat |
| `/upload` | Drag-and-drop ingest, SSE progress, cancel support |
| `/search` | Visual search, example queries, inline galleries |
| `/chat` | Streaming assistant with page thumbnails and adjustable settings |
| `/maintenance` | Initialisation, data reset, configuration editor |
| `/about` | Project overview and stack primer |

The frontend uses OpenAPI-generated SDKs (`yarn gen:sdk && yarn gen:zod`), stored in `frontend/lib/api/generated`.

---

## Maintenance & configuration

The Maintenance tab exposes backend configuration over HTTP:

- `GET /config/schema` – schema with metadata, defaults, and validation.
- `GET /config/values` – live values.
- `POST /config/update` – runtime updates (non-persistent).
- `POST /config/reset` – revert to defaults.

Sections cover application, processing, embedding service, Qdrant, MinIO, and MUVERA options. Changes apply immediately but do **not** patch `.env`; update your environment files for persistent tweaks.

Use the same page to initialise or delete the Qdrant collection and MinIO bucket.

---

## Backend overview

- `backend/main.py` – API router.
- `backend/services/` – clients for ColPali, Qdrant, MinIO.
- `backend/runtime_config.py` – local cache of runtime overrides.
- `backend/config_schema.py` – strongly typed configuration schema.

Key endpoints:

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/index` | Ingest documents (multipart upload) |
| `GET` | `/progress/stream/{job_id}` | SSE progress feed |
| `GET` | `/search` | Visual search (`q`, optional `k`) |
| `POST` | `/chat` (Next.js route) | Uses backend search + OpenAI responses |
| `GET` | `/status` | Collection/bucket stats |
| `POST` | `/initialize` / `/delete` | Provision or tear down infrastructure |
| `POST` | `/config/update` | Runtime config |

See `backend/docs` for deeper dives (architecture, analysis, configuration guide).

---

## Testing ideas & next steps

- Add auth, rate limiting, or tenancy for production.
- Hook in tracing/observability (OpenTelemetry, Prometheus).
- Swap in your own embedding pipeline or RAG orchestration.
- Build deploy manifests (Terraform, Helm) for your environment.

---

## License

MIT © the Snappy contributors.
