# Backend Refactoring Plan - Clean Architecture

## Current Issues

### 1. **Tight Coupling**
- `QdrantService` depends directly on `ColPaliService`, `MinioService`, `DeepSeekOCRService`
- Routers directly instantiate and use services
- No abstractions between layers
- Services know too much about each other

### 2. **Inconsistent Structure**
- `qdrant/` has subdirectories, other services are single files
- No clear separation of concerns
- Business logic mixed with infrastructure code
- Configuration scattered across files

### 3. **Dependency Injection Issues**
- `@lru_cache` for DI is a hack, not proper DI
- Services are singletons with global state
- Hard to test in isolation
- Hard to swap implementations

## Proposed Structure

```
backend/
├─ app/                              # Importable package: `app`
│  ├─ __init__.py
│  ├─ main.py                        # FastAPI app + lifespan
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ deps.py                     # DI wiring for routers
│  │  └─ v1/
│  │     ├─ __init__.py
│  │     ├─ routers/
│  │     │  ├─ indexing.py
│  │     │  ├─ retrieval.py
│  │     │  ├─ config.py
│  │     │  ├─ maintenance.py
│  │     │  └─ meta.py
│  │     └─ schemas/                 # Pydantic I/O models
│  │        ├─ indexing.py
│  │        ├─ retrieval.py
│  │        └─ common.py
│  ├─ core/                           # Cross-cutting concerns
│  │  ├─ __init__.py
│  │  ├─ config.py                    # Pydantic Settings v2
│  │  ├─ logging.py                   # Logging config
│  │  └─ security.py                  # (if needed) auth helpers
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ session.py                   # Engine / session factory
│  │  └─ base.py                      # SQLAlchemy Base & registry
│  ├─ models/                         # ORM models
│  │  ├─ __init__.py
│  │  └─ document.py
│  ├─ repositories/                   # Data access layer (ports + adapters)
│  │  ├─ __init__.py
│  │  ├─ interfaces/                  # Clean-arch ports
│  │  │  ├─ document_repository.py    # IDocumentRepository
│  │  │  └─ vector_repository.py      # IVectorRepository
│  │  ├─ qdrant_vector.py             # QdrantVectorRepository (impl)
│  │  └─ document_repository.py       # DocumentRepositoryImpl (impl)
│  ├─ services/                        # Application/use-case layer
│  │  ├─ __init__.py
│  │  ├─ index_documents.py           # IndexDocumentsUseCase
│  │  └─ search_documents.py          # SearchDocumentsUseCase
│  ├─ integrations/                    # External service clients
│  │  ├─ __init__.py
│  │  ├─ colpali_client.py
│  │  ├─ deepseek_client.py
│  │  └─ minio_client.py
│  ├─ workers/                         # Background jobs if any
│  │  └─ __init__.py
│  ├─ middleware/
│  │  └─ timing.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ slugs.py
│     └─ pdf.py                        # (moved from api/utils.py)
├─ migrations/                         # Alembic
│  └─ env.py
├─ tests/
│  ├─ __init__.py
│  ├─ conftest.py
│  ├─ unit/
│  └─ integration/
├─ scripts/
│  └─ export_openapi.py
├─ .env.example
├─ pyproject.toml
├─ pre-commit-config.yaml
├─ Dockerfile
├─ docker-compose.yml
└─ README.md

# REMOVE: legacy services/ (migrated into integrations/ and repositories/) and ensure a single solution without fallbacks to old files.
```

### Utilities

- Move PDF helpers to `app/utils/pdf.py`
- Keep non-HTTP progress utilities (if any) under `app/utils/` or surface them via use-case callbacks

---

## Implementation Phases

### Phase 1 — Create Integrations & Repos

- [x] Scaffold `backend/app/` package skeleton (api/, core/, integrations/, etc.) to support incremental migration.

#### Integrations

- [x] `services/colpali.py` → `app/integrations/colpali_client.py`
- [x] `services/minio.py` → `app/integrations/minio_client.py`
- [x] `services/deepseek.py` → `app/integrations/deepseek_client.py`
- [x] `services/qdrant/` → `app/integrations/qdrant/` (with shims under `services/qdrant/`)
- [x] Move shared indexing helpers (OCR, storage, progress) into `app/services/indexing/` to decouple them from the Qdrant client

> Legacy `services/*.py` modules now provide compatibility shims that re-export the new clients until Phase 4 removes the old package.

#### Repositories

- Extract from `app/integrations/qdrant/service.py` → `app/repositories/qdrant_vector.py`
- Extract from `app/integrations/qdrant/indexing/` → `app/repositories/document_repository.py`
- Define ports in `app/repositories/interfaces/*`

#### Config

- Consolidate config into `app/core/config.py` (+ `app/core/logging.py`)

### Phase 2 — Use Cases (Services)

- `app/services/index_documents.py`
- `app/services/search_documents.py`
- Move orchestration/business rules here; repositories are IO-only

### Phase 3 — API Layer

- Add `app/api/deps.py` for DI factories
- Create/adjust `app/api/v1/schemas/*` and wire routers to use cases

### Phase 4 — Cleanup

- Remove legacy `services/` folder
- Remove `api/models.py` in favor of `api/v1/schemas/*`
- Update imports; run `ruff`, `black`, `mypy`
- Update `docs/README`
