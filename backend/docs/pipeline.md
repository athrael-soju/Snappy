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
from services.pipeline import DocumentIndexer, ProcessedBatch
from services.qdrant.indexing import PointFactory

# Create generic indexer
indexer = DocumentIndexer(
    embedding_processor=embedding_service,
    minio_service=minio,
)

# Create Qdrant-specific point factory
point_factory = PointFactory(muvera_post=muvera)

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

## Migration Notes

This package was created by extracting generic components from `services/qdrant/indexing/`:

- `progress.py` → `pipeline/progress.py`
- `storage.py` → `pipeline/storage.py`
- `utils.py` → `pipeline/utils.py`
- `processor.py` → `pipeline/batch_processor.py`
- `document_indexer.py` → `pipeline/document_indexer.py`

Qdrant-specific code remains in `services/qdrant/indexing/`:
- `points.py` - Qdrant PointStruct construction
- `qdrant_indexer.py` - Qdrant-specific wrapper
