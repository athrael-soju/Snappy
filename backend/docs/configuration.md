# Snappy Configuration Guide - Master Your Settings! ⚙️

Welcome to Snappy's complete configuration reference! This is your go-to guide for every runtime setting in the FastAPI backend. All the magic is defined in `backend/config_schema.py`, which powers:
- 🎛️ The beautiful web configuration panel
- 🔌 The `/config/*` API endpoints
- 📦 The `config` module used throughout the app

**How It Works** 🔧:
- 📚 Defaults are defined in `config_schema.py`
- 🌱 Settings load from your environment (`.env` file) into `runtime_config`
- 🔑 Access via `config.MY_SETTING` (reads from runtime, falls back to defaults)
- ⚡ Updates via `/config/update` API change runtime values instantly (`.env` untouched)

**Critical Settings** 🚨: Some settings are marked as **critical**. Changing these invalidates cached services (Qdrant, MinIO, ColPali) so your next request picks up the new values automatically!

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

## How Configuration Is Resolved 🔍

1. **Startup**: `.env` (or shell environment) loads once
2. **Runtime Store**: `runtime_config` maintains a mutable copy of all settings
3. **Smart Accessors**: The `config` module provides typed access:
   - 🔍 Looks up keys in the schema
   - 🔄 Coerces to the correct type
   - 🧠 Supplies computed values (like auto-sized MinIO workers)
4. **Live Updates**: Calling `/config/update` or `/config/reset` updates the cache instantly and invalidates critical services

🔒 **Important**: Only settings in the schema can be changed dynamically. Everything else requires an environment update + restart.

---

## Core Application 🏛️

| Key             | Type | Default | What It Does |
|-----------------|------|---------|-------------|
| `LOG_LEVEL`     | str  | `INFO`  | Controls verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `ALLOWED_ORIGINS` | list | `*`   | CORS settings. Use `*` for dev, explicit URLs for production! |
| `UVICORN_RELOAD` | bool | `True` | Hot reload in dev. Turn OFF for production (saves resources) |

🚨 **Security Note**: `ALLOWED_ORIGINS=["*"]` is wide open! Lock it down with specific URLs before going live.

---

## Document Ingestion 📚

| Key                       | Type | Default | What It Does |
|---------------------------|------|---------|-------------|
| `BATCH_SIZE`              | int  | `12`    | Pages per batch. Lower = smoother progress, less memory. Higher = faster (but spikier) |
| `ENABLE_PIPELINE_INDEXING`| bool | `True`  | Overlaps embedding, uploads, and upserts for max speed. Disable for debugging only! |

**Smart Defaults** 🧠:
- `config.get_ingestion_worker_threads()` auto-sizes PDF rasterization threads based on your CPU count
- `config.get_pipeline_max_concurrency()` calculates optimal batch concurrency; no manual tuning needed!

---

## ColPali Embedding Service 🧠✨

| Key               | Type | Default              | What It Does |
|-------------------|------|----------------------|-------------|
| `COLPALI_MODE`    | str  | `gpu`                | Choose your weapon: `cpu` or `gpu` |
| `COLPALI_CPU_URL` | str  | `http://localhost:7001` | Where to find the CPU service |
| `COLPALI_GPU_URL` | str  | `http://localhost:7002` | Where to find the GPU service (much faster!) |
| `COLPALI_API_TIMEOUT` | int | `300` seconds | Patience is a virtue! Bump this up for large docs on CPU |

💡 **How It Works**: Snappy picks the right URL based on `COLPALI_MODE`. No single override; just point to the service you want!

---

## Qdrant Vector Database 🕸️

| Key                         | Type  | Default | What It Does |
|-----------------------------|-------|---------|-------------|
| `QDRANT_URL`                | str   | `http://localhost:6333` | External Qdrant endpoint (ignored in embedded mode) |
| `QDRANT_EMBEDDED`           | bool  | `False` | Run Qdrant in-process. Great for testing, not for production! |
| `QDRANT_COLLECTION_NAME`    | str   | `documents` | Collection name (also used for MinIO bucket by default) |
| `QDRANT_PREFETCH_LIMIT`     | int   | `200`   | Multivector candidates for reranking (when mean pooling is on) |
| `QDRANT_ON_DISK`            | bool  | `True`  | Memory-map vectors to disk (saves RAM!) |
| `QDRANT_ON_DISK_PAYLOAD`    | bool  | `True`  | Store payloads on disk too |
| `QDRANT_USE_BINARY`         | bool  | `False` | Binary quantization for huge datasets (trades some recall for speed) |
| `QDRANT_BINARY_ALWAYS_RAM`  | bool  | `True`  | Keep quantized vectors in RAM (faster searches) |
| `QDRANT_SEARCH_IGNORE_QUANT`| bool  | `False` | Skip quantization during search (use full precision) |
| `QDRANT_SEARCH_RESCORE`     | bool  | `True`  | Rescore with full precision after quantized search |
| `QDRANT_SEARCH_OVERSAMPLING`| float | `2.0`   | Fetch 2× candidates before rescoring (improves recall) |
| `QDRANT_MEAN_POOLING_ENABLED` | bool | `False` | Enable row/column pooling for better reranking (slower indexing) |

🔄 **Critical Settings**: Changing collection name, URL, or quantization options refreshes the Qdrant client automatically.

---

## Object Storage (MinIO) 🗄️

| Key                | Type | Default | What It Does |
|--------------------|------|---------|-------------|
| `MINIO_URL`        | str  | `http://localhost:9000` | Internal endpoint for backend uploads |
| `MINIO_PUBLIC_URL` | str  | `http://localhost:9000` | Public URL for browser access (defaults to MINIO_URL) |
| `MINIO_ACCESS_KEY` | str  | `minioadmin` | Access credentials (CHANGE IN PRODUCTION!) |
| `MINIO_SECRET_KEY` | str  | `minioadmin` | Secret credentials (CHANGE IN PRODUCTION!) |
| `MINIO_BUCKET_NAME`| str  | *(auto)* | Bucket name (auto-derived from collection name if blank) |
| `MINIO_WORKERS`    | int  | *(auto)* | Upload workers (auto-sized based on CPU + pipeline) |
| `MINIO_RETRIES`    | int  | *(auto)* | Retry attempts (computed from worker count) |
| `MINIO_FAIL_FAST`  | bool | `False` | Stop on first error? Keep OFF for resilience! |
| `MINIO_PUBLIC_READ`| bool | `True`  | Public bucket policy (turn OFF for private signed URLs) |
| `IMAGE_FORMAT`     | str  | `JPEG`  | Image format: `JPEG`, `PNG`, or `WEBP` |
| `IMAGE_QUALITY`    | int  | `75`    | Quality (1-100) for JPEG/WEBP (PNG ignores this) |

🚨 **MinIO is Required**: No fallback to inline storage anymore! Snappy needs proper object storage to work its magic.

🧠 **Smart Defaults**: The config system auto-calculates worker and retry counts based on your hardware. Less config, more performance!

---

## MUVERA Post-Processing 🚀

| Key                | Type | Default | What It Does |
|--------------------|------|---------|-------------|
| `MUVERA_ENABLED`   | bool | `False` | Speed up searches with single-vector encodings (needs `fastembed[postprocess]`) |
| `MUVERA_K_SIM`     | int  | `6`     | Similar tokens to sample for FDE generation |
| `MUVERA_DIM_PROJ`  | int  | `32`    | Projection dimension (lower = faster, less precise) |
| `MUVERA_R_REPS`    | int  | `20`    | Projection repetitions (more = better quality) |
| `MUVERA_RANDOM_SEED` | int | `42`   | Random seed (keep it consistent for reproducibility!) |

**How It Works** ⚙️: When enabled, Snappy creates an extra vector space (`muvera_fde`) in Qdrant for lightning-fast first-stage searches, then reranks with full multivectors for precision!

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

## Runtime Updates via API 🔌

| Endpoint                 | What It Does |
|--------------------------|-------------|
| `GET /config/schema`     | Get the config blueprint (powers the UI) |
| `GET /config/values`     | See current runtime values |
| `POST /config/update`    | Change a setting instantly (auto-invalidates critical services) |
| `POST /config/reset`     | Back to defaults (clears service cache too) |
| `POST /config/optimize`  | Let Snappy auto-tune based on your hardware! |

💨 **Remember**: Runtime changes are temporary! Update `.env` for permanent tweaks.

---

## Troubleshooting - We've Got Your Back! 🔧

**Changes won't stick?**  
Make sure the key exists in `config_schema.py`. Only schema keys work with the runtime API!

**Service ignoring new values?**  
Some settings are cached in Qdrant/MinIO clients. Critical changes auto-invalidate, but manual `.env` updates need a restart.

**MinIO upload issues?**  
Try lowering `BATCH_SIZE` or temporarily disable `ENABLE_PIPELINE_INDEXING` to reduce load.

**Quantization not working?**  
Qdrant needs to reinitialize. For existing collections, you might need to recreate them for new layouts to apply.

📘 **Deep Dive**: Check `backend/CONFIGURATION_GUIDE.md` for implementation details and best practices!

