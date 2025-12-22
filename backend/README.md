# Snappy Backend - FastAPI Service

FastAPI service for PDF ingestion, vision-grounded search, optional OCR, runtime config, and maintenance.

## Project Structure
The backend follows a layered architecture to separate concerns:
- **`api/`**: FastAPI routers and HTTP handling. Delegates all business logic to the Domain layer.
- **`domain/`**: Core business logic, orchestration, and rules. Pure Python code, independent of HTTP frameworks.
- **`clients/`**: Infrastructure adapters for external services (Local Storage, Qdrant, OCR).
- **`config/`**: Configuration schemas and loading logic.

## Quick start
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Prereqs: Python 3.11+ and Poppler (`pdftoppm`) on PATH.

## Docker
- Backend only (Qdrant): `cd backend && docker compose up -d --build`
- Full stack (from repo root): `docker compose up -d`

Use container hostnames inside Compose (`http://colpali:7000`, `http://deepseek-ocr:8200`). From host, use `localhost`.

## Essential settings
Set in `.env`; see `docs/configuration.md` for the full list.
- ColPali: `COLPALI_URL`, `COLPALI_API_TIMEOUT`
- OCR: `DEEPSEEK_OCR_ENABLED`, `DEEPSEEK_OCR_URL`
- Qdrant: `QDRANT_URL`, `QDRANT_COLLECTION_NAME`
- Local Storage: `LOCAL_STORAGE_PATH`, `LOCAL_STORAGE_PUBLIC_URL`

## API basics
- Health: `GET /health`
- Search: `GET /search?q=...&k=5`
- Index: `POST /index` (multipart PDF upload) with progress at `/progress/stream/{job_id}` or `/progress/{job_id}`
- Cancel: `POST /index/cancel/{job_id}`
- OCR (when enabled): `POST /ocr/process-page`, `/ocr/process-batch`, `/ocr/process-document`; progress at `/ocr/progress/stream/{job_id}`
- Maintenance: `/status`, `/initialize`, `/delete`, `/clear/*`
- Config UI/API: `/config/schema`, `/config/values`, `/config/update`, `/config/reset`
Interactive docs: http://localhost:8000/docs

## Cancellation overview
- Stops running indexing/OCR, optional service restarts.
- Cleans Qdrant vectors, stored files, temp files.
- Reports progress over `/progress/stream/{job_id}`.
Configure with `JOB_CANCELLATION_*` vars; see `backend/docs/configuration.md`.

## Notes
- ColPali auto-detects CUDA, MPS, or CPU; OCR requires NVIDIA GPU.
- Use `backend/docs/architecture.md`, `STREAMING_PIPELINE.md`, and `backend/docs/analysis.md` for flow and mode details.
