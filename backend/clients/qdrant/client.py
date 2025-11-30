"""Main Qdrant service that orchestrates all operations."""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from clients.colpali import ColPaliClient

from .collection import CollectionManager
from .embedding import EmbeddingProcessor
from .search import SearchManager

logger = logging.getLogger(__name__)


class QdrantClient:
    """Main service class for Qdrant operations.

    Handles document indexing, search, and retrieval with inline image storage.
    """

    def __init__(
        self,
        api_client: Optional["ColPaliClient"] = None,
        ocr_service=None,
    ):
        """Initialize Qdrant service with all subcomponents.

        Args:
            api_client: ColPali client for embeddings
            ocr_service: Optional OCR service for parallel processing
        """
        try:
            # Initialize dependencies
            self.api_client = api_client
            self.ocr_service = ocr_service

            # Initialize subcomponents
            self.collection_manager = CollectionManager(
                api_client=api_client,
            )

            self.embedding_processor = EmbeddingProcessor(
                api_client=api_client,
            )

            self.search_manager = SearchManager(
                qdrant_client=self.collection_manager.service,
                collection_name=self.collection_manager.collection_name,
                embedding_processor=self.embedding_processor,
            )

            # Expose underlying Qdrant client for direct access
            self.service = self.collection_manager.service
            self.collection_name = self.collection_manager.collection_name

        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant service: {e}")

    # Collection management methods
    def _create_collection_if_not_exists(self):
        """Create Qdrant collection if it doesn't exist."""
        return self.collection_manager.create_collection_if_not_exists()

    def clear_collection(self) -> str:
        """Delete and recreate the configured collection to remove all points."""
        return self.collection_manager.clear_collection()

    def health_check(self) -> bool:
        """Check if Qdrant service is healthy and accessible."""
        return self.collection_manager.health_check()

    # Search methods
    def search_with_metadata(
        self,
        query: str,
        k: int = 5,
        payload_filter: Optional[dict] = None,
        include_full_images: bool = False,
    ):
        """Search and return metadata with inline image data.

        Returns search results with payload metadata. Images are stored inline
        as base64-encoded data in the payload.

        Args:
            query: Search query text
            k: Number of results to return
            payload_filter: Optional dict of equality filters
            include_full_images: If True, include full-resolution images
        """
        return self.search_manager.search_with_metadata(
            query, k, payload_filter, include_full_images
        )

    def search(self, query: str, k: int = 5):
        """Search for relevant documents and return metadata.

        This is a convenience wrapper around search_with_metadata().
        Returns thumbnail images for display.
        """
        return self.search_manager.search(query, k)

    def get_point_with_full_image(self, point_id: str) -> Optional[dict]:
        """Retrieve a specific point with full-resolution image data.

        Use this when user wants to view the full image.
        """
        return self.search_manager.get_point_with_full_image(point_id)
