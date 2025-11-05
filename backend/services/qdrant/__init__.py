"""Backward compatibility shim for Qdrant integrations."""

from app.integrations.qdrant import (  # noqa: F401
    CollectionManager,
    DocumentIndexer,
    EmbeddingProcessor,
    MuveraPostprocessor,
    QdrantService,
    SearchManager,
)

__all__ = [
    "QdrantService",
    "CollectionManager",
    "EmbeddingProcessor",
    "MuveraPostprocessor",
    "DocumentIndexer",
    "SearchManager",
]
