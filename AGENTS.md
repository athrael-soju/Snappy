# AI Agent Guide for Snappy Development 🤖

> **Project:** Snappy – Vision-Grounded Document Retrieval  
> **For:** AI agents, code assistants, and automated development tools  
> **Purpose:** Comprehensive reference for understanding and modifying this codebase

---

## Table of Contents

- [Quick Start for Agents](#quick-start-for-agents)
- [Project Overview](#project-overview)
- [Architecture Deep Dive](#architecture-deep-dive)
- [Development Environment](#development-environment)
- [Codebase Navigation](#codebase-navigation)
- [Common Patterns](#common-patterns)
- [Testing & Validation](#testing--validation)
- [Deployment](#deployment)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Best Practices](#best-practices)

---

## Quick Start for Agents

### Essential Context

**What is Snappy?**
A vision-first document retrieval system that uses ColPali embeddings to search PDFs by visual appearance, not just text. Users can upload documents, search visually, and chat with AI using visual citations.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.11+) with async/await patterns
- **Frontend:** Next.js 16 (App Router, Server Components, TypeScript) with React 19.2
- **Vector DB:** Qdrant (multivector search with optional MUVERA)
- **Storage:** MinIO (S3-compatible object storage)
- **Embeddings:** ColPali service (standalone FastAPI app)
- **Orchestration:** Docker Compose (GPU/CPU profiles)
- **Package Management:** `uv` (Python), `yarn` (Node.js)

**Key Features:**
- Page-level visual retrieval (no OCR required)
- Streaming chat with visual citations (OpenAI Responses API)
- Real-time indexing progress (Server-Sent Events)
- Runtime configuration with schema-driven UI
- Background job management for long-running tasks

### First Steps When Engaging with This Project

1. **Read the README** (`README.md`) for system overview and quick start
2. **Review architecture** (`backend/docs/architecture.md`) for data flows
3. **Check configuration** (`backend/docs/configuration.md`, `backend/CONFIGURATION_GUIDE.md`)
4. **Examine relevant routers** in `backend/api/routers/` for API patterns
5. **Explore frontend pages** in `frontend/app/` for UI implementation

### Critical Files to Understand

| File | Purpose | When to Reference |
|------|---------|-------------------|
| `backend/api/app.py` | FastAPI application setup | Understanding API structure |
| `backend/config_schema.py` | Configuration defaults & schema | Adding/modifying settings |
| `backend/api/dependencies.py` | Service instances & caching | Service lifecycle management |
| `backend/api/progress.py` | SSE job tracking | Implementing background tasks |
| `backend/services/qdrant/indexing.py` | Document indexing logic | Understanding embedding workflow |
| `backend/services/qdrant/search.py` | Search & retrieval logic | Implementing search features |
| `frontend/lib/api/client.ts` | API client wrapper | Frontend-backend integration |
| `frontend/app/api/chat/route.ts` | Streaming chat implementation | SSE patterns in Next.js |
| `docker-compose.yml` | Service orchestration | Deployment and service dependencies |

---

## Project Overview

### Directory Structure

```
.
├── backend/                    # FastAPI backend application
│   ├── api/                   # API layer (routers, models, dependencies)
│   │   └── routers/          # Endpoint definitions
│   ├── services/              # Business logic layer
│   │   └── qdrant/           # Vector DB operations
│   ├── data/                  # Sample datasets
│   ├── docs/                  # Technical documentation
│   └── scripts/               # Utility scripts (OpenAPI generation)
│
├── colpali/                   # Standalone embedding service
│   ├── app.py                # ColPali FastAPI server
│   └── Dockerfile.{cpu,gpu}  # Environment-specific builds
│
├── frontend/                  # Next.js 16 frontend with React 19.2
│   ├── app/                  # App Router pages & API routes
│   │   ├── api/chat/        # SSE streaming chat endpoint
│   │   └── [feature]/       # Feature pages (upload, search, chat, etc.)
│   ├── components/           # React components
│   │   ├── ui/              # shadcn/ui components
│   │   └── chat/            # Chat-specific components
│   ├── lib/                  # Utilities, API client, hooks
│   ├── stores/               # Zustand state management
│   └── docs/                 # Frontend-specific docs (OpenAPI spec)
│
├── docker-compose.yml         # Main service orchestration
└── .env                       # Backend environment variables
```

### Component Communication

```
User Browser
    ↓ ↑
Next.js Frontend (Port 3000)
    ↓ ↑
FastAPI Backend (Port 8000)
    ↓ ↑ (parallel)
    ├─→ Qdrant (Port 6333)     - Vector search
    ├─→ MinIO (Port 9000)       - Image storage
    └─→ ColPali (Port 8080)     - Embeddings

Chat Flow (separate):
User Browser ←SSE← Next.js Chat API ←→ OpenAI API
                         ↓
                   Backend /search
```

---

## Architecture Deep Dive

### Backend Architecture

**Layer Separation:**
```
Routers (HTTP handlers)
    ↓
Dependencies (service instances, caching)
    ↓
Services (business logic)
    ↓
External APIs/DBs (Qdrant, MinIO, ColPali)
```

**Key Patterns:**

1. **Dependency Injection**
   - Services instantiated via `@lru_cache` in `api/dependencies.py`
   - Cached until `invalidate_services()` is called
   - Critical config changes trigger automatic invalidation

2. **Background Tasks**
   - Long operations (indexing) run via `BackgroundTasks`
   - Progress tracked in-memory via `api/progress.py`
   - SSE streams provide real-time updates to frontend

3. **Configuration Management**
   - Schema-driven: `config_schema.py` is single source of truth
   - Runtime updates: `runtime_config.py` provides thread-safe storage
   - Lazy access: `config.py` with `__getattr__` for dynamic lookup
   - API exposure: `/config/*` endpoints for UI integration

4. **Error Handling**
   - HTTP exceptions with descriptive messages
   - Structured logging via `logging` module
   - Graceful degradation where possible

### Frontend Architecture

**Framework:** Next.js 16 App Router with React 19.2

**Key Patterns:**

1. **Server Components First**
   - Default to Server Components for better performance
   - Client Components (`'use client'`) only when needed for interactivity
   - Metadata exported from page components

2. **Type Safety**
   - OpenAPI spec → generated TypeScript types (`yarn gen:sdk`)
   - Zod schemas for runtime validation (`yarn gen:zod`)
   - Zodios client for type-safe API calls

3. **State Management**
   - Zustand store in `stores/app-store.tsx`
   - Reducers pattern for complex state logic
   - Local component state for ephemeral UI state

4. **Streaming**
   - SSE for real-time updates (indexing progress, chat)
   - Edge runtime for chat API route
   - Event-driven UI updates

5. **Design System**
   - shadcn/ui components in `components/ui/`
   - Design tokens: `text-body-*`, `size-icon-*`, etc.
   - Tailwind CSS with custom utilities in `utilities.css`

### Service Layer Details

#### Qdrant Service (`backend/services/qdrant/`)

**Modules:**
- `service.py` - Main client wrapper, collection management
- `collection.py` - Collection creation, schema definition
- `indexing.py` - Document indexing with pipeline parallelization
- `search.py` - Multi-stage retrieval (MUVERA + prefetch + rerank)
- `embedding.py` - Embedding utilities and pooling

**Search Flow:**
1. Query embedding via ColPali
2. Optional MUVERA first-stage (if enabled)
3. Prefetch with pooled vectors (if mean pooling enabled)
4. Final rerank with full multivectors
5. Score normalization and result formatting

**Indexing Flow:**
1. PDF → images (via Poppler)
2. Batch images for embedding
3. Parallel pipeline (when enabled):
   - Executor 1: Embedding + image upload
   - Executor 2: Qdrant upserts
4. Progress updates via SSE

#### MinIO Service (`backend/services/minio.py`)

**Features:**
- Concurrent uploads with ThreadPoolExecutor
- Retry logic with exponential backoff
- Public URL generation (handles `MINIO_PUBLIC_URL`)
- Auto-sizing worker pool based on CPU count

#### ColPali Service (`backend/services/colpali.py`)

**Endpoints Used:**
- `POST /embed/queries` - Text → embeddings
- `POST /embed/images` - Images → embeddings + token boundaries
- `GET /info` - Model metadata (dimensions, patch size)

**Configuration:**
- `COLPALI_URL` - Service endpoint
- `COLPALI_API_TIMEOUT` - Request timeout (default 300s)

---

## Development Environment

### Terminal Usage by Component

**CRITICAL:** Use the correct terminal for each component:

| Component | Terminal | Package Manager | Setup Steps | Example Commands |
|-----------|----------|-----------------|-------------|------------------|
| **Backend** | WSL | `uv` + `venv` | 1. Open WSL terminal<br>2. Navigate to project root<br>3. `cd backend`<br>4. `source .venv/bin/activate` | `uv run uvicorn backend.main:app --reload`<br>`uv pip install -r requirements.txt` |
| **ColPali Service** | WSL | `uv` + `venv` | 1. Open WSL terminal<br>2. Navigate to project root<br>3. `cd colpali`<br>4. `source .venv/bin/activate` | `uv run uvicorn colpali.app:app --port 8080`<br>`uv pip install -r requirements.txt` |
| **Frontend** | bash/PowerShell | `yarn` | 1. Open bash or PowerShell terminal<br>2. Navigate to project root<br>3. `cd frontend` | `yarn install --frozen-lockfile`<br>`yarn dev`<br>`yarn gen:sdk` |

### Environment Setup

#### Backend & ColPali (WSL + uv)

```bash
# In WSL terminal
cd Snappy

# Backend
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# ColPali
cd ../colpali
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn colpali.app:app --host 0.0.0.0 --port 8080
```

#### Frontend (bash + yarn)

```bash
# In bash terminal
cd frontend
yarn install --frozen-lockfile
yarn dev
```

### Docker Development

**Start all services:**
```bash
# In WSL or bash
docker compose up -d --build
```

**ColPali profiles (start only one):**
```bash
# GPU
cd colpali
docker compose --profile gpu up -d --build

# CPU
docker compose --profile cpu up -d --build
```

**View logs:**
```bash
docker compose logs -f [service_name]
```

---

## Codebase Navigation

### When Adding Features

**Ask yourself:**
1. **Is this a new endpoint?** → Add router in `backend/api/routers/`
2. **Does it need business logic?** → Create/extend service in `backend/services/`
3. **Does it need a UI?** → Create page in `frontend/app/` or component in `frontend/components/`
4. **Does it need configuration?** → Add to `backend/config_schema.py`
5. **Is it a long-running task?** → Use `BackgroundTasks` + progress tracking
6. **Does it need state?** → Add to Zustand store or use React state

### Finding Existing Functionality

**Search Strategy:**
1. **Semantic search** for concepts (use grep or IDE search)
2. **File naming** follows clear conventions (routers match features)
3. **Import tracing** from routers → dependencies → services

**Common Queries:**
- "How is indexing implemented?" → `backend/services/qdrant/indexing.py`
- "How does search work?" → `backend/services/qdrant/search.py`
- "Where is the upload UI?" → `frontend/app/upload/page.tsx`
- "How does chat streaming work?" → `frontend/app/api/chat/route.ts`
- "Where are config settings defined?" → `backend/config_schema.py`

### API Documentation

**Generate OpenAPI spec:**
```bash
# In WSL (from project root)
cd Snappy
uv run python scripts/generate_openapi.py
```

**Update frontend types:**
```bash
# In bash
cd frontend
yarn gen:sdk    # TypeScript types
yarn gen:zod    # Zod schemas
```

---

## Common Patterns

### Backend Patterns

#### 1. Creating a New Router

```python
# backend/api/routers/my_feature.py
from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_my_service
from ..models import MyRequest, MyResponse

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post("/action", response_model=MyResponse)
async def perform_action(
    request: MyRequest,
    service = Depends(get_my_service)
):
    try:
        result = await service.do_something(request.data)
        return MyResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Register in `backend/api/app.py`:**
```python
from .routers import my_feature
app.include_router(my_feature.router)
```

#### 2. Background Task with Progress

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

#### 3. Adding Configuration

```python
# backend/config_schema.py
"my_feature": {
    "MY_SETTING": {
        "default": "default_value",
        "type": "str",
        "description": "Description of setting",
        "critical": False,  # Set True if change requires service reload
        "group": "My Feature",
        "label": "My Setting"
    }
}
```

**Access in code:**
```python
from backend.config import config

value = config.MY_SETTING  # Dynamic lookup
```

#### 4. Service with Caching

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

# Invalidate when critical config changes
def invalidate_services():
    get_my_service.cache_clear()
    # ... other services
```

### Frontend Patterns

#### 1. Creating a New Page

```typescript
// frontend/app/my-feature/page.tsx
import { PageHeader } from '@/components/page-header';
import { MyFeatureComponent } from '@/components/my-feature';

export const metadata = {
  title: 'My Feature',
  description: 'Description of my feature'
};

export default function MyFeaturePage() {
  return (
    <div className="container mx-auto py-6">
      <PageHeader
        title="My Feature"
        description="Description of my feature"
      />
      <MyFeatureComponent />
    </div>
  );
}
```

#### 2. API Integration with Type Safety

```typescript
// After yarn gen:sdk and yarn gen:zod
import { apiClient } from '@/lib/api/client';
import { MyRequestSchema } from '@/lib/validation/schemas';

async function callApi(data: unknown) {
  // Runtime validation
  const validated = MyRequestSchema.parse(data);
  
  // Type-safe API call
  const response = await apiClient.post('/my-feature/action', validated);
  return response.data;
}
```

#### 3. Server-Sent Events (SSE)

```typescript
// Frontend component
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

#### 4. Using the App Store

```typescript
// frontend/stores/app-store.tsx
import { create } from 'zustand';

interface MyFeatureState {
  data: string | null;
  setData: (data: string) => void;
}

export const useMyFeatureStore = create<MyFeatureState>((set) => ({
  data: null,
  setData: (data) => set({ data })
}));

// In component
const { data, setData } = useMyFeatureStore();
```

---

## Testing & Validation

### Backend Testing

**Manual API Testing:**
```bash
# In WSL
# Health check
curl http://localhost:8000/health

# Search
curl "http://localhost:8000/search?q=test&k=5"

# Upload
curl -X POST http://localhost:8000/index \
  -F "files=@/path/to/document.pdf"
```

**Python Testing:**
```bash
# In WSL
cd backend
uv run pytest tests/
```

### Frontend Testing

**Development Server:**
```bash
# In bash
cd frontend
yarn dev
```

**Build Validation:**
```bash
yarn build
yarn start
```

**Type Checking:**
```bash
yarn type-check
```

### Integration Testing

**Full Stack:**
1. Start all services via Docker Compose
2. Test upload → indexing → search → chat flow
3. Monitor logs for errors
4. Check Qdrant UI (http://localhost:6333/dashboard)
5. Check MinIO console (http://localhost:9001)

### Pre-commit Validation

Backend has pre-commit hooks (see `.pre-commit-config.yaml`):
- `autoflake` - Remove unused imports
- `isort` - Sort imports
- `black` - Format code
- `pyright` - Type checking

**Run manually:**
```bash
# In WSL
cd backend
pre-commit run --all-files
```

---

## Deployment

### Docker Compose Production

**Environment files:**
```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

**Key variables to set:**
- `.env`: `OPENAI_API_KEY`, database URLs, credentials
- `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL`, `OPENAI_API_KEY`

**Start services:**
```bash
docker compose up -d --build
```

**Scale considerations:**
- Backend: Stateless, can scale horizontally
- Qdrant: Single instance (or cluster with Qdrant Cloud)
- MinIO: Single instance (or distributed setup)
- ColPali: GPU-enabled host recommended for performance

### Individual Services

**Backend only:**
```bash
# In WSL
cd backend
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Frontend only:**
```bash
# In bash
cd frontend
yarn build
yarn start
```

---

## Troubleshooting Guide

### Common Issues

#### Backend Issues

**Problem:** ColPali timing out
- **Cause:** Heavy workload, CPU-only service
- **Solution:** Increase `COLPALI_API_TIMEOUT` or use GPU profile

**Problem:** Progress bar stuck during indexing
- **Cause:** PDF conversion failure (Poppler missing)
- **Solution:** Install `poppler-utils` in backend environment/container

**Problem:** Config changes not persisting
- **Cause:** `/config/update` only affects runtime
- **Solution:** Update `.env` file and restart

**Problem:** Service cache not invalidating
- **Cause:** Setting not marked as critical
- **Solution:** Add key to `get_critical_keys()` in `config_schema.py`

#### Frontend Issues

**Problem:** CORS errors
- **Cause:** Backend `ALLOWED_ORIGINS` not configured
- **Solution:** Set explicit origins (not `*`) in `.env`

**Problem:** Images not loading
- **Cause:** MinIO URL misconfiguration or Next.js domain not allowed
- **Solution:** 
  - Check `MINIO_PUBLIC_URL` in `.env`
  - Add MinIO domain to `next.config.ts` `images.remotePatterns`

**Problem:** Type errors after API changes
- **Cause:** OpenAPI spec out of sync
- **Solution:**
  ```bash
  # WSL (from project root)
  uv run python scripts/generate_openapi.py
  
  # bash
  cd frontend
  yarn gen:sdk
  yarn gen:zod
  ```

#### Docker Issues

**Problem:** Port conflicts
- **Cause:** Multiple services or profiles running
- **Solution:** Stop conflicting containers, use one ColPali profile only

**Problem:** ColPali GPU build failing
- **Cause:** Flash-attention compilation issues
- **Solution:** 
  - Ensure CUDA toolkit installed
  - First build takes longer (compiling flash-attn)
  - Check CUDA version compatibility

### Debug Checklist

1. **Check logs:** `docker compose logs -f [service]`
2. **Verify environment:** Ensure `.env` and `.env.local` are correct
3. **Test connectivity:** Can backend reach Qdrant/MinIO/ColPali?
4. **Check config:** `GET /config/values` to see runtime values
5. **Validate data:** Check Qdrant dashboard, MinIO browser
6. **Review recent changes:** What was modified last?

---

## Best Practices

### For AI Agents Working on This Project

#### Before Making Changes

1. **Understand context fully**
   - Read relevant documentation (`README.md`, `backend/docs/`)
   - Examine existing code in the area you're modifying
   - Check for similar patterns elsewhere in the codebase

2. **Identify impact**
   - Will this affect the API contract? (regenerate OpenAPI)
   - Does it need new configuration? (update `config_schema.py`)
   - Will it break existing features? (test thoroughly)
   - Does it need documentation? (update relevant `.md` files)

3. **Plan the implementation**
   - Break down into smaller, testable units
   - Identify dependencies and order of implementation
   - Consider error cases and edge conditions

#### While Implementing

1. **Follow existing patterns**
   - Router → Service → External API structure
   - Dependency injection for services
   - Pydantic models for validation
   - SSE for long-running tasks
   - Type hints everywhere (Python and TypeScript)

2. **Write clean code**
   - Descriptive variable/function names
   - Comments for non-obvious logic
   - Error handling with context
   - Logging for debugging

3. **Test incrementally**
   - Test each component as you build it
   - Use appropriate terminal (WSL for backend, bash for frontend)
   - Verify against actual services (not just mocks)

4. **Update documentation**
   - Inline comments in code
   - API documentation (OpenAPI spec)
   - User-facing docs (README, guides)
   - This AGENTS.md if adding new patterns

#### After Implementation

1. **Validate thoroughly**
   - Run pre-commit hooks (backend)
   - Type checking (frontend)
   - Manual testing of the feature
   - Integration testing with full stack

2. **Update generated artifacts**
   - Regenerate OpenAPI spec if API changed
   - Regenerate TypeScript types if API changed
   - Update Zod schemas if models changed

3. **Check for regressions**
   - Test existing features that might be affected
   - Review error logs
   - Verify configuration still works

4. **Document changes**
   - Update relevant README sections
   - Add/update inline code comments
   - Note any breaking changes clearly

### Code Quality Standards

**Python (Backend & ColPali):**
- Type hints required (enforced by Pyright)
- Async/await for I/O operations
- Pydantic for validation
- Descriptive error messages
- Comprehensive logging

**TypeScript (Frontend):**
- Strict mode enabled
- No `any` types (use `unknown` if needed)
- Prefer Server Components
- Client Components only when necessary
- Zod for runtime validation

**General:**
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- Single Responsibility Principle
- Clear separation of concerns
- Meaningful names over comments

### Performance Considerations

**Backend:**
- Use async/await, never blocking calls
- Batch operations when possible (indexing, uploads)
- Cache expensive computations
- Stream large responses
- Background tasks for long operations

**Frontend:**
- Server Components for static content
- Client Components for interactivity only
- Image optimization (Next.js Image component)
- Code splitting (dynamic imports)
- Minimize bundle size

**Database:**
- Use prefetch for better Qdrant performance
- Enable mean pooling for faster search
- Configure quantization for memory efficiency
- Adjust `QDRANT_PREFETCH_LIMIT` based on data size

### Security Considerations

**Backend:**
- Validate all inputs (Pydantic models)
- Sanitize file uploads (type checking)
- Use explicit CORS origins (not `*`)
- Secure MinIO credentials
- Rate limiting for expensive endpoints (consider adding)

**Frontend:**
- Sanitize user inputs
- Use environment variables for secrets
- HTTPS in production
- Validate API responses with Zod

---

## Quick Reference Commands

### Backend (WSL + uv)

```bash
# Setup
uv venv
source .venv/bin/activate
uv pip install -r backend/requirements.txt

# Run
uv run uvicorn backend.main:app --reload

# Generate OpenAPI (from project root)
uv run python scripts/generate_openapi.py

# Pre-commit hooks
pre-commit run --all-files
```

### Frontend (bash + yarn)

```bash
# Setup
yarn install --frozen-lockfile

# Run
yarn dev

# Build
yarn build
yarn start

# Type generation
yarn gen:sdk      # TypeScript types from OpenAPI
yarn gen:zod      # Zod schemas from OpenAPI

# Type checking
yarn type-check
```

### Docker

```bash
# Full stack
docker compose up -d --build
docker compose logs -f
docker compose down

# ColPali GPU
cd colpali
docker compose --profile gpu up -d --build

# ColPali CPU
docker compose --profile cpu up -d --build
```

### Versioning & Releases

```bash
# Check version sync status
python scripts/sync_version.py

# Sync versions manually
python scripts/sync_version.py 1.2.3

# Create release (bash)
./scripts/create_release.sh

# Commit with conventional format
git commit -m "feat: add new feature"  # Minor bump
git commit -m "fix: bug fix"           # Patch bump
git commit -m "feat!: breaking change" # Major bump
```

---

## Additional Resources

### Documentation Files

- `README.md` - Project overview, quick start
- `VERSIONING.md` - **Version management and release guide**
- `scripts/README.md` - **Project utility scripts documentation**
- `backend/README.md` - Backend-specific guide
- `frontend/README.md` - Frontend-specific guide
- `colpali/README.md` - ColPali service guide
- `backend/docs/architecture.md` - System architecture deep dive
- `backend/docs/configuration.md` - Configuration reference
- `backend/docs/analysis.md` - Vision vs. text RAG comparison
- `backend/CONFIGURATION_GUIDE.md` - Config implementation details

### External References

- **ColPali:** https://arxiv.org/abs/2407.01449
- **Qdrant multivector:** https://qdrant.tech/blog/colpali-qdrant-optimization/
- **MUVERA:** https://qdrant.tech/articles/muvera-embeddings/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Next.js:** https://nextjs.org/docs
- **Zustand:** https://github.com/pmndrs/zustand
- **shadcn/ui:** https://ui.shadcn.com/

---

## Contributing

When contributing to this project:

1. **Follow the patterns** established in existing code
2. **Use the correct terminal** (WSL for backend, bash for frontend)
3. **Use Conventional Commits** for all commit messages (see `VERSIONING.md`)
4. **Test thoroughly** before committing
5. **Update documentation** for any new features or changes
6. **Regenerate types** if API contracts change
7. **Run pre-commit hooks** to ensure code quality

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature (minor version bump)
git commit -m "feat: add MUVERA support"

# Bug fix (patch version bump)
git commit -m "fix: resolve search timeout issue"

# Breaking change (major version bump)
git commit -m "feat!: redesign search API

BREAKING CHANGE: /search endpoint requires 'collection' parameter"

# No version bump
git commit -m "docs: update configuration guide"
```

See `VERSIONING.md` for complete release workflow.

---

## Final Notes for AI Agents

This codebase is designed to be:
- **Modular:** Each component has clear responsibilities
- **Type-safe:** Comprehensive typing in both Python and TypeScript
- **Configurable:** Schema-driven configuration with runtime updates
- **Observable:** SSE streaming for long operations, comprehensive logging
- **Maintainable:** Clear patterns, good documentation, automated tooling

When in doubt:
1. Look for similar existing implementations
2. Follow established patterns strictly
3. Test in the correct environment (WSL vs bash)
4. Update documentation
5. Ask clarifying questions before making assumptions

**Remember:** This is a production-quality template. Maintain that standard in all contributions.

---

**Last Updated:** October 23, 2025  
**For Questions:** Review documentation, examine existing code patterns, or consult project maintainers
