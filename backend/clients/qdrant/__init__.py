"""Qdrant client package with separation of concerns."""

from .client import QdrantClient
from .collection import CollectionManager
from .embedding import EmbeddingProcessor
from .search import SearchManager

__all__ = [
    "QdrantClient",
    "CollectionManager",
    "EmbeddingProcessor",
    "SearchManager",
]
