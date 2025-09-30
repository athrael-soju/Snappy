# Qdrant Client Module

This module has been refactored for better separation of concerns from a single monolithic file into multiple focused modules.

## Module Structure

### `service.py` - Main Service Orchestrator
Main entry point that coordinates all Qdrant operations. The `QdrantService` class:
- Initializes all subcomponents
- Exposes a unified API for the rest of the application
- Maintains backward compatibility with the original interface

**Public Methods:**
- `index_documents(images, progress_cb)` - Index documents with metadata
- `search(query, k)` - Search for relevant documents
- `search_with_metadata(query, k, payload_filter)` - Search with filters
- `get_image_from_url(image_url)` - Retrieve image from MinIO
- `clear_collection()` - Delete and recreate collection
- `health_check()` - Check service health

### `collection.py` - Collection Management
Handles Qdrant collection lifecycle operations:
- Creating collections with proper vector configurations
- Managing MUVERA vector space
- Collection deletion and recreation
- Health checks

**Key Class:** `CollectionManager`

### `embedding.py` - Embedding & Pooling Operations
Handles image embedding and token pooling:
- Image embedding via ColPali API
- Mean pooling by rows and columns
- Parallel pooling for performance on high-core systems
- Query embedding

**Key Class:** `EmbeddingProcessor`

### `indexing.py` - Document Indexing
Manages document indexing workflows:
- Sequential batch processing
- Pipelined processing for maximum throughput
- MinIO image storage integration
- MUVERA FDE computation
- Progress tracking and cancellation support

**Key Class:** `DocumentIndexer`

**Processing Modes:**
1. **Sequential** - Process one batch fully before starting next
2. **Pipelined** - Overlap embedding, storage, and upserting (controlled by `ENABLE_PIPELINE_INDEXING`)

### `search.py` - Search Operations
Handles search and retrieval:
- Two-stage retrieval with MUVERA-first (when enabled)
- Multi-vector reranking
- Payload filtering
- Quantization-aware search parameters

**Key Class:** `SearchManager`

## Configuration

All configuration is loaded from environment variables (no hardcoded fallbacks):

### Required Variables
- `QDRANT_URL` - Qdrant server URL
- `QDRANT_COLLECTION_NAME` - Collection name for documents

### Optional Variables
- `BATCH_SIZE` - Batch size for processing (default: 12)
- `QDRANT_SEARCH_LIMIT` - Search result limit (default: 20)
- `QDRANT_PREFETCH_LIMIT` - Prefetch limit for multi-vector search (default: 200)
- `QDRANT_ON_DISK` - Store vectors on disk (default: True)
- `QDRANT_ON_DISK_PAYLOAD` - Store payloads on disk (default: True)
- `QDRANT_USE_BINARY` - Enable binary quantization (default: True)
- `QDRANT_BINARY_ALWAYS_RAM` - Keep binary quantization in RAM (default: True)
- `QDRANT_SEARCH_IGNORE_QUANT` - Ignore quantization during search (default: False)
- `QDRANT_SEARCH_RESCORE` - Rescore results (default: True)
- `QDRANT_SEARCH_OVERSAMPLING` - Oversampling factor (default: 2.0)
- `ENABLE_PIPELINE_INDEXING` - Enable pipelined processing (default: True)
- `MAX_CONCURRENT_BATCHES` - Max concurrent batches in pipeline (default: 3)
- `MINIO_IMAGE_QUALITY` - JPEG quality for stored images (default: 85)

## Usage

```python
from services.qdrant import QdrantService

# Initialize service (typically done via dependency injection)
service = QdrantService(
    api_client=colpali_client,
    minio_service=minio_service,
    muvera_post=muvera_postprocessor,  # Optional
)

# Index documents
result = service.index_documents(images, progress_callback)

# Search
results = service.search("query text", k=5)

# Search with filters
results = service.search_with_metadata(
    query="query text",
    k=5,
    payload_filter={"filename": "doc.pdf"}
)
```

## Design Principles

1. **No Hardcoded Values** - All configuration from environment variables
2. **No Fallbacks** - Explicit errors for missing configuration
3. **Separation of Concerns** - Each module has a single responsibility
4. **Backward Compatibility** - Public API unchanged from original
5. **Dependency Injection** - Services injected at initialization
6. **Explicit Error Handling** - No silent failures

## Refactoring Benefits

- **Maintainability** - Easier to locate and modify specific functionality
- **Testability** - Each module can be tested independently
- **Readability** - Smaller, focused files are easier to understand
- **Extensibility** - New features can be added to appropriate modules
- **Performance** - No functional changes; all optimizations retained

## Dependencies

- `qdrant-client` - Qdrant vector database client
- `numpy` - Numerical operations for embeddings
- `PIL` - Image processing
- `tqdm` - Progress bars

## No Regressions

This refactoring maintains 100% functional compatibility:
- All public methods preserved
- All configuration handling unchanged
- All optimizations retained (parallel pooling, pipelined indexing)
- All error handling preserved
- All progress tracking maintained
