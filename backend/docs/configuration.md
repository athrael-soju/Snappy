# Snappy Configuration Guide ⚙️

This document lists every runtime setting exposed by the FastAPI backend. Defaults and metadata live in `backend/config_schema.py`, which also powers:

- the `/config/*` API endpoints,
- the configuration UI,
- and the `config` module used throughout the application.

Runtime updates take effect immediately but do not persist across restarts—update your `.env` or deployment secrets for changes you want to keep.

---

## Contents

- [How configuration is resolved](#how-configuration-is-resolved)
- [Core application](#core-application)
- [Document ingestion](#document-ingestion)
- [Upload controls](#upload-controls)
- [ColPali embedding service](#colpali-embedding-service)
- [DeepSeek OCR](#deepseek-ocr)
- [Qdrant vector database](#qdrant-vector-database)
- [Object storage (MinIO)](#object-storage-minio)
- [DuckDB analytics](#duckdb-analytics)
- [Operational environment variables](#operational-environment-variables)
- [Runtime updates via API](#runtime-updates-via-api)
- [Troubleshooting](#troubleshooting)

---

## How Configuration Is Resolved

1. `.env` (and other environment values) load on startup.
2. `runtime_config` keeps a mutable copy of every setting.
3. The `config` module looks up values in the schema, coerces them to the correct type, and applies computed defaults when needed (for example, auto-sized MinIO workers).
4. `/config/update` and `/config/reset` change the runtime store and invalidate cached service clients if a critical setting changed.

Only keys defined in the schema can be updated at runtime.

---

## Core Application

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `LOG_LEVEL` | str | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `ALLOWED_ORIGINS` | list | `*` | CORS policy. Use explicit URLs for production. |
| `UVICORN_RELOAD` | bool | `True` | Hot reload in development. Disable in production. |

⚠️ `ALLOWED_ORIGINS=["*"]` is permissive; lock it down when exposing the API.

---

## Document Ingestion

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `BATCH_SIZE` | int | `4` | Pages processed per batch. Higher values increase throughput but need more memory. |
| `ENABLE_AUTO_CONFIG_MODE` | bool | `True` | Overlaps embedding, storage, and upserts. Disable for debugging or very small machines. |

Helpers:
- `config.get_ingestion_worker_threads()` estimates PDF conversion threads from CPU count.
- `config.get_pipeline_max_concurrency()` sizes pipeline concurrency.

---

## Upload Controls

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `UPLOAD_ALLOWED_FILE_TYPES` | list | `pdf` | Comma-separated extensions accepted during upload. Snappy currently ships with PDF support only; the configuration UI prevents deselecting the last remaining type. |
| `UPLOAD_MAX_FILE_SIZE_MB` | int | `10` | Maximum size (MB) for a single file. Values are clamped between 1 and 200 MB. |
| `UPLOAD_MAX_FILES` | int | `5` | Maximum number of files per upload request. Clamped between 1 and 20. |
| `UPLOAD_CHUNK_SIZE_MBYTES` | int | `2` | Chunk size used when streaming uploads to disk. Values outside 64 KB to 16 MB are clamped automatically. |

> The upload endpoint validates all limits server-side. Adjusting these values affects both the backend acceptance criteria and the frontend hints.

---

## ColPali Embedding Service

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `COLPALI_URL` | str | `http://localhost:7000` | Endpoint for the ColPali service. |
| `COLPALI_API_TIMEOUT` | int | `300` | Timeout (seconds) for embedding requests. Increase for large documents, especially on CPU. |

---

## DeepSeek OCR

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `DEEPSEEK_OCR_ENABLED` | bool | `False` | Enable/disable DeepSeek OCR integration for advanced text extraction. |
| `DEEPSEEK_OCR_URL` | str | `http://localhost:8200` | Base URL for the DeepSeek OCR microservice. |
| `DEEPSEEK_OCR_API_TIMEOUT` | int | `180` | Request timeout (seconds) for OCR API calls. Increase for longer documents or CPU-only deployments. |
| `DEEPSEEK_OCR_MAX_WORKERS` | int | `4` | Maximum concurrent OCR requests per batch. Higher values increase throughput but require more GPU memory. |
| `DEEPSEEK_OCR_POOL_SIZE` | int | `20` | HTTP connection pool size. Should be ≥ (Max Workers × 3) to handle retries. |
| `DEEPSEEK_OCR_MODE` | str | `Gundam` | Default processing mode: `Gundam` (best balance), `Tiny` (fastest), `Small` (quick), `Base` (standard), `Large` (highest quality). |
| `DEEPSEEK_OCR_TASK` | str | `markdown` | Default task type: `markdown` (structured output), `plain_ocr` (simple text), `locate` (find text), `describe` (image description), `custom` (custom prompts). |
| `DEEPSEEK_OCR_LOCATE_TEXT` | str | `` | Specific text to find when using `locate` task. |
| `DEEPSEEK_OCR_CUSTOM_PROMPT` | str | `` | Custom prompt when using `custom` task type. Use `<\|grounding\|>` tag for spatial information. |
| `DEEPSEEK_OCR_INCLUDE_GROUNDING` | bool | `True` | Include bounding box information in OCR results for layout analysis. |
| `DEEPSEEK_OCR_INCLUDE_IMAGES` | bool | `True` | Extract and embed images from documents as base64-encoded data in markdown output. |

> **GPU requirement:** The DeepSeek OCR container only runs when the GPU Docker Compose profile is active. Disable `DEEPSEEK_OCR_ENABLED` (or point to another OCR service) when running the CPU stack.

The OCR service is optional and runs separately from the main backend. When enabled, it provides advanced text extraction, markdown conversion, visual grounding with bounding boxes, and embedded image extraction. See `deepseek-ocr/README.md` for service setup and `backend/api/routers/ocr.py` for API endpoints.

---

## Qdrant Vector Database

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `QDRANT_URL` | str | `http://localhost:6333` | External Qdrant endpoint (ignored in embedded mode). |
| `QDRANT_HTTP_TIMEOUT` | int | `5` | REST timeout for indexing calls. Increase for large batches. |
| `QDRANT_EMBEDDED` | bool | `False` | Run Qdrant in-process (handy for tests). |
| `QDRANT_COLLECTION_NAME` | str | `documents` | Collection name (also drives the MinIO bucket when unset). |
| `QDRANT_PREFETCH_LIMIT` | int | `200` | Multivector candidates when mean pooling is enabled. Higher values improve recall. |
| `QDRANT_ON_DISK` | bool | `True` | Store vectors on disk (memory-mapped). |
| `QDRANT_ON_DISK_PAYLOAD` | bool | `True` | Store payloads on disk. |
| `QDRANT_USE_BINARY` | bool | `False` | Enable binary quantisation. |
| `QDRANT_BINARY_ALWAYS_RAM` | bool | `True` | Keep binary vectors in RAM (only when quantisation is enabled). |
| `QDRANT_SEARCH_IGNORE_QUANT` | bool | `False` | Skip quantisation during search (diagnostic). |
| `QDRANT_SEARCH_RESCORE` | bool | `True` | Rescore with full precision after quantised search. |
| `QDRANT_SEARCH_OVERSAMPLING` | float | `2.0` | Candidate oversampling factor for rescoring. |
| `QDRANT_MEAN_POOLING_ENABLED` | bool | `False` | Enable row/column pooling (improves recall, increases indexing cost). |

Changing collection names, URLs, or quantisation settings triggers client invalidation automatically.

---

## Object Storage (MinIO)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `MINIO_URL` | str | `http://localhost:9000` | Internal endpoint for uploads. |
| `MINIO_PUBLIC_URL` | str | `http://localhost:9000` | Public URL for image links (defaults to `MINIO_URL` when empty). |
| `MINIO_ACCESS_KEY` | str | `minioadmin` | Access key (change in production). |
| `MINIO_SECRET_KEY` | str | `minioadmin` | Secret key (change in production). |
| `MINIO_BUCKET_NAME` | str | `` (auto) | Bucket name; auto-derived from collection name when blank. |
| `MINIO_WORKERS` | int | `12` (auto) | Concurrent upload workers. Auto-sized if not set. |
| `MINIO_RETRIES` | int | `3` (auto) | Retry attempts per object. Auto-sized with workers. |
| `MINIO_FAIL_FAST` | bool | `False` | Stop on first upload failure. |
| `MINIO_PUBLIC_READ` | bool | `True` | Apply a public-read bucket policy automatically. |
| `IMAGE_FORMAT` | str | `JPEG` | Output format (`JPEG`, `PNG`, `WEBP`). |
| `IMAGE_QUALITY` | int | `75` | JPEG/WEBP quality (ignored for PNG). |

Snappy requires object storage; inline image storage is not supported.

---

## DuckDB Analytics

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `DUCKDB_ENABLED` | bool | `False` | Enable DuckDB columnar storage for OCR analytics. |
| `DUCKDB_URL` | str | `http://localhost:8300` | DuckDB service endpoint. |
| `DUCKDB_DATABASE_NAME` | str | `documents` | Database name for OCR data storage. |
| `DUCKDB_API_TIMEOUT` | int | `30` | HTTP timeout for DuckDB API calls (seconds). |
| `DUCKDB_BATCH_SIZE` | int | `10` | Number of pages to batch for bulk inserts. |
| `DUCKDB_RETRY_ATTEMPTS` | int | `3` | Retry attempts for failed HTTP requests. |

DuckDB is an optional analytics service that stores OCR results in columnar format for SQL-based analysis. When enabled alongside DeepSeek OCR, extracted text, regions, and metadata are automatically stored in DuckDB for complex queries and reporting. See `duckdb/README.md` for service setup and schema details.

> **Note:** DuckDB integration is non-blocking. If the service is unavailable, OCR processing continues normally with a warning logged.

---

## Operational Environment Variables

These values are read directly from the environment and are not part of the dynamic schema:

- `HOST`, `PORT` – used by `backend/main.py` when launching uvicorn.
- `LOG_LEVEL` – uvicorn respects the environment value at process launch; it remains exposed in the schema for runtime adjustments.

Because they are absent from `config_schema.py`, they cannot be updated through the configuration API.

---

## Runtime Updates via API

| Endpoint | Purpose |
|----------|---------|
| `GET /config/schema` | Fetch schema metadata (used by the UI). |
| `GET /config/values` | Inspect the current runtime values. |
| `POST /config/update` | Set a single value. Critical keys trigger cache invalidation. |
| `POST /config/reset` | Restore defaults and clear runtime overrides. |

---

## Troubleshooting

- **Updates ignored?** Ensure the key exists in `config_schema.py`; only schema keys are allowed.
- **Clients not refreshing?** Critical keys invalidate caches automatically, but manual `.env` changes still require a restart.
- **MinIO upload failures?** Try reducing `BATCH_SIZE` or temporarily disabling pipeline indexing.
- **Quantisation changes not applied?** Recreate the Qdrant collection if schema-altering settings changed.

`backend/CONFIGURATION_GUIDE.md` covers how the configuration system is implemented internally.

