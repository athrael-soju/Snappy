"""Qdrant client package with separation of concerns."""

from .collection import CollectionManager
from .embedding import EmbeddingProcessor
from .indexing import QdrantDocumentIndexer
from .search import SearchManager
from .service import QdrantService

__all__ = [
    "QdrantService",
    "CollectionManager",
    "EmbeddingProcessor",
    "QdrantDocumentIndexer",
    "SearchManager",
]
