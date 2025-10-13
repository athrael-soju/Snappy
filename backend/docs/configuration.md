# Configuration Reference

This document describes every runtime configuration knob exposed by the FastAPI
backend. All dynamic settings are defined in `backend/config_schema.py`. The
schema powers the web configuration panel, the `/config/*` API endpoints, and
the `config` module that the application imports at runtime.

- Defaults live in `config_schema.py`.
- Settings are loaded from the environment (for example `.env`) into
  `runtime_config`.
- Accessing `config.MY_SETTING` reads from `runtime_config` and falls back
  to the schema default.
- Updating values through the `/config/update` API writes back to
  `runtime_config` and `os.environ` without touching your `.env` file.

When a setting is marked as **critical**, changing it will invalidate the
cached service singletons so that the next request observes the new value.

---

## Contents

- [How configuration is resolved](#how-configuration-is-resolved)
- [Core application](#core-application)
- [Document ingestion](#document-ingestion)
- [ColPali embedding service](#colpali-embedding-service)
- [Qdrant vector database](#qdrant-vector-database)
- [Object storage (MinIO)](#object-storage-minio)
- [MUVERA post-processing](#muvera-post-processing)
- [Operational environment variables](#operational-environment-variables)
- [Runtime updates via API](#runtime-updates-via-api)
- [Troubleshooting](#troubleshooting)

---

## How configuration is resolved

1. `.env` (or the shell environment) is loaded once on startup.
2. `runtime_config` keeps a mutable copy of all key/value pairs.
3. The `config` module exposes typed accessors that:
   - look up the requested key in the schema,
   - coerce it to the correct type,
   - supply computed values for a few convenience settings (for example,
     automatic MinIO worker counts).
4. When `/config/update` or `/config/reset` is called, the runtime cache is
   updated immediately and critical services are invalidated.

If a setting is not listed in the schema it is not exposed through the runtime
API and cannot be changed dynamically.

---

## Core application

| Key             | Type | Default | Notes |
|-----------------|------|---------|-------|
| `LOG_LEVEL`     | str  | `INFO`  | Logging level used for the API and uvicorn loggers (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `ALLOWED_ORIGINS` | list | `*`   | CORS configuration. Supply a comma-separated list for production (for example `https://app.example.com,https://admin.example.com`). |
| `UVICORN_RELOAD` | bool | `True` | Enables auto-reload in development. Disable for production to avoid the filesystem watcher overhead. |

> `ALLOWED_ORIGINS=["*"]` keeps CORS wide open. Always pin explicit origins
> before exposing the API publicly.

---

## Document ingestion

| Key                       | Type | Default | Notes |
|---------------------------|------|---------|-------|
| `BATCH_SIZE`              | int  | `12`    | Number of pages processed per batch. Lower values give steadier progress feedback and reduce peak memory usage. |
| `ENABLE_PIPELINE_INDEXING`| bool | `True`  | Overlaps embedding, MinIO uploads, and Qdrant upserts using a pipelined executor. Disable only when debugging. |

Additional behaviour:

- `config.get_ingestion_worker_threads()` chooses a sensible thread count for
  PDF rasterisation based on `os.cpu_count()`.
- `config.get_pipeline_max_concurrency()` derives how many batches can be in
  flight simultaneously; no environment variable is required.

---

## ColPali embedding service

| Key               | Type | Default              | Notes |
|-------------------|------|----------------------|-------|
| `COLPALI_MODE`    | str  | `gpu`                | Selects the preferred embedding service (`cpu` or `gpu`). |
| `COLPALI_CPU_URL` | str  | `http://localhost:7001` | Base URL for the CPU ColPali service (used when `COLPALI_MODE=cpu`). |
| `COLPALI_GPU_URL` | str  | `http://localhost:7002` | Base URL for the GPU ColPali service (used when `COLPALI_MODE=gpu`). |
| `COLPALI_API_TIMEOUT` | int | `300` seconds | Request timeout applied to all calls to the ColPali API. Increase when indexing large documents on CPU. |

The backend currently selects between the CPU and GPU URLs based on
`COLPALI_MODE`. There is no single "override" URL; supply the correct hostname
and port for the service you want to talk to.

---

## Qdrant vector database

| Key                         | Type  | Default | Notes |
|-----------------------------|-------|---------|-------|
| `QDRANT_URL`                | str   | `http://localhost:6333` | External Qdrant endpoint (ignored when `QDRANT_EMBEDDED=True`). |
| `QDRANT_EMBEDDED`           | bool  | `True`  | Launch an embedded in-memory Qdrant instance. Disable to connect to an external deployment. |
| `QDRANT_COLLECTION_NAME`    | str   | `documents` | Collection name used for all vectors and metadata (also feeds the default MinIO bucket name). |
| `QDRANT_PREFETCH_LIMIT`     | int   | `200`   | Number of multivector candidates prefetched for reranking when mean pooling is enabled. |
| `QDRANT_ON_DISK`            | bool  | `True`  | Store primary vector data on disk (memory-mapped). |
| `QDRANT_ON_DISK_PAYLOAD`    | bool  | `True`  | Store payload data on disk. |
| `QDRANT_USE_BINARY`         | bool  | `False` | Enable binary quantisation. Recommended for very large datasets; keep disabled for maximum recall while prototyping. |
| `QDRANT_BINARY_ALWAYS_RAM`  | bool  | `True`  | Keep the compressed binary vectors in RAM. Only applies when quantisation is enabled. |
| `QDRANT_SEARCH_IGNORE_QUANT`| bool  | `False` | Use full-precision vectors during search even when quantised. |
| `QDRANT_SEARCH_RESCORE`     | bool  | `True`  | Rescore results using full-precision vectors after the quantised search. |
| `QDRANT_SEARCH_OVERSAMPLING`| float | `2.0`   | Oversampling factor used with binary quantisation (searches N× more candidates before rescoring). |
| `QDRANT_MEAN_POOLING_ENABLED` | bool | `False` | Enable mean-pooled row/column vectors for reranking. Leave disabled for maximum indexing speed. |

> Changing `QDRANT_COLLECTION_NAME`, `QDRANT_URL`, or the quantisation options
> invalidates the Qdrant client so the next request will recreate the service.

---

## Object storage (MinIO)

| Key                | Type | Default | Notes |
|--------------------|------|---------|-------|
| `MINIO_ENABLED`    | bool | `False` | Toggle MinIO integration. When disabled, images are embedded inline in Qdrant payloads. |
| `MINIO_URL`        | str  | `http://localhost:9000` | Internal S3 endpoint used by the backend (shown only when MinIO is enabled). |
| `MINIO_PUBLIC_URL` | str  | `http://localhost:9000` | Public URL embedded in payloads. Falls back to `MINIO_URL` when blank. |
| `MINIO_ACCESS_KEY` | str  | `minioadmin` | Access key used to authenticate MinIO requests. Replace in production. |
| `MINIO_SECRET_KEY` | str  | `minioadmin` | Secret key used with the access key. Replace in production. |
| `MINIO_BUCKET_NAME`| str  | *(auto)* | When empty, derived from `QDRANT_COLLECTION_NAME` (slugified). |
| `MINIO_WORKERS`    | int  | *(auto)* | Number of concurrent upload workers. Defaults are computed from CPU count and pipeline concurrency; override only when fine tuning. |
| `MINIO_RETRIES`    | int  | *(auto)* | Retry attempts per upload batch. Computed from the worker count. |
| `MINIO_FAIL_FAST`  | bool | `False` | Abort immediately on the first upload error. Keep disabled for resiliency. |
| `MINIO_PUBLIC_READ`| bool | `True`  | Apply a public-read bucket policy automatically. Disable when you intend to serve images through signed URLs or another private mechanism. |
| `IMAGE_FORMAT`     | str  | `JPEG`  | Format used when storing rendered pages (`JPEG`, `PNG`, or `WEBP`). Applies to both MinIO uploads and inline payloads. |
| `IMAGE_QUALITY`    | int  | `75`    | Quality setting for `JPEG` and `WEBP` images (1-100). Ignored for PNG. |

A few helper methods inside `config.py` compute worker and retry counts when they
are not explicitly set. That keeps the upload pipeline balanced without
managing yet another environment variable.

---

## MUVERA post-processing

| Key                | Type | Default | Notes |
|--------------------|------|---------|-------|
| `MUVERA_ENABLED`   | bool | `False` | Enable MUVERA single-vector encodings for a faster first-stage search. Requires the optional `fastembed[postprocess]` dependency. |
| `MUVERA_K_SIM`     | int  | `6`     | Number of similar tokens sampled when generating MUVERA FDEs. |
| `MUVERA_DIM_PROJ`  | int  | `32`    | Projection dimension for MUVERA vectors. |
| `MUVERA_R_REPS`    | int  | `20`    | Number of repetitions used during MUVERA projection. |
| `MUVERA_RANDOM_SEED` | int | `42`   | Random seed used to keep MUVERA projections reproducible. |

When MUVERA is enabled the backend initialises an additional vector space in Qdrant (`muvera_fde`) and performs first-stage searches against it before
reranking on the original multivectors.

---
## Operational environment variables

The following values are not part of the dynamic schema but are still read by
the runtime:

- `HOST` and `PORT` - consumed by `backend/main.py` when launching uvicorn.
- `LOG_LEVEL` - the environment value takes precedence when spawning uvicorn; it is still exposed through the schema for runtime adjustments.

Because they are not defined in `config_schema.py`, these variables cannot be
updated via the configuration API. Edit your `.env` file or shell environment
and restart the process instead.

---

- `HOST` and `PORT` – consumed by `backend/main.py` when launching uvicorn.
- `LOG_LEVEL` – the environment value takes precedence when spawning uvicorn;
  it is still exposed through the schema for runtime adjustments.

Because they are not defined in `config_schema.py`, these variables cannot be
updated via the configuration API. Edit your `.env` file or shell environment
and restart the process instead.

---

## Runtime updates via API

| Endpoint                 | Description |
|--------------------------|-------------|
| `GET /config/schema`     | Returns the schema used by the UI. |
| `GET /config/values`     | Returns the current runtime values for all keys in the schema. |
| `POST /config/update`    | Accepts `{ "key": "...", "value": "..." }` and updates the runtime configuration. Critical services are invalidated automatically. |
| `POST /config/reset`     | Restores all schema-driven settings to their defaults and clears cached services. |
| `POST /config/optimize`  | Runs the hardware optimiser (`services/system_optimizer.py`) and applies any suggested overrides. |

Remember: runtime changes do **not** persist across restarts. Update `.env` if
you need the new values to survive a rebuild or container restart.

---

## Troubleshooting

- **Value changes do not stick** – make sure the key exists in the schema. Keys
  outside of `config_schema.py` are not exposed via the runtime API.
- **Service still uses the old value** – some settings are cached as part of the
  Qdrant or MinIO services. When a critical key changes the dependency cache is
  cleared; if you update manually (for example via `.env`) restart the process
  to force a reload.
- **MinIO uploads fail intermittently** – consider lowering `BATCH_SIZE`
  or disabling `ENABLE_PIPELINE_INDEXING` temporarily to reduce parallelism.
- **Quantisation toggles are ignored** – ensure Qdrant is initialised after the
  change. For existing collections you may need to clear or recreate the
  collection for new vector layouts to apply.

For a deeper dive into the configuration architecture see
`backend/CONFIGURATION_GUIDE.md`.
