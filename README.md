# ColPali (ColQwen2) Knowledgebase Retrieval Agent

A lightweight Gradio app for page-level retrieval over PDFs using an external ColQwen embeddings API, with optional vector storage in Qdrant and image storage in MinIO. No local GPU or PyTorch is required.

## Features
- API-first: uses an external ColQwen API for embeddings (`services/colqwen_api_client.py`).
- Two storage modes:
  - In-memory (quick demos)
  - Qdrant + MinIO (persistent, scalable)
- Gradio UI with streaming OpenAI chat for answer generation.

## Repository Structure
- `app.py` – Gradio UI and app wiring
- `config.py` – Centralized configuration via environment variables
- `services/` – Integration layers
  - `colqwen_api_client.py` – Client for the external ColQwen API
  - `qdrant_store.py` – Qdrant-backed store using the API for embeddings
  - `minio_service.py` – MinIO image storage utilities
  - `memory_store.py` – In-memory store using the API
- `docker-compose.yml` – Qdrant, MinIO, and the app container
- `Dockerfile` – Slim Python base (no CUDA/PyTorch)
- `requirements.txt` – Python dependencies
- `.env.example` – Example environment variables

## Prerequisites
- Docker and Docker Compose
- An accessible ColQwen embeddings API endpoint
  - Example base URL: `http://localhost:8000` (host machine) or `http://host.docker.internal:8000` (from inside Docker on Mac/Windows)
- Optional: OpenAI API key for chat completion

## Quick Start (Docker Compose)
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` as needed. Key settings:
   - `COLQWEN_API_BASE_URL=http://host.docker.internal:8000` (Mac/Windows)
     - On Linux, use your host IP or add to compose: `extra_hosts: ["host.docker.internal:host-gateway"]` under the `vision-rag` service.
   - `STORAGE_TYPE=qdrant` (default) or `memory`
   - `OPENAI_API_KEY` if you want AI answers (otherwise you can disable AI responses in the UI or leave the key empty)
3. Start services:
   ```bash
   docker compose up -d --build
   ```
4. Open the app: http://localhost:7860

Services started by Compose:
- Qdrant: http://localhost:6333
- MinIO: http://localhost:9001 (console), S3 API at http://localhost:9000 (user: `minioadmin`, pass: `minioadmin`)

## Local (No Docker)
1. Install system dependencies:
   - Poppler (for `pdf2image`). On macOS: `brew install poppler`. On Linux: your package manager. On Windows: install Poppler and set `POPPLER_PATH` in `.env`.
2. Python deps:
   ```bash
   python -m venv .venv
   . .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -U pip
   pip install -r requirements.txt
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   # edit .env to point COLQWEN_API_BASE_URL to your API
   ```
4. Run the app:
   ```bash
   python app.py
   ```
   Visit http://localhost:7860.

## Configuration
All settings come from environment variables (see `.env.example` and `config.py`). Notable keys:
- Core
  - `HOST`, `PORT`
  - `LOG_LEVEL`
- ColQwen API
  - `COLQWEN_API_BASE_URL` – Base URL of the external embeddings API
  - `COLQWEN_API_TIMEOUT` – Request timeout (seconds)
- OpenAI
  - `OPENAI_API_KEY`, `OPENAI_MODEL`
- Storage
  - `STORAGE_TYPE` – `memory` or `qdrant`
  - Qdrant: `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, `QDRANT_SEARCH_LIMIT`, `QDRANT_PREFETCH_LIMIT`
  - MinIO: `MINIO_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME`, `MINIO_WORKERS`, `MINIO_RETRIES`, `MINIO_FAIL_FAST`, `MINIO_IMAGE_FMT`
  - In-memory: `IN_MEMORY_NUM_IMAGES`
- Windows:
  - `POPPLER_PATH` – Path to Poppler binaries for `pdf2image`

## Notes on the API Migration
- The Dockerfile no longer installs CUDA/PyTorch; embeddings are obtained from the external API.
- `services/colqwen_api_client.py` handles all embeddings operations:
  - `embed_queries`, `embed_images`, and `get_patches`
- `services/qdrant_store.py` and `services/memory_store.py` are updated to rely on the API client.

## Troubleshooting
- App shows "API not available" errors:
  - Verify `COLQWEN_API_BASE_URL` is reachable from inside the container.
  - On Mac/Windows Docker, prefer `http://host.docker.internal:8000`.
  - On Linux, add `extra_hosts: ["host.docker.internal:host-gateway"]` to `vision-rag` in `docker-compose.yml` or use your host IP.
- PDFs fail to convert:
  - Ensure Poppler is installed. On Windows, set `POPPLER_PATH` in `.env`.
- MinIO access issues:
  - Check the console at http://localhost:9001. The app auto-creates the bucket and a public-read policy.

## License
Apache-2.0. See `LICENSE`.
