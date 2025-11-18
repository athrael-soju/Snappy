# Snappy Agent Guide 🤖

This document provides high-level context, architectural summaries, and development rules for AI agents working on the Snappy codebase.

---

## 🧠 Project Overview

Snappy is a **vision-grounded document retrieval system** (RAG) that processes PDFs as images.
*   **Core Idea**: Embed page images directly using ColPali (multivector) instead of relying solely on OCR text.
*   **Hybrid Mode**: Optionally uses DeepSeek OCR for text extraction and bounding boxes, combining vision and text search.
*   **Stack**: FastAPI (Backend), Next.js 16 (Frontend), Qdrant (Vector DB), MinIO (Storage), DuckDB (Analytics).

## 📂 Key Directories

*   `backend/` - FastAPI application (Python 3.11+).
    *   `api/` - Routers and app entry point.
    *   `clients/` - Integrations (Qdrant, MinIO, ColPali, OCR, DuckDB).
    *   `domain/` - Core logic (Pipeline, Batch Processing).
    *   `config/` - Schema-driven configuration.
*   `frontend/` - Next.js application (TypeScript, React 19).
    *   `app/` - App router pages and API routes.
    *   `lib/api/` - Generated OpenAPI client.
    *   `components/` - UI components (shadcn/ui based).
*   `colpali/` - Embedding service (Python/FastAPI).
*   `deepseek-ocr/` - OCR service (Python/FastAPI).

## 🛠️ Development Workflow

### Backend
*   **Manager**: `uv` (preferred) or `pip`.
*   **Run**: `uvicorn backend.main:app --reload` (Port 8000).
*   **Test**: `pytest tests/`.
*   **Lint**: `pre-commit run --all-files`.

### Frontend
*   **Manager**: `yarn`.
*   **Run**: `yarn dev` (Port 3000).
*   **Gen SDK**: `yarn gen:sdk` (after backend API changes).

### Docker
*   **Full Stack**: `docker compose --profile gpu up -d` (or `--profile cpu`).
*   **Services**: `colpali`, `deepseek-ocr`, `qdrant`, `minio`, `duckdb`.

## 📏 Coding Standards

### General
*   **Robustness**: Implement changes robustly. Avoid temporary shims unless requested.
*   **Cleanup**: Remove unused files/code after refactoring.
*   **Communication**: Ask clarifying questions if instructions are ambiguous.

### Backend (Python)
*   **Style**: PEP 8, Black formatting, isort.
*   **Types**: Full type hinting required (enforced by Pyright).
*   **Async**: Use `async/await` for I/O.
*   **API**: Update `backend/config_schema.py` for new settings. Rerun `scripts/generate_openapi.py` if routes change.

### Frontend (TypeScript)
*   **Style**: Prettier, ESLint.
*   **Types**: Strict TypeScript. No `any`.
*   **API**: Use the generated SDK (`@/lib/api/generated`) for all backend calls. Do not use `fetch` directly.
*   **State**: Use `stores/app-store.tsx` and domain-specific hooks.

## 🔄 Common Tasks

*   **New Config**: Add to `backend/config/schema/`, update `.env.example`.
*   **New Endpoint**: Add router in `backend/api/routers/`, include in `backend/api/app.py`, regen SDK.
*   **Job Cancellation**: Handled by `CancellationService` in `backend/domain/pipeline/cancellation.py`.

---

*Ref: `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`*
