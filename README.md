<p align="center">
  <img width="754" height="643" alt="snappy_light_nobg_resized" src="https://github.com/user-attachments/assets/2ebd2908-42a7-46d4-84a1-cad8aeca1847" style="background-color: white;" />
</p>

---

# Snappy – Vision-Grounded Document Retrieval 📸

<!-- Project Stats -->
[![GitHub Release](https://img.shields.io/github/v/release/athrael-soju/Snappy?include_prereleases&sort=semver&display_name=tag&style=flat-square&logo=github&color=blue)](https://github.com/athrael-soju/Snappy/releases)
[![GitHub Stars](https://img.shields.io/github/stars/athrael-soju/Snappy?style=flat-square&logo=github&color=yellow)](https://github.com/athrael-soju/Snappy/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/athrael-soju/Snappy?style=flat-square&logo=github&color=green)](https://github.com/athrael-soju/Snappy/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/athrael-soju/Snappy?style=flat-square&logo=github&color=red)](https://github.com/athrael-soju/Snappy/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

<!-- Build & Quality -->
[![CI/CD](https://img.shields.io/github/actions/workflow/status/athrael-soju/Snappy/release-please.yml?style=flat-square&logo=githubactions&label=CI%2FCD)](https://github.com/athrael-soju/Snappy/actions)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/athrael-soju/Snappy/codeql.yml?style=flat-square&logo=github&label=CodeQL)](https://github.com/athrael-soju/Snappy/security/code-scanning)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen?style=flat-square&logo=codacy)](https://github.com/athrael-soju/Snappy)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square&logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Tech Stack -->
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-000000?style=flat-square&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-ff6b6b?style=flat-square&logo=qdrant)](https://qdrant.tech/)
[![MinIO](https://img.shields.io/badge/Storage-MinIO-f79533?style=flat-square&logo=minio)](https://min.io/)
[![Docker](https://img.shields.io/badge/Orchestration-Docker-2496ed?style=flat-square&logo=docker)](https://docs.docker.com/compose/)

Snappy pairs a FastAPI backend, a ColPali embedding service, and a Next.js frontend to deliver vision-first retrieval over PDFs. Each page is rasterised, embedded as multivectors, and stored alongside images so you can search by how documents look—not just by extracted text.

> Component docs:
> - Backend: `backend/README.md`
> - Frontend: `frontend/README.md`
> - ColPali service: `colpali/README.md`
> - Configuration reference: `backend/docs/configuration.md`
> - **Version management: `VERSIONING.md`**

---

## Architecture

```mermaid
---
config:
  theme: neutral
  layout: elk
---
flowchart TB
  subgraph Frontend["Next.js Frontend"]
    UI["Pages (/upload, /search, /chat, /configuration, /maintenance)"]
    CHAT["Chat API Route"]
  end

  subgraph Backend["FastAPI Backend"]
    API["REST Routers"]
  end

  subgraph Services["Supporting Services"]
    QDRANT["Qdrant"]
    MINIO["MinIO"]
    COLPALI["ColPali Embedding API"]
    OPENAI["OpenAI Responses API"]
  end

  USER["Browser"] <--> UI
  UI --> API
  API --> QDRANT
  API --> MINIO
  API --> COLPALI
  CHAT --> API
  CHAT --> OPENAI
  CHAT -- SSE --> USER
```

Head to `backend/docs/architecture.md` and `backend/docs/analysis.md` for a deeper walkthrough of the indexing and retrieval flows.

---

## Highlights

- 🎯 Page-level vision retrieval powered by ColPali multivector embeddings—no OCR pipeline to maintain.
- 💬 Streaming chat responses from the OpenAI Responses API with inline visual citations so you can see each supporting page.
- ⚡ Pipelined indexing with live Server-Sent Events progress updates and optional MUVERA-assisted first-stage search.
- 🎛️ Runtime configuration UI backed by a typed schema, with reset/draft flows that make experimentation safe.
- 🐳 Docker Compose profiles for ColPali (GPU or CPU) plus an all-in-one stack for local development.

---

## Frontend Experience

The Next.js 16 frontend with React 19.2 keeps things fast and friendly: real-time streaming, responsive layouts, and design tokens (`text-body-*`, `size-icon-*`) that make extending the UI consistent. Configuration and maintenance pages expose everything the backend can do, while upload/search/chat give you the workflows you need day to day.

---

## Demo

https://github.com/user-attachments/assets/99438b0d-c62e-4e47-bdc8-623ee1d2236c

---

## Quick Start

> 🚀 **Using Pre-built Images?** Skip to [Option A](#option-a--run-with-pre-built-docker-images) for the fastest deployment using our pre-built containers from GitHub Container Registry.

### 1. Prepare environment files

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Add your OpenAI API key to `frontend/.env.local` and review the backend defaults in `.env`.

### 2. Start the ColPali embedding service

From `colpali/` pick one profile:

```bash
# GPU profile (CUDA + flash-attn tooling)
docker compose --profile gpu up -d --build

# CPU profile (no GPU dependencies)
docker compose --profile cpu up -d --build
```

Only start one profile at a time to avoid port clashes. The first GPU build compiles `flash-attn`; subsequent builds reuse the cached wheel.

---

### Option A – Run with Pre-built Docker Images

Use our pre-built images from GitHub Container Registry for instant deployment:

```bash
# Pull pre-built images
docker pull ghcr.io/athrael-soju/Snappy/backend:latest
docker pull ghcr.io/athrael-soju/Snappy/frontend:latest
docker pull ghcr.io/athrael-soju/Snappy/colpali-cpu:latest

# Create minimal docker-compose.yml (see docs/DOCKER_IMAGES.md)
# Then start services
docker compose up -d
```

**Available images:**
- `backend:latest` - FastAPI backend (amd64/arm64)
- `frontend:latest` - Next.js frontend (amd64/arm64)
- `colpali-cpu:latest` - CPU embedding service (amd64/arm64)
- `colpali-gpu:latest` - GPU embedding service (amd64 only)

📖 **Full guide**: See [`docs/DOCKER_IMAGES.md`](docs/DOCKER_IMAGES.md) for complete documentation on using pre-built images, version tags, configuration, and production deployment examples.

---

### Option B – Run the full stack with Docker Compose (Build from Source)

At the project root:

```bash
docker compose up -d --build
```

Services will come online at:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Qdrant: http://localhost:6333
- MinIO: http://localhost:9000 (console at :9001)

Update `.env` and `frontend/.env.local` if you need to expose different hostnames or ports.

---

### Option C – Run services locally

1. In `backend/`, install dependencies and launch FastAPI:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
   pip install -U pip setuptools wheel
   pip install -r backend/requirements.txt
   uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Start Qdrant and MinIO (via Docker or your preferred deployment).

3. In `frontend/`, install and run the Next.js app:

   ```bash
   yarn install --frozen-lockfile
   yarn dev
   ```

4. Keep the ColPali service from step 2 running (Docker or `uvicorn colpali/app.py`).

---

## Environment Variables

### Backend highlights

- `COLPALI_URL`, `COLPALI_API_TIMEOUT`
- `QDRANT_EMBEDDED`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, `QDRANT_PREFETCH_LIMIT`, `QDRANT_MEAN_POOLING_ENABLED`, optional quantisation toggles
- `MINIO_URL`, `MINIO_PUBLIC_URL`, credentials, bucket naming, `IMAGE_FORMAT`, `IMAGE_QUALITY`
- `MUVERA_ENABLED` and related settings (requires `fastembed[postprocess]` in your environment)
- `LOG_LEVEL`, `ALLOWED_ORIGINS`, `UVICORN_RELOAD`

All schema-backed settings (and defaults) are documented in `backend/docs/configuration.md`. Runtime updates via `/config/update` are ephemeral; update `.env` for persistence.

### Frontend highlights (`frontend/.env.local`)

- `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)
- `OPENAI_API_KEY`, `OPENAI_MODEL`, optional `OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS`

---

## API Overview

| Area         | Endpoint(s)                              | Notes |
|--------------|------------------------------------------|-------|
| Meta         | `GET /health`                            | Service and dependency status |
| Retrieval    | `GET /search?q=...&k=5`                  | Page-level search (defaults to 10 when `k` omitted) |
| Indexing     | `POST /index`                            | Background indexing job (multipart PDF upload) |
|              | `GET /progress/stream/{job_id}`          | Real-time progress (SSE) |
|              | `POST /index/cancel/{job_id}`            | Cancel an active job |
| Maintenance  | `GET /status`                            | Collection/bucket statistics |
|              | `POST /initialize`, `DELETE /delete`     | Provision or tear down collection + bucket |
|              | `POST /clear/qdrant`, `/clear/minio`, `/clear/all` | Data reset helpers |
| Configuration| `GET /config/schema`, `/config/values`   | Expose runtime schema and values |
|              | `POST /config/update`, `/config/reset`   | Runtime configuration management |

Chat streaming lives in `frontend/app/api/chat/route.ts`. The route calls the backend search endpoint, invokes the OpenAI Responses API, and streams Server-Sent Events to the browser. The backend does not proxy OpenAI calls.

---

## Troubleshooting

- **ColPali timing out?** Increase `COLPALI_API_TIMEOUT` or run the GPU profile for heavy workloads.
- **Progress bar stuck?** Ensure Poppler is installed and check backend logs for PDF conversion errors.
- **Missing images?** Verify MinIO credentials/URLs and confirm `next.config.ts` allows the domains you expect.
- **CORS issues?** Replace wildcard `ALLOWED_ORIGINS` entries with explicit URLs before exposing the API publicly.
- **Config changes vanish?** `/config/update` modifies runtime state only—update `.env` for anything you need to keep after a restart.
- **Upload rejected?** The uploader currently accepts PDFs only. Adjust max size, chunk size, or file count limits in the “Uploads” section of the configuration UI.

`backend/docs/configuration.md` and `backend/CONFIGURATION_GUIDE.md` cover advanced troubleshooting and implementation details.

---

## Developer Notes

- Background indexing uses FastAPI `BackgroundTasks`. For larger deployments consider a dedicated task queue.
- MinIO worker pools auto-size based on hardware. Override only when you have specific throughput limits.
- TypeScript types and Zod schemas regenerate from the OpenAPI spec (`yarn gen:sdk`, `yarn gen:zod`) to keep the frontend in sync.
- Pre-commit hooks (autoflake, isort, black, pyright) keep the codebase tidy—run them before contributing.
- **Version management:** Uses Release Please + Conventional Commits for automated releases. See `VERSIONING.md` for details.

---

## Further Reading

- `backend/docs/analysis.md` – vision vs. text RAG comparison
- `backend/docs/architecture.md` – collection, indexing, and search deep dive
- `colpali/README.md` – details on the standalone embedding service

---

## License

MIT License – see [LICENSE](LICENSE).

---

## Acknowledgements

Snappy builds on the work of:

- **ColPali / ColModernVBert** – multimodal models for visual retrieval  
  📄 https://arxiv.org/abs/2407.01449
  📄 https://arxiv.org/abs/2510.01149

- **Qdrant** – the vector database powering multivector search  
  📚 https://qdrant.tech/blog/colpali-qdrant-optimization/  
  📚 https://qdrant.tech/articles/binary-quantization/  
  📚 https://qdrant.tech/articles/muvera-embeddings/

- **PyTorch** – core deep learning framework  
  🔥 https://pytorch.org/  

