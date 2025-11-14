"""Qdrant-specific document indexing operations."""

import logging
from typing import Callable, Iterable, Optional

from domain.pipeline import DocumentIndexer as GenericDocumentIndexer
from domain.pipeline import ProcessedBatch

from .points import PointFactory

logger = logging.getLogger(__name__)


class QdrantDocumentIndexer:
    """Qdrant-specific document indexer.

    This wraps the generic DocumentIndexer and adds Qdrant-specific
    point construction and storage logic.
    """

    def __init__(
        self,
        qdrant_client,
        collection_name: str,
        embedding_processor,
        minio_service=None,
        ocr_service=None,
    ):
        """Initialize Qdrant document indexer."""
        self.service = qdrant_client
        self.collection_name = collection_name

        # Create generic pipeline indexer
        self._pipeline = GenericDocumentIndexer(
            embedding_processor=embedding_processor,
            minio_service=minio_service,
            ocr_service=ocr_service,
        )

        # Create Qdrant-specific point factory
        self._point_factory = PointFactory()

    def index_documents(
        self,
        images: Iterable,
        total_images: Optional[int] = None,
        progress_cb: Optional[Callable[[int, dict | None], None]] = None,
    ) -> str:
        """Index documents in Qdrant.

        Uses the generic pipeline and adds Qdrant point construction.
        """

        def store_batch(processed_batch: ProcessedBatch):
            """Convert processed batch to Qdrant points and store."""
            points = self._point_factory.build(
                batch_start=processed_batch.batch_start,
                original_batch=processed_batch.original_embeddings,
                pooled_by_rows_batch=processed_batch.pooled_by_rows,
                pooled_by_columns_batch=processed_batch.pooled_by_columns,
                image_ids=processed_batch.image_ids,
                image_records=processed_batch.image_records,
                meta_batch=processed_batch.meta_batch,
                ocr_results=processed_batch.ocr_results,
            )

            self.service.upsert(
                collection_name=self.collection_name,
                points=points,
            )

        return self._pipeline.index_documents(
            images=images,
            total_images=total_images,
            progress_cb=progress_cb,
            store_batch_cb=store_batch,
        )
