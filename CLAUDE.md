# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Overview

Snappy is a vision-grounded document retrieval system that uses ColPali multivector embeddings to search PDFs by visual appearance rather than just text. The system consists of a FastAPI backend, Next.js 16 frontend with React 19.2, and supporting services (Qdrant vector DB, MinIO storage, ColPali embeddings, optional DeepSeek OCR, optional DuckDB analytics).

**Tech Stack:**
- Backend: FastAPI (Python 3.11+, async/await)
- Frontend: Next.js 16 App Router + React 19.2 (TypeScript)
- Package Managers: `uv` (Python), `yarn` (Node.js)
- Services: Qdrant, MinIO, ColPali, DeepSeek OCR (optional), DuckDB (optional)

---

## Critical Terminal Usage

**USE THE CORRECT TERMINAL FOR EACH COMPONENT:**

| Component | Terminal | Package Manager | Virtual Env |
|-----------|----------|-----------------|-------------|
| Backend | WSL | `uv` | `backend/.venv` |
| ColPali Service | WSL | `uv` | `colpali/.venv` |
| DeepSeek OCR | WSL | `pip` | `deepseek-ocr/.venv` |
| Frontend | bash/PowerShell | `yarn` | N/A |

**Common Mistake:** Running frontend commands in WSL or backend commands in bash/PowerShell will cause package manager conflicts.

---

## Common Commands

### Backend (WSL terminal)

```bash
# Setup
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run development server
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Pre-commit hooks (autoflake, isort, black, pyright)
pre-commit run --all-files

# Generate OpenAPI spec (from project root)
cd ..
uv run python scripts/generate_openapi.py
```

### Frontend (bash/PowerShell terminal)

```bash
# Setup
cd frontend
yarn install --frozen-lockfile

# Development
yarn dev

# Build
yarn build
yarn start

# Type generation (after API changes)
yarn gen:sdk    # Generate TypeScript types from OpenAPI
yarn gen:zod    # Generate Zod schemas from OpenAPI

# Type checking
yarn type-check
```

### Docker

```bash
# Full stack (choose one profile)
docker compose --profile cpu up -d --build
docker compose --profile gpu up -d --build

# View logs
docker compose logs -f [service_name]

# Individual services
docker compose up -d qdrant minio backend frontend
```

---

## Architecture

### Layer Separation

```
Routers (HTTP handlers)
    ↓
Dependencies (cached service instances)
    ↓
Services (business logic)
    ↓
External APIs/DBs (Qdrant, MinIO, ColPali, DeepSeek OCR, DuckDB)
```

### Key Directories

```
backend/
├── api/
│   ├── routers/          # HTTP endpoints (config, duckdb, indexing, maintenance, meta, ocr, retrieval)
│   ├── dependencies.py   # Service instances with @lru_cache
│   ├── progress.py       # SSE job tracking
│   └── models.py         # Pydantic request/response models
├── services/
│   ├── qdrant/          # Vector DB operations (collection, search, indexing, embedding)
│   ├── pipeline/        # DB-agnostic indexing pipeline (batch_processor, document_indexer, progress, storage)
│   ├── ocr/            # DeepSeek OCR integration (processor, service, storage)
│   ├── minio.py        # S3-compatible object storage
│   ├── colpali.py      # Embedding service client
│   ├── duckdb.py       # Analytics service client
│   └── image_processor.py  # PDF rasterization
├── config_schema/       # Schema-driven configuration (application, colpali, deepseek_ocr, duckdb, minio, qdrant, upload)
├── config.py            # Runtime config access with lazy __getattr__
└── runtime_config.py    # Thread-safe runtime config storage

frontend/
├── app/                 # Next.js 16 App Router pages
│   ├── api/chat/       # SSE streaming chat endpoint (Edge runtime)
│   ├── upload/         # Document upload page
│   ├── search/         # Visual search page
│   ├── chat/           # Chat interface
│   ├── configuration/  # Runtime config UI
│   └── maintenance/    # System status and data management
├── components/
│   ├── ui/             # shadcn/ui components
│   └── chat/           # Chat-specific components
├── lib/
│   ├── api/            # API client wrapper (generated types)
│   └── hooks/          # Custom React hooks
└── stores/             # Zustand state management

colpali/                # Standalone embedding service
deepseek-ocr/          # Standalone OCR service (GPU only)
duckdb/                # Standalone analytics service
```

### Data Flows

**Indexing:** PDF upload → **Deduplication check (DuckDB)** → Backend rasterizes → BatchProcessor (embeds via ColPali, stores images in MinIO, optional OCR via DeepSeek with UUID naming) → QdrantIndexer upserts vectors → **Document metadata stored (DuckDB)** → SSE progress updates

**Search:** User query → Backend embeds via ColPali → SearchManager (two-stage: pooled vectors prefetch + multivector rerank) → Results with MinIO image URLs → Optional OCR data from DuckDB

**Chat:** User message → Next.js chat API route → Backend search → OpenAI Responses API → SSE stream to browser (text-delta + kb.images events)

**OCR:** Page/document request → Backend fetches images from MinIO → DeepSeek OCR service (adjustable workers) → UUID-named results stored in MinIO → **OCR metadata stored in pages/regions tables (DuckDB)** → SSE progress for documents

---

## Configuration System

Configuration is **schema-driven** with three layers:

1. **Schema** (`backend/config_schema/`): Modular schema files (application, colpali, deepseek_ocr, duckdb, minio, qdrant, upload) defining defaults, types, UI metadata, and critical keys
2. **Runtime Store** (`backend/runtime_config.py`): Thread-safe in-memory storage with error tracking
3. **Access Layer** (`backend/config.py`): Lazy `__getattr__` for dynamic lookup with type coercion

**Critical Pattern:** When a setting marked as "critical" changes via `/config/update`, `invalidate_services()` in `backend/api/dependencies.py` clears all `@lru_cache` decorated service factories to force re-instantiation with new values. Thread-safe error tracking ensures initialization failures are reported properly.

**Important:** Runtime updates via `/config/update` are ephemeral. Update `.env` file for persistence across restarts.

---

## Common Patterns

### Adding a New Endpoint

1. Create router in `backend/api/routers/my_feature.py`:
```python
from fastapi import APIRouter, Depends
from ..dependencies import get_my_service
from ..models import MyRequest, MyResponse

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post("/action", response_model=MyResponse)
async def perform_action(
    request: MyRequest,
    service = Depends(get_my_service)
):
    result = await service.do_something(request.data)
    return MyResponse(result=result)
```

2. Register in `backend/api/app.py`:
```python
from .routers import my_feature
app.include_router(my_feature.router)
```

3. Regenerate types:
```bash
# WSL
uv run python scripts/generate_openapi.py

# bash
cd frontend
yarn gen:sdk
yarn gen:zod
```

### Background Tasks with Progress

```python
from fastapi import BackgroundTasks
from ..progress import JobManager, ProgressUpdate

job_manager = JobManager()

@router.post("/long-task")
async def start_task(background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(process_task, job_id)
    return {"job_id": job_id}

async def process_task(job_id: str):
    try:
        for i in range(100):
            # Do work
            job_manager.update(job_id, ProgressUpdate(
                stage="processing",
                percent=i,
                message=f"Step {i}/100"
            ))
        job_manager.complete(job_id)
    except Exception as e:
        job_manager.fail(job_id, str(e))

@router.get("/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    return EventSourceResponse(job_manager.stream(job_id))
```

### Adding Configuration

1. Add to appropriate schema file in `backend/config_schema/` (e.g., `my_feature.py`):
```python
def get_my_feature_schema() -> dict:
    return {
        "order": 10,
        "icon": "settings",
        "name": "My Feature",
        "description": "Feature description",
        "settings": [
            {
                "key": "MY_SETTING",
                "type": "str",
                "default": "default_value",
                "label": "My Setting",
                "description": "Setting description",
                "help_text": "Detailed help text",
                "critical": False,  # Set True to trigger service cache invalidation
            }
        ]
    }
```

Then register it in `backend/config_schema/__init__.py`:
```python
from .my_feature import get_my_feature_schema

def get_full_schema() -> dict:
    return {
        # ... existing schemas ...
        "my_feature": get_my_feature_schema(),
    }
```

2. Access in code:
```python
from backend.config import config
value = config.MY_SETTING  # Dynamic lookup via __getattr__
```

3. If critical, add to cache invalidation in `backend/api/dependencies.py`:
```python
def invalidate_services():
    get_my_service.cache_clear()
    # ... other services
```

### Service with Dependency Injection

```python
# backend/api/dependencies.py
from functools import lru_cache
from ..services.my_service import MyService

@lru_cache(maxsize=1)
def get_my_service() -> MyService:
    return MyService(
        setting1=config.MY_SETTING_1,
        setting2=config.MY_SETTING_2
    )
```

---

## Frontend Patterns

### Type-Safe API Calls

**IMPORTANT:** Always use the generated SDK from `lib/api/generated` instead of manual `fetch()` calls.

```typescript
// ✅ CORRECT - Use generated service
import { RetrievalService, ConfigurationService } from '@/lib/api/generated';

// Search documents
const results = await RetrievalService.searchSearchGet(query, k, includeOcr);

// Update configuration
await ConfigurationService.updateConfigConfigUpdatePost({
  key: 'MY_SETTING',
  value: 'new_value'
});

// ❌ INCORRECT - Don't use manual fetch
const response = await fetch(`${baseUrl}/search?q=${query}`);
```

**Why use generated SDK:**
- ✅ Type safety - Compile-time checking of requests/responses
- ✅ Consistency - Single source of truth for API contracts
- ✅ Maintainability - API changes only require regenerating types
- ✅ Error handling - Built-in `ApiError` with status codes

**Available Services:**
- `RetrievalService` - Document search
- `ConfigurationService` - Runtime config management
- `MaintenanceService` - System status and operations
- `IndexingService` - Document upload/indexing
- `OcrService` - OCR processing
- `DuckdbService` - Analytics queries
- `MetaService` - Health checks

**Regenerating after backend changes:**
```bash
# Backend: Generate OpenAPI schema
cd backend
uv run python ../scripts/generate_openapi.py

# Frontend: Generate TypeScript SDK
cd ../frontend
yarn gen:sdk
```

### Server-Sent Events (SSE)

```typescript
'use client';

import { useEffect, useState } from 'react';

export function ProgressComponent({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/progress/stream/${jobId}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.percent);
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, [jobId]);

  return <div>Progress: {progress}%</div>;
}
```

---

## Code Quality Standards

### Python (Backend)

- **Type hints required** (enforced by Pyright)
- **Async/await** for all I/O operations (never blocking calls)
- **Pydantic** for validation (all request/response models)
- **Black** formatting (88 char line length)
- **isort** for imports
- **Descriptive error messages** with context

```python
from typing import List, Optional

async def search_documents(
    query: str,
    k: int = 10,
    collection: Optional[str] = None
) -> List[SearchResult]:
    """Search documents using visual embeddings.

    Args:
        query: Search query text
        k: Number of results to return
        collection: Optional collection name override

    Returns:
        List of search results with scores and metadata
    """
    # Implementation
```

### TypeScript (Frontend)

- **Strict mode** enabled
- **No `any` types** (use `unknown` if needed)
- **Prefer Server Components** (default)
- **Client Components** only when needed (`'use client'`)
- **Zod** for runtime validation

```typescript
interface SearchProps {
  query: string;
  limit?: number;
}

export async function searchDocuments({
  query,
  limit = 10
}: SearchProps): Promise<SearchResult[]> {
  const validated = SearchRequestSchema.parse({ query, k: limit });
  const response = await apiClient.get('/search', { params: validated });
  return response.data;
}
```

---

## Testing

### Backend Testing

```bash
# WSL
cd backend

# Manual API tests
curl http://localhost:8000/health
curl "http://localhost:8000/search?q=test&k=5"
curl -X POST http://localhost:8000/index -F "files=@document.pdf"

# Pre-commit hooks (includes pyright type checking)
pre-commit run --all-files
```

### Frontend Testing

```bash
# bash
cd frontend

# Type checking
yarn type-check

# Build validation
yarn build
yarn start
```

### Integration Testing

1. Start all services: `docker compose --profile cpu up -d --build`
2. Test flow: Upload → Indexing → Search → Chat
3. Check Qdrant: http://localhost:6333/dashboard
4. Check MinIO: http://localhost:9001
5. Monitor logs: `docker compose logs -f backend`

---

## Common Issues

### Backend

**ColPali timeout:** Increase `COLPALI_API_TIMEOUT` or use GPU profile

**Progress stuck:** Install `poppler-utils` for PDF conversion

**Config changes not persisting:** Update `.env` file (runtime updates are ephemeral)

**Service cache not invalidating:** Mark setting as `critical: True` in the appropriate schema file in `backend/config_schema/`

**DeepSeek OCR not working:** Ensure `DEEPSEEK_OCR_ENABLED=True` in `.env` and GPU profile is running (DeepSeek is GPU-only)

### Frontend

**CORS errors:** Set explicit `ALLOWED_ORIGINS` in `.env` (not `*`)

**Images not loading:**
- Check `MINIO_PUBLIC_URL` in `.env`
- Add MinIO domain to `next.config.ts` `images.remotePatterns`

**Type errors after API changes:**
```bash
# WSL (from project root)
uv run python scripts/generate_openapi.py

# bash
cd frontend
yarn gen:sdk
yarn gen:zod
```

### Docker

**Port conflicts:** Stop conflicting containers, use only one ColPali profile at a time

**ColPali GPU build failing:** Ensure CUDA toolkit installed, first build compiles flash-attn (takes longer)

---

## File Organization Conventions

### When Adding Features

1. **New endpoint?** → Add router in `backend/api/routers/`
2. **Business logic?** → Create/extend service in `backend/services/`
3. **UI needed?** → Create page in `frontend/app/` or component in `frontend/components/`
4. **Configuration?** → Add to appropriate schema file in `backend/config_schema/` and register in `__init__.py`
5. **Long-running task?** → Use `BackgroundTasks` + progress tracking in `backend/api/progress.py`
6. **State management?** → Add to Zustand store in `frontend/stores/`

### Import Patterns

Backend services follow clear import hierarchy:
- Routers import from `dependencies.py` and `models.py`
- Dependencies import from `services/`
- Services import from `config.py` and external clients
- Never import routers from services (creates circular dependencies)

Frontend follows Next.js conventions:
- Pages in `app/` are Server Components by default
- Components in `components/` can be Server or Client
- Use `'use client'` directive only when needed (interactivity, hooks, browser APIs)
- API client in `lib/api/` uses generated types from `yarn gen:sdk`

---

## Version Management

Uses **Release Please** with **Conventional Commits**:

```bash
# Feature (minor version bump)
git commit -m "feat: add advanced search filters"

# Bug fix (patch version bump)
git commit -m "fix: resolve timeout issue"

# Breaking change (major version bump)
git commit -m "feat!: redesign API

BREAKING CHANGE: endpoint requires new parameter"

# No version bump
git commit -m "docs: update guide"
```

See `VERSIONING.md` for complete workflow.

---

## Special Notes

### Pipeline Package

The `backend/services/pipeline/` package is **vector-database-agnostic**. It handles batch processing, image storage, OCR coordination, and progress tracking independently of Qdrant. Database-specific code (point construction, upserts) lives in `backend/services/qdrant/indexing/`.

This separation allows the pipeline to work with other vector databases (Pinecone, Weaviate, etc.) by providing a custom `store_batch_cb` callback to `DocumentIndexer.index_documents()`.

### Docker Compose Profiles

Profiles are **mutually exclusive**:
- `--profile cpu` starts CPU-only ColPali (no GPU dependencies)
- `--profile gpu` starts GPU-accelerated ColPali + DeepSeek OCR (requires NVIDIA GPU and CUDA)

Only run one profile at a time to avoid port conflicts.

### DeepSeek OCR

- **GPU-only:** Requires `--profile gpu` and NVIDIA GPU with CUDA
- **Optional:** Set `DEEPSEEK_OCR_ENABLED=False` to disable when running CPU profile
- **Modes:** Gundam (default), Tiny, Small, Base, Large (configurable in `.env`)
- **Tasks:** markdown, plain_ocr, locate, describe, custom (see `backend/docs/configuration.md`)
- **UUID Naming:** OCR results use UUID-based filenames for reliable storage and retrieval
- **Worker Pool:** Adjustable concurrent workers via `DEEPSEEK_OCR_MAX_WORKERS` for batch processing

### DuckDB Analytics

- **Optional:** Set `DUCKDB_ENABLED=True` to enable
- **Document Deduplication:** Automatically detects and prevents duplicate uploads using content-based fingerprinting (filename, file_size_bytes, total_pages). Duplicates are skipped with user feedback.
- **Schema:** Three tables - `documents` (metadata), `pages` (page-level OCR data), `regions` (text regions with bounding boxes)
- **Purpose:** Store document metadata and OCR results in columnar format for SQL-based analytics
- **Query Sanitization:** SQL queries are sanitized (block comment stripping, length limits) before execution
- **UI:** DuckDB-Wasm UI available at http://localhost:4213
- **Graceful Shutdown:** Automatic checkpointing ensures data persistence on close

---

## Additional Resources

- `README.md` - Project overview and quick start
- `AGENTS.md` - Comprehensive AI agent development guide (very detailed)
- `VERSIONING.md` - Version management and release workflow
- `backend/docs/architecture.md` - System architecture deep dive
- `backend/docs/configuration.md` - Complete configuration reference
- `backend/docs/pipeline.md` - Pipeline processing architecture
- `backend/docs/analysis.md` - Vision vs. text RAG comparison
- `.github/DOCKER_REGISTRY.md` - Pre-built Docker images guide
