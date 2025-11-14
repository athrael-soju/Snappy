# Pipeline Processing Package

This package provides **vector-database-agnostic** pipeline components for document indexing.

---

## Overview

The pipeline package handles the core processing flow for document indexing:
- Batch processing coordination
- Image storage management
- Embedding generation coordination
- OCR processing (optional)
- Progress tracking and cancellation

---

## Architecture

### Key Principles

1. **Separation of Concerns**: Pipeline logic is independent of vector database implementation
2. **Reusability**: Components can be used with Qdrant, Pinecone, Weaviate, or any other vector DB
3. **Callback Pattern**: Database-specific operations (like point construction) are delegated via callbacks

### Components

#### `DocumentIndexer`
Main orchestrator that coordinates the entire indexing pipeline:
- Handles sequential vs pipelined processing modes
- Manages batch iteration
- Coordinates progress tracking
- Delegates storage via callback pattern

```python
indexer = DocumentIndexer(
    embedding_processor=embedding_service,
    minio_service=minio,
    ocr_service=ocr,
)

indexer.index_documents(
    images=image_list,
    progress_cb=my_progress_handler,
    store_batch_cb=my_storage_handler,  # DB-specific
)
```

#### `BatchProcessor`
Processes individual batches:
- Generates embeddings
- Stores images in MinIO
- Runs OCR (if enabled)
- Returns `ProcessedBatch` with all metadata

#### `ImageStorageHandler`
Manages image persistence in MinIO:
- Format conversion
- Quality optimization
- Hierarchical storage structure

#### `ProgressNotifier`
Lightweight progress callback orchestration:
- Stage tracking
- Cancellation support
- Error handling

#### `ProcessedBatch`
Data class containing all processed batch data:
- Embeddings (original + pooled variants)
- Image metadata
- Storage URLs
- OCR results

---

## Usage with Vector Databases

### Qdrant Example

```python
from domain.pipeline import DocumentIndexer, ProcessedBatch
from clients.qdrant.indexing import PointFactory

# Create generic indexer
indexer = DocumentIndexer(
    embedding_processor=embedding_service,
    minio_service=minio,
)

# Create Qdrant-specific point factory
point_factory = PointFactory()

def store_in_qdrant(batch: ProcessedBatch):
    """Qdrant-specific storage logic."""
    points = point_factory.build(
        batch_start=batch.batch_start,
        original_batch=batch.original_embeddings,
        # ... other batch data
    )
    qdrant_client.upsert(points=points)

# Run indexing with Qdrant storage
indexer.index_documents(
    images=images,
    store_batch_cb=store_in_qdrant,
)
```

### Other Vector DBs

The same pipeline can work with any vector database by providing an appropriate `store_batch_cb`:

```python
def store_in_pinecone(batch: ProcessedBatch):
    """Pinecone-specific storage logic."""
    vectors = [
        (id, embedding, metadata)
        for id, embedding, metadata in zip(
            batch.image_ids,
            batch.original_embeddings,
            batch.meta_batch,
        )
    ]
    pinecone_index.upsert(vectors=vectors)

indexer.index_documents(
    images=images,
    store_batch_cb=store_in_pinecone,
)
```

---

## Benefits

1. **Reduced Coupling**: Vector DB changes don't affect core pipeline logic
2. **Testability**: Pipeline components can be tested independently
3. **Flexibility**: Easy to add new vector databases
4. **Maintainability**: Clear separation between generic and DB-specific code

---

## Cancellation Service

The `CancellationService` (`cancellation.py`) provides comprehensive job cleanup and service management.

### Features

- **Multi-Service Coordination**: Cleans up data across Qdrant, MinIO, DuckDB, and filesystem
- **Service Restart**: Optionally restarts ColPali and DeepSeek OCR services to stop ongoing processing
- **Progress Tracking**: Reports cleanup progress via callbacks for SSE streaming
- **Graceful Error Handling**: Continues cleanup even if individual services fail
- **Batch Operations**: Supports cleanup of multiple jobs simultaneously

### Usage

```python
from domain.pipeline.cancellation import CancellationService

# Initialize with service dependencies
cancellation = CancellationService(
    minio_service=minio,
    duckdb_service=duckdb,
    qdrant_collection_manager=qdrant,
    colpali_client=colpali,
    ocr_client=ocr,
)

# Cleanup a single job
result = cancellation.cleanup_job_data(
    job_id="uuid-123",
    filename="document.pdf",
    collection_name="documents",
    restart_services=True,
    progress_callback=lambda percent, msg: print(f"{percent}% - {msg}"),
)

# Result contains detailed cleanup status
{
    "job_id": "uuid-123",
    "filename": "document.pdf",
    "restart_results": {
        "colpali": {"success": true, "message": "Restarted in 2.3s"},
        "deepseek_ocr": {"success": true, "message": "Restarted in 1.8s"}
    },
    "cleanup_results": {
        "qdrant": {"success": true, "points_deleted": 15},
        "minio": {"success": true, "objects_deleted": 45},
        "duckdb": {"success": true, "records_deleted": "unknown"},
        "temp_files": {"success": true, "files_removed": 2}
    },
    "overall_success": true,
    "errors": []
}
```

### Service Restart

The restart mechanism provides immediate termination of long-running operations:

- Sends HTTP POST to `/restart` endpoint on ColPali and DeepSeek OCR services
- Services exit immediately and rely on Docker restart policy to come back online
- Optional health check polling verifies services are operational before continuing
- Configurable timeout (default: 30s) prevents indefinite waiting
- Two-phase verification: down detection → up detection

---

## Migration Notes

This package was created by extracting generic components from `clients/qdrant/indexing/`:

- `progress.py` → `domain/pipeline/progress.py`
- `storage.py` → `domain/pipeline/storage.py`
- `utils.py` → `domain/pipeline/utils.py`
- `processor.py` → `domain/pipeline/batch_processor.py`
- `document_indexer.py` → `domain/pipeline/document_indexer.py`

New additions to the pipeline package:
- `cancellation.py` - Job cancellation and cleanup coordination

Qdrant-specific code remains in `clients/qdrant/indexing/`:
- `points.py` - Qdrant PointStruct construction
- `qdrant_indexer.py` - Qdrant-specific wrapper
