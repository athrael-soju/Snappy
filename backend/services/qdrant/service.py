"""Main Qdrant service that orchestrates all operations."""

import logging
from typing import TYPE_CHECKING, Callable, Iterable, Optional

from PIL import Image

from .collection import CollectionManager
from .embedding import EmbeddingProcessor, MuveraPostprocessor
from .indexing import DocumentIndexer
from .search import SearchManager

if TYPE_CHECKING:
    from services.colpali import ColPaliService
    from services.minio import MinioService
    from services.paddleocr import PaddleOCRService

logger = logging.getLogger(__name__)


class QdrantService:
    """Main service class for Qdrant operations."""

    def __init__(
        self,
        api_client: Optional["ColPaliService"] = None,
        minio_service: Optional["MinioService"] = None,
        muvera_post: Optional[MuveraPostprocessor] = None,
        ocr_service: Optional["PaddleOCRService"] = None,
    ):
        """Initialize Qdrant service with all subcomponents.

        Args:
            api_client: ColPali client for embeddings
            minio_service: MinIO service for image storage
            muvera_post: Optional MUVERA postprocessor
        """
        try:
            if minio_service is None:
                raise ValueError("MinIO service is required for QdrantService")

            # Initialize dependencies
            self.api_client = api_client
            self.minio_service = minio_service
            self.muvera_post = muvera_post
            self.ocr_service = ocr_service

            # Initialize subcomponents
            self.collection_manager = CollectionManager(
                api_client=api_client,
                muvera_post=muvera_post,
            )

            self.embedding_processor = EmbeddingProcessor(
                api_client=api_client,
            )

            self.indexer = DocumentIndexer(
                qdrant_client=self.collection_manager.service,
                collection_name=self.collection_manager.collection_name,
                embedding_processor=self.embedding_processor,
                minio_service=minio_service,
                muvera_post=muvera_post,
                ocr_service=ocr_service,
            )

            self.search_manager = SearchManager(
                qdrant_client=self.collection_manager.service,
                collection_name=self.collection_manager.collection_name,
                embedding_processor=self.embedding_processor,
                muvera_post=muvera_post,
            )

            # Expose client for backward compatibility
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

    # Indexing methods
    def index_documents(
        self,
        images: Iterable,
        total_images: Optional[int] = None,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
    ):
        """Index documents in Qdrant with rich payload metadata.

        Accepts either an iterable of PIL Images or dictionaries containing an
        ``image`` key and optional metadata such as ``filename`` and
        ``pdf_page_index``. When streaming an iterator, ``total_images`` must be
        supplied so that progress reporting remains accurate.
        """
        self._create_collection_if_not_exists()
        return self.indexer.index_documents(
            images,
            total_images=total_images,
            progress_cb=progress_cb,
        )

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
        For backwards compatibility, use get_image_from_url() to fetch PIL images.
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
