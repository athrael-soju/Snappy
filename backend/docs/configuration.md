# Configuration Reference

This document provides detailed explanations for all configuration options available in the FastAPI backend. All settings are configured via environment variables, typically defined in a `.env` file at the project root.

## Table of Contents

- [Application Settings](#application-settings)
- [Processing & Performance](#processing--performance)
- [ColPali API Configuration](#colpali-api-configuration)
- [Qdrant Vector Database](#qdrant-vector-database)
- [MinIO Object Storage](#minio-object-storage)
- [MUVERA (Optional)](#muvera-optional)

---

## Application Settings

### `LOG_LEVEL`
- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Controls the verbosity of application logging. Use `DEBUG` for development and troubleshooting, `INFO` for production.

### `HOST`
- **Type**: String
- **Default**: `0.0.0.0`
- **Description**: The host address the FastAPI server binds to. Use `0.0.0.0` to accept connections from any network interface, or `127.0.0.1` for localhost only.

### `PORT`
- **Type**: Integer
- **Default**: `8000`
- **Description**: The port number the FastAPI server listens on.

### `ALLOWED_ORIGINS`
- **Type**: String (comma-separated) or `*`
- **Default**: `*`
- **Description**: CORS (Cross-Origin Resource Sharing) configuration. Specifies which origins can access the API.
  - Use `*` to allow all origins (development only)
  - Use comma-separated list for production: `http://localhost:3000,https://yourdomain.com`
- **Security Note**: Never use `*` in production. Always specify exact origins.

---

## Processing & Performance

### `DEFAULT_TOP_K`
- **Type**: Integer
- **Default**: `5`
- **Range**: `1-50`
- **Description**: Default number of search results to return when not specified in the query. Higher values return more results but increase response time.

### `MAX_TOKENS`
- **Default**: `500`
- **Description**: Maximum number of tokens for text generation or processing operations. Primarily used for chat/completion features.

### `BATCH_SIZE`
- **Type**: Integer
- **Default**: `12`
- **Recommended**:
  - **CPU mode**: `1-2` (better progress feedback, lower memory)
  - **GPU mode (consumer)**: `4-12` (GTX/RTX 30xx/40xx with 8-16GB VRAM)
  - **GPU mode (high-end)**: `12-16` (RTX 5090 with 32GB VRAM)
- **Description**: Number of document pages processed per batch during indexing. Larger batches maximize GPU utilization but use more VRAM.
- **Performance Impact**:
{{ ... }}
  - CPU: ~1.5-3 minutes per page
  - GPU: ~1-2 seconds per page
  - 30-50x speed difference between CPU and GPU
- **Memory Usage**: ~2GB VRAM per batch of 8 images (ColQwen2.5), scales linearly

### `WORKER_THREADS`
- **Type**: Integer
- **Default**: `8`
- **Recommended**:
  - **Consumer CPU**: `4-8` (8-16 threads)
  - **High-end CPU**: `8-12` (24+ threads like Ryzen 9 7950X, Threadripper)
- **Description**: Number of worker threads for PDF rasterization (via `pdf2image`). More threads = faster PDF-to-image conversion.
- **Performance Impact**: Directly affects PDF conversion speed (CPU-bound). Use 50-75% of your CPU thread count.

### `ENABLE_PIPELINE_INDEXING`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Enables concurrent batch processing with dual thread pools to overlap embedding (slow), MinIO uploads (I/O), and Qdrant upserts (I/O).
- **Benefits**:
  - 20-40% faster indexing for multi-page documents
  - Better resource utilization (GPU stays busy while I/O happens)
  - Non-blocking upserts allow next batch to start immediately
- **When to Disable**: For single-page documents or when debugging indexing issues.

### `MAX_CONCURRENT_BATCHES`
- **Type**: Integer
- **Default**: `3`
- **Recommended**:
  - **Low RAM (16GB)**: `2`
  - **Medium RAM (32GB)**: `3`
  - **High RAM (64GB+)**: `3-4`
  - **CPU mode**: Stay lower (2-3) due to slower processing
- **Description**: Maximum number of batches processed concurrently when `ENABLE_PIPELINE_INDEXING=True`. Each batch runs in parallel: embedding, MinIO upload, and upsert all overlap.
- **Memory Impact**: Each concurrent batch holds `BATCH_SIZE` images in RAM during processing. Formula: `~200MB × BATCH_SIZE × MAX_CONCURRENT_BATCHES`
- **Example**: `BATCH_SIZE=16, MAX_CONCURRENT_BATCHES=3` → ~9.6GB RAM for image buffers

### `MINIO_IMAGE_QUALITY`
- **Type**: Integer
- **Default**: `75`
- **Range**: `1-100`
- **Description**: JPEG compression quality for images stored in MinIO. Higher values produce better quality but larger files.
- **Recommendations**:
  - **75**: Good balance for most use cases (~80KB per page)
  - **85**: High quality (~100KB per page)
  - **90-95**: Near-lossless quality (~150-200KB per page)
- **Note**: Only applies to JPEG format. PNG is lossless and ignores this setting.

---

## ColPali API Configuration

The ColPali API handles document embedding using vision-language models. You can configure it in two ways:

### Option A: Mode-Based Configuration (Recommended)

#### `COLPALI_MODE`
- **Type**: String
- **Default**: `gpu`
- **Options**: `cpu`, `gpu`
- **Description**: Selects which ColPali API endpoint to use based on available hardware.

#### `COLPALI_CPU_URL`
- **Type**: String (URL)
- **Default**: `http://localhost:7001`
- **Description**: URL for the CPU-based ColPali API service.

#### `COLPALI_GPU_URL`
- **Type**: String (URL)
- **Default**: `http://localhost:7002`
- **Description**: URL for the GPU-based ColPali API service.

### Option B: Explicit Override

#### `COLPALI_API_BASE_URL`
- **Type**: String (URL)
- **Default**: *(empty, uses mode-based selection)*
- **Description**: Explicitly sets the ColPali API endpoint, overriding mode-based selection. Useful for custom deployments or external API services.
- **Priority**: If set, this takes precedence over `COLPALI_MODE`, `COLPALI_CPU_URL`, and `COLPALI_GPU_URL`.

### `COLPALI_API_TIMEOUT`
- **Type**: Integer (seconds)
- **Default**: `300` (5 minutes)
- **Description**: Maximum time to wait for ColPali API responses. Increase for large documents on CPU.
- **Recommendations**:
  - **CPU mode**: `300-600` (5-10 minutes)
  - **GPU mode**: `60-120` (1-2 minutes)

---

## Qdrant Vector Database

Qdrant stores document embeddings and enables semantic search.

### Connection

#### `QDRANT_URL`
- **Type**: String (URL)
- **Default**: `http://localhost:6333`
- **Description**: URL of the Qdrant vector database service.

#### `QDRANT_COLLECTION_NAME`
- **Type**: String
- **Default**: `documents`
- **Description**: Name of the Qdrant collection where document embeddings are stored. Use different names to separate document sets.

### Search Configuration

#### `QDRANT_SEARCH_LIMIT`
- **Type**: Integer
- **Default**: `20`
- **Description**: Maximum number of results returned from Qdrant search. The final result count is determined by `k` in the search query, but this sets an upper bound.

#### `QDRANT_PREFETCH_LIMIT`
- **Type**: Integer
- **Default**: `200`
- **Description**: Number of candidates to retrieve in the first stage of multi-vector search before reranking. Higher values improve recall but increase latency.
- **Performance**: Increase if you notice relevant results being missed.

### Storage Optimization

#### `QDRANT_ON_DISK`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Store vector data on disk instead of RAM. Reduces memory usage significantly with minimal performance impact.
- **Recommendation**: Keep `True` unless you have abundant RAM and need maximum speed.

#### `QDRANT_ON_DISK_PAYLOAD`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Store payload data (metadata) on disk instead of RAM.
- **Recommendation**: Keep `True` for large document collections.

### Binary Quantization

Binary quantization compresses vectors to 1-bit representations, reducing memory usage by ~32x with minimal accuracy loss.

#### `QDRANT_USE_BINARY`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Enable binary quantization for vector compression.
- **Benefits**:
  - 32x memory reduction
  - Faster search (fewer bytes to compare)
  - ~1-2% accuracy loss (acceptable for most use cases)

#### `QDRANT_BINARY_ALWAYS_RAM`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Keep binary quantized vectors in RAM while original vectors stay on disk. Provides speed benefits of quantization without memory overhead of full vectors.
- **Recommendation**: Keep `True` when using binary quantization.

#### `QDRANT_SEARCH_IGNORE_QUANT`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Skip quantized vectors and search directly on original vectors. Disables quantization benefits.
- **Use Case**: Debugging or when maximum accuracy is required.

#### `QDRANT_SEARCH_RESCORE`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Rescore top candidates using original (non-quantized) vectors for improved accuracy.
- **Recommendation**: Keep `True` for best accuracy with quantization.

#### `QDRANT_SEARCH_OVERSAMPLING`
- **Type**: Float
- **Default**: `2.0`
- **Description**: Multiplier for how many candidates to retrieve before rescoring. Higher values improve accuracy but increase latency.
- **Example**: With `SEARCH_LIMIT=20` and `OVERSAMPLING=2.0`, retrieves 40 candidates, then rescores to return top 20.

#### `QDRANT_MEAN_POOLING_ENABLED`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Enable mean pooling computation and two-stage reranking for improved search quality. When disabled, skips mean pooling during indexing and uses simple single-vector search.
- **Benefits of Enabling**:
  - Better search quality through two-stage retrieval
  - Reranking with row/column pooled vectors
  - More robust results for complex queries
- **Benefits of Disabling**:
  - **20-40% faster indexing** (no mean pooling computation)
  - Lower storage requirements (no mean pooling vectors)
  - Simpler search pipeline
  - Ideal for small-scale deployments or rapid prototyping
- **Recommendation**: 
  - **Enable** (`True`) for production with large document collections where search quality is critical
  - **Disable** (`False`) for development, testing, or small-scale loads where indexing speed matters more

---

## MinIO Object Storage

MinIO stores document images and provides public URLs for retrieval.

### Connection

#### `MINIO_URL`
- **Type**: String (URL)
- **Default**: `http://localhost:9000`
- **Description**: Internal MinIO API endpoint. Used by the backend to upload/download images.

#### `MINIO_PUBLIC_URL`
- **Type**: String (URL)
- **Default**: *(same as `MINIO_URL`)*
- **Description**: Public URL for accessing stored images. Used in URLs returned to services.
- **Use Case**: Set differently from `MINIO_URL` when MinIO is behind a reverse proxy or load balancer.
- **Example**: `MINIO_URL=http://minio:9000` (internal), `MINIO_PUBLIC_URL=https://storage.yourdomain.com` (public)

### Authentication

#### `MINIO_ACCESS_KEY`
- **Type**: String
- **Default**: `minioadmin`
- **Description**: MinIO access key (username). Change from default in production.

#### `MINIO_SECRET_KEY`
- **Type**: String
- **Default**: `minioadmin`
- **Description**: MinIO secret key (password). Change from default in production.
- **Security**: Use strong, randomly generated secrets in production.

### Storage Configuration

#### `MINIO_BUCKET_NAME`
- **Type**: String
- **Default**: *(derived from `QDRANT_COLLECTION_NAME`)*
- **Description**: Name of the MinIO bucket where images are stored. When left unset the backend slugifies `QDRANT_COLLECTION_NAME` to build the bucket name and creates it automatically if it does not exist.

#### `MINIO_PUBLIC_READ`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Automatically set bucket policy to allow public read access. Required for images to be accessible via URLs.
- **Security**: Images will be publicly accessible. Don't store sensitive documents without additional access controls.

### Image Processing

#### `MINIO_IMAGE_FMT`
- **Type**: String
- **Default**: `JPEG` (optimized for balance of quality and compression)
- **Options**: `PNG`, `JPEG`, `WEBP`
- **Description**: Image format for storing document pages.
- **Recommendations**:
  - **PNG**: Lossless, larger files (~500KB per page), best quality - use when file size isn't a concern
  - **JPEG**: Lossy, smaller files (~80-200KB per page depending on quality), excellent visual quality - **recommended for most use cases**
  - **WEBP**: Modern format, best compression, may have compatibility issues with older browsers
- **Note**: When using JPEG, adjust `MINIO_IMAGE_QUALITY` (75=good balance, 90-95=near-lossless quality)

### Performance Tuning

#### `MINIO_WORKERS`
- **Type**: Integer
- **Default**: *auto (CPU cores x pipeline concurrency)*
- **Description**: Auto-sized concurrency for MinIO uploads. The backend inspects available CPU cores and pipeline concurrency to choose a safe level.
- **Manual Override**: Set via environment variable when you need to cap concurrency for bandwidth-limited or shared clusters.
- **Performance Impact**: Each worker handles one upload at a time; higher values use more network and CPU.
- **Note**: HTTP connection pool is automatically sized to `MINIO_WORKERS x MAX_CONCURRENT_BATCHES + 10` to prevent connection exhaustion
#### `MINIO_RETRIES`
- **Type**: Integer
- **Default**: *auto (derived from worker concurrency)*
- **Description**: Retry attempts for failed MinIO operations (total attempts = retries + 1). Auto-sizing increases retries when concurrency is high to smooth over transient failures.
- **Manual Override**: Adjust via environment variables when operating across unreliable links or when strict failure detection is preferred.
#### `MINIO_FAIL_FAST`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Stop entire batch upload on first failure. Leave disabled unless you are debugging a failure mode that needs immediate aborts.
- **Manual Override**: Hidden from the default UI; toggle via environment variables only for diagnostics.
---

## MUVERA (Optional)

MUVERA (Multi-Vector Embedding Reduction Algorithm) creates single-vector representations from multi-vector embeddings for faster first-stage retrieval.

### `MUVERA_ENABLED`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Enable MUVERA for faster search with large document collections.
- **Benefits**:
  - 10-50x faster first-stage retrieval
  - Maintains accuracy through multi-vector reranking
- **Trade-offs**:
  - Additional memory for single-vector index
  - Slight overhead during indexing

### `MUVERA_K_SIM`
- **Type**: Integer
- **Default**: `6`
- **Description**: Number of most similar vectors to consider when creating the fixed-dimensional encoding.
- **Impact**: Higher values capture more information but increase computation.

### `MUVERA_DIM_PROJ`
- **Type**: Integer
- **Default**: `32`
- **Description**: Dimensionality of the projected single-vector representation.
- **Trade-off**: Higher dimensions = better accuracy, more memory.

### `MUVERA_R_REPS`
- **Type**: Integer
- **Default**: `20`
- **Description**: Number of random projections used in the encoding process.
- **Impact**: More repetitions improve stability but increase computation time.

### `MUVERA_RANDOM_SEED`
- **Type**: Integer
- **Default**: `42`
- **Description**: Random seed for reproducible MUVERA projections. Use the same seed across restarts to maintain consistent encodings.

---

## Configuration Examples

### Development (CPU, Small Documents)

```bash
# Application
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=*

# Processing
BATCH_SIZE=1
ENABLE_PIPELINE_INDEXING=False
MAX_CONCURRENT_BATCHES=1

# ColPali
COLPALI_MODE=cpu
COLPALI_API_TIMEOUT=300

# Qdrant - Disable mean pooling for faster indexing
QDRANT_MEAN_POOLING_ENABLED=False

# Storage
MINIO_IMAGE_FMT=JPEG
MINIO_IMAGE_QUALITY=75
```

### Production (GPU, Large Collections)

```bash
# Application
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Processing
BATCH_SIZE=12
ENABLE_PIPELINE_INDEXING=True
MAX_CONCURRENT_BATCHES=3
WORKER_THREADS=8

# ColPali
COLPALI_MODE=gpu
COLPALI_API_TIMEOUT=120

# Qdrant
QDRANT_USE_BINARY=True
QDRANT_SEARCH_RESCORE=True
QDRANT_MEAN_POOLING_ENABLED=False

# MinIO
MINIO_IMAGE_FMT=JPEG
MINIO_IMAGE_QUALITY=75
MINIO_PUBLIC_URL=https://storage.yourdomain.com

# MUVERA (for large collections)
MUVERA_ENABLED=True
```

### High-Quality Archival

```bash
# Prioritize quality over storage/speed
MINIO_IMAGE_FMT=PNG  # Lossless
BATCH_SIZE=2
QDRANT_USE_BINARY=False  # No quantization
QDRANT_SEARCH_RESCORE=True
QDRANT_MEAN_POOLING_ENABLED=False
```

---

## Performance Tuning Guide

### For Faster Indexing

1. **Use GPU**: Set `COLPALI_MODE=gpu` (30-50x faster)
2. **Disable mean pooling**: `QDRANT_MEAN_POOLING_ENABLED=False` (20-40% faster, already default)
3. **Increase batch size**: `BATCH_SIZE=12-16` (GPU only)
4. **Enable pipelining**: `ENABLE_PIPELINE_INDEXING=True` (already default)
5. **More concurrent batches**: `MAX_CONCURRENT_BATCHES=3-4`
6. **Lower image quality**: `MINIO_IMAGE_QUALITY=75` (already default)

### For Lower Memory Usage

1. **Reduce batch size**: `BATCH_SIZE=1-2`
2. **Fewer concurrent batches**: `MAX_CONCURRENT_BATCHES=1-2`
3. **Enable disk storage**: `QDRANT_ON_DISK=True`, `QDRANT_ON_DISK_PAYLOAD=True`
4. **Use binary quantization**: `QDRANT_USE_BINARY=True`

### For Better Search Quality

1. **Enable mean pooling reranking**: `QDRANT_MEAN_POOLING_ENABLED=True`
2. **Disable quantization**: `QDRANT_USE_BINARY=False`
3. **Increase prefetch**: `QDRANT_PREFETCH_LIMIT=500`
4. **Enable rescoring**: `QDRANT_SEARCH_RESCORE=True`
5. **Higher oversampling**: `QDRANT_SEARCH_OVERSAMPLING=3.0`

### For Large Document Collections (1M+ pages)

1. **Enable MUVERA**: `MUVERA_ENABLED=True`
2. **Use binary quantization**: `QDRANT_USE_BINARY=True` (already default)
3. **Disk storage**: `QDRANT_ON_DISK=True` (already default)
4. **Lower image quality**: `MINIO_IMAGE_QUALITY=75` (already default)

---

## Troubleshooting

### Indexing is too slow
- Check `COLPALI_MODE` (GPU is 30-50x faster)
- Disable mean pooling: `QDRANT_MEAN_POOLING_ENABLED=False` (20-40% faster)
- Increase `BATCH_SIZE` (GPU only)
- Enable `ENABLE_PIPELINE_INDEXING=True`
- Increase `MAX_CONCURRENT_BATCHES`

### Out of memory errors
- Reduce `BATCH_SIZE`
- Reduce `MAX_CONCURRENT_BATCHES`
- Enable `QDRANT_ON_DISK=True`
- Use `QDRANT_USE_BINARY=True`

### Search results are poor
- Enable mean pooling reranking: `QDRANT_MEAN_POOLING_ENABLED=True`
- Disable quantization: `QDRANT_USE_BINARY=False`
- Enable rescoring: `QDRANT_SEARCH_RESCORE=True`
- Increase `QDRANT_PREFETCH_LIMIT`

### Images fail to upload
- Check MinIO is running and accessible
- Verify `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
- Increase `MINIO_RETRIES`
- Check `MINIO_PUBLIC_READ=True`

### CORS errors in browser
- Add your frontend URL to `ALLOWED_ORIGINS`
- Never use `*` in production

---

## Security Considerations

1. **Change default credentials**: Update `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
2. **Restrict CORS**: Set specific origins in `ALLOWED_ORIGINS`
3. **Use HTTPS**: Configure `MINIO_PUBLIC_URL` with HTTPS in production
4. **Secure secrets**: Use environment variables, never commit secrets to git
5. **Network isolation**: Run services in private networks when possible

---

## See Also

- [Architecture Documentation](./architecture.md)
- [Analysis Documentation](./analysis.md)
- [.env.example](../../.env.example) - Complete example configuration
