# Snappy Configuration Guide ⚙️

Snappy uses a simplified configuration approach with sensible defaults that work well for most use cases. The system automatically optimizes settings based on your hardware.

This document lists the user-facing configuration options. Internal optimizations (binary quantization, mean pooling, parallelism) are handled automatically for best performance.

---

## Contents

- [Quick Start](#quick-start)
- [Core Configuration](#core-configuration)
- [How Configuration Works](#how-configuration-works)
- [Configuration Reference](#configuration-reference)
- [Advanced Features (Enterprise)](#advanced-features-enterprise)
- [Runtime Updates via API](#runtime-updates-via-api)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update essential settings:
   ```bash
   QDRANT_COLLECTION_NAME=your-collection-name
   OPENAI_API_KEY=your-api-key  # For chat feature
   ```

3. Optionally adjust:
   - `BATCH_SIZE` (2-4 for CPU, 4-8 for GPU)
   - `DEEPSEEK_OCR_ENABLED` (true to enable OCR)
   - `UPLOAD_MAX_FILES` / `UPLOAD_MAX_FILE_SIZE_MB` (upload limits)

4. Start with Docker:
   ```bash
   docker compose up
   ```

That's it! The system auto-configures parallelism, quantization, and pooling for optimal performance.

---

## Core Configuration

**What You Control:**
- Collection names and upload limits
- OCR mode (quality vs speed)
- Batch size (affects memory usage)
- Search result limit
- Mean pooling re-ranking (two-stage retrieval for better accuracy)

**What's Automatic:**
- Binary quantization (32x memory reduction)
- Parallelism (CPU/GPU workers, connection pools)
- Storage optimization (disk vs RAM)

---

## How Configuration Works

1. `.env` loads on startup
2. Hard-coded optimizations apply automatically:
   - Binary quantization: Always ON
   - Auto-config mode: Always ON
3. System auto-sizes:
   - Pipeline concurrency (based on CPU cores)
   - MinIO workers (based on CPU + concurrency)
   - Connection pools (based on workers)

Runtime updates via `/config/*` API take effect immediately but don't persist across restarts; update `.env` for permanent changes.

---

## Configuration Reference

### Core Application

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8000` | CORS origins (comma-separated). ⚠️ Use specific URLs in production! |

---

### Qdrant Vector Database

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_COLLECTION_NAME` | `documents` | Collection name (also used for MinIO bucket) |
| `QDRANT_EMBEDDED` | `false` | Use embedded Qdrant (single-machine only) |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant service URL |
| `QDRANT_SEARCH_LIMIT` | `20` | Number of search results to return |
| `QDRANT_MEAN_POOLING_ENABLED` | `false` | Enable two-stage retrieval with mean pooling for improved accuracy |
| `QDRANT_PREFETCH_LIMIT` | `200` | Number of candidates to prefetch when mean pooling is enabled |

**Note:** Binary quantization and disk storage are automatically enabled for optimal performance. Mean pooling is configurable and requires the ColPali model to support the `/patches` endpoint (enabled in `colmodernvbert`).

---

### Document Processing

| Variable | Default | Description |
|----------|---------|-------------|
| `BATCH_SIZE` | `4` | Pages per batch. Use 2-4 for CPU, 4-8 for GPU |

**Note:** Pipeline concurrency auto-adjusts based on CPU cores and batch size.

---

### Upload Controls

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_MAX_FILE_SIZE_MB` | `10` | Maximum file size (1-200 MB) |
| `UPLOAD_MAX_FILES` | `5` | Maximum files per upload (1-20) |

---

### ColPali Embedding Service

| Variable | Default | Description |
|----------|---------|-------------|
| `COLPALI_URL` | `http://localhost:7000` | ColPali service endpoint |

**Note:** API timeouts auto-adjust based on GPU availability (120s for GPU, 300s for CPU).

---

### DeepSeek OCR (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_OCR_ENABLED` | `true` | Enable OCR for text extraction |
| `DEEPSEEK_OCR_URL` | `http://localhost:8200` | DeepSeek OCR service URL |
| `DEEPSEEK_OCR_MODE` | `Gundam` | Quality mode: `Tiny` (fast), `Small`, `Gundam` (balanced), `Base`, `Large` (high quality) |
| `DEEPSEEK_OCR_TASK` | `markdown` | Task type: `markdown` (structured), `plain_ocr` (simple text) |

**Note:** Worker threads and connection pools auto-size based on GPU availability.

---

### MinIO Object Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_URL` | `http://localhost:9000` | MinIO service URL |
| `MINIO_PUBLIC_URL` | `http://localhost:9000` | Public URL for image links |
| `MINIO_ACCESS_KEY` | `minioadmin` | ⚠️ Change in production! |
| `MINIO_SECRET_KEY` | `minioadmin` | ⚠️ Change in production! |
| `MINIO_PUBLIC_READ` | `true` | Allow public read access |

**Note:** Upload workers, retry attempts, image format (JPEG), and quality (75) are auto-configured.

---

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend API URL (for browser) |
| `PUBLIC_MINIO_URL_SET` | `true` | Replace localhost with service name in Docker |

---

### OpenAI (Chat Feature)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `your-api-key-here` | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4` | Model to use |
| `OPENAI_TEMPERATURE` | `0.7` | Creativity (0.0-1.0) |

---

## Advanced Features (Enterprise)

These features add complexity but provide additional capabilities for enterprise deployments:

### DuckDB Analytics
Disabled by default. Provides SQL-based analytics on OCR data.

```bash
DUCKDB_ENABLED=false  # Set to true to enable
```

### Fine-Grained Control
The simplified open-source version uses optimized defaults. Enterprise deployments can access:
- Custom quantization parameters
- Manual parallelism control
- Advanced pooling strategies
- Performance profiling
- Multi-GPU orchestration

Contact for enterprise licensing and advanced configuration options.

---

## Runtime Updates via API

| Endpoint | Purpose |
|----------|---------|
| `GET /config/schema` | Fetch schema metadata |
| `GET /config/values` | Inspect current runtime values |
| `POST /config/update` | Set a single value (doesn't persist) |
| `POST /config/reset` | Restore defaults |

**Note:** Changes via API don't persist across restarts. Update `.env` for permanent changes.

---

## Troubleshooting

### Performance

**Problem:** Slow indexing on CPU
- **Solution:** Set `BATCH_SIZE=2` to reduce memory usage and provide better progress feedback

**Problem:** GPU memory issues
- **Solution:** Reduce `BATCH_SIZE` or switch to `DEEPSEEK_OCR_MODE=Small`

### Configuration

**Problem:** Changes not taking effect
- **Solution:** Restart services after modifying `.env`. Runtime API updates don't persist.

**Problem:** Upload failures
- **Solution:** Check `UPLOAD_MAX_FILE_SIZE_MB` limit or try reducing `BATCH_SIZE`

### Deployment

**Problem:** CORS errors in browser
- **Solution:** Update `ALLOWED_ORIGINS` with your frontend domain (don't use `*` in production)

**Problem:** MinIO connection errors
- **Solution:** Verify `MINIO_URL` is accessible from backend container (use service name in Docker)

---

## What's Automatic vs Manual

| Feature | Configuration | Notes |
|---------|--------------|-------|
| Binary quantization | ✅ Automatic | Always ON (32x memory reduction) |
| Disk storage | ✅ Automatic | Always ON (memory optimization) |
| Pipeline concurrency | ✅ Automatic | Based on CPU cores + batch size |
| MinIO workers | ✅ Automatic | Based on CPU cores + concurrency |
| Connection pools | ✅ Automatic | Based on worker counts |
| Image format/quality | ✅ Automatic | JPEG @ 75% (good balance) |
| Mean pooling re-ranking | 🎛️ Manual | Two-stage retrieval (better accuracy, more compute) |
| Batch size | 🎛️ Manual | User choice (affects memory) |
| Upload limits | 🎛️ Manual | User choice (security/UX) |
| OCR mode | 🎛️ Manual | User choice (speed vs quality) |
| Collection name | 🎛️ Manual | User choice (organization) |

---

For implementation details, see `backend/config/application.py` which contains the hard-coded optimizations and auto-sizing logic.
