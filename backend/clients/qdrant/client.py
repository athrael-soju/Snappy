"""Main Qdrant service that orchestrates all operations."""

import logging
from typing import TYPE_CHECKING, Callable, Iterable, Optional

from PIL import Image

from .collection import CollectionManager
from .embedding import EmbeddingProcessor
from .search import SearchManager

if TYPE_CHECKING:
    from clients.colpali import ColPaliClient
    from clients.minio import MinioClient

logger = logging.getLogger(__name__)


class QdrantClient:
    """Main service class for Qdrant operations."""

    def __init__(
        self,
        api_client: Optional["ColPaliClient"] = None,
        minio_service: Optional["MinioClient"] = None,
        ocr_service=None,
    ):
        """Initialize Qdrant service with all subcomponents.

        Args:
            api_client: ColPali client for embeddings
            minio_service: MinIO service for image storage
            ocr_service: Optional OCR service for parallel processing
        """
        try:
            if minio_service is None:
                raise ValueError("MinIO service is required for QdrantClient")

            # Initialize dependencies
            self.api_client = api_client
            self.minio_service = minio_service
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
        self, query: str, k: int = 5, payload_filter: Optional[dict] = None
    ):
        """Search and return metadata with image URLs.

        Returns search results with payload metadata including image_url.
        Images are NOT fetched from MinIO to optimize latency - the frontend
        uses URLs directly for display and chat.

        payload_filter: optional dict of equality filters, e.g.
          {"filename": "doc.pdf", "pdf_page_index": 3}
        """
        return self.search_manager.search_with_metadata(query, k, payload_filter)

    def search(self, query: str, k: int = 5):
        """Search for relevant documents and return metadata with URLs.

        This is a convenience wrapper around search_with_metadata().
        Use get_image_from_url() to fetch PIL images from the returned URLs.
        """
        return self.search_manager.search(query, k)

    # Image retrieval
    def get_image_from_url(self, image_url: str) -> Image.Image:
        """Fetch a PIL Image from MinIO by URL.

        Use this when you need the actual image object (e.g., for server-side processing).
        The main search flow returns URLs to avoid unnecessary downloads.
        """
        if not image_url:
            raise Exception("No image reference provided")
        if not self.minio_service:
            raise Exception("MinIO service not available")
        return self.minio_service.get_image(image_url)
