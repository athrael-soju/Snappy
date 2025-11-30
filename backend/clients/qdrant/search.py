"""Search operations for Qdrant."""

import logging
from typing import List, Optional

import config  # Import module for dynamic config access
import numpy as np
from api.utils import compute_page_label
from qdrant_client import models

logger = logging.getLogger(__name__)

# Large payload fields to exclude by default for performance
EXCLUDE_LARGE_FIELDS = ["image_data_full"]


class SearchManager:
    """Handles search operations in Qdrant."""

    def __init__(
        self,
        qdrant_client,
        collection_name: str,
        embedding_processor,
    ):
        """Initialize search manager.

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection
            embedding_processor: EmbeddingProcessor instance
        """
        self.service = qdrant_client
        self.collection_name = collection_name
        self.embedding_processor = embedding_processor

    def _build_payload_selector(
        self, include_full_images: bool = False
    ) -> models.PayloadSelectorExclude:
        """Build payload selector to exclude large fields.

        Args:
            include_full_images: If True, include full-resolution image data

        Returns:
            PayloadSelectorExclude with appropriate exclusions
        """
        if include_full_images:
            # Include everything
            return True

        # Exclude large fields for performance
        return models.PayloadSelectorExclude(exclude=EXCLUDE_LARGE_FIELDS)

    def reranking_search_batch(
        self,
        query_embeddings_batch: List[np.ndarray],
        search_limit: Optional[int] = None,
        prefetch_limit: Optional[int] = None,
        qdrant_filter: Optional[models.Filter] = None,
        include_full_images: bool = False,
    ):
        """Perform two-stage retrieval with prefetch and multivector rerank.

        If QDRANT_MEAN_POOLING_ENABLED is False, performs simple single-vector search.

        Args:
            query_embeddings_batch: List of query embeddings
            search_limit: Maximum number of results
            prefetch_limit: Number of candidates for reranking
            qdrant_filter: Optional filter conditions
            include_full_images: If True, include full-resolution image data
        """
        # Use config defaults if not specified
        if search_limit is None:
            search_limit = config.QDRANT_SEARCH_LIMIT
        if prefetch_limit is None:
            prefetch_limit = config.QDRANT_PREFETCH_LIMIT

        # Optional quantization-aware search params
        params = None
        if config.QDRANT_USE_BINARY_QUANTIZATION:
            params = models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=config.QDRANT_SEARCH_IGNORE_QUANTIZATION,
                    rescore=config.QDRANT_SEARCH_RESCORE,
                    oversampling=config.QDRANT_SEARCH_OVERSAMPLING,
                )
            )

        # Build payload selector
        payload_selector = self._build_payload_selector(include_full_images)

        search_queries = []
        for query_embedding in query_embeddings_batch:
            if not config.QDRANT_MEAN_POOLING_ENABLED:
                # Simple single-vector search without reranking
                logger.info("Search using simple single-vector (mean pooling disabled)")
                req = models.QueryRequest(
                    query=query_embedding.tolist(),
                    limit=search_limit,
                    with_payload=payload_selector,
                    with_vector=False,
                    using="original",
                    filter=qdrant_filter,
                    params=params,
                )
            else:
                # Two-stage search with prefetch and rerank
                logger.info(
                    "Search using multivector pipeline with prefetch and rerank"
                )
                req = models.QueryRequest(
                    query=query_embedding.tolist(),
                    prefetch=[
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_columns",
                        ),
                        models.Prefetch(
                            query=query_embedding.tolist(),
                            limit=prefetch_limit,
                            using="mean_pooling_rows",
                        ),
                    ],
                    limit=search_limit,
                    with_payload=payload_selector,
                    with_vector=False,
                    using="original",
                    filter=qdrant_filter,
                    params=params,
                )
            search_queries.append(req)
        try:
            return self.service.query_batch_points(
                collection_name=self.collection_name, requests=search_queries
            )
        except ValueError as exc:
            if "not found" in str(exc).lower():
                logger.warning(
                    "Qdrant collection '%s' missing during search; returning empty results",
                    self.collection_name,
                )
                return []
            raise

    def search_with_metadata(
        self,
        query: str,
        k: int = 5,
        payload_filter: Optional[dict] = None,
        include_full_images: bool = False,
    ):
        """Search and return metadata with inline image data.

        Returns search results with payload metadata. For inline storage,
        image_data contains base64-encoded thumbnail for display.

        Args:
            query: Search query text
            k: Number of results to return
            payload_filter: Optional dict of equality filters
            include_full_images: If True, include full-resolution image data

        Returns:
            List of search result items with payload, label, and score
        """
        query_embedding = self.embedding_processor.batch_embed_query([query])
        q_filter = None
        if payload_filter:
            try:
                conditions = []
                for kf, vf in payload_filter.items():
                    conditions.append(
                        models.FieldCondition(
                            key=str(kf), match=models.MatchValue(value=vf)
                        )
                    )
                q_filter = models.Filter(must=conditions) if conditions else None
            except Exception:
                q_filter = None

        # Ensure we request at least k results from Qdrant
        effective_limit = max(int(k), 1)
        search_results = self.reranking_search_batch(
            [query_embedding],
            search_limit=effective_limit,
            qdrant_filter=q_filter,
            include_full_images=include_full_images,
        )

        items = []
        if search_results and search_results[0].points:
            for i, point in enumerate(search_results[0].points[:k]):
                if not point.payload:
                    logger.warning(f"Point {i} has no payload")
                    continue

                # Check for inline image data or URL
                has_inline = point.payload.get("image_inline", False)
                has_image_data = point.payload.get("image_data") is not None

                if not has_inline and not has_image_data:
                    # No image data available
                    logger.warning(f"Point {i} has no image data")
                    continue

                items.append(
                    {
                        "payload": point.payload,
                        "label": compute_page_label(point.payload),
                        "score": getattr(point, "score", None),
                    }
                )
        return items

    def search(self, query: str, k: int = 5):
        """Search for relevant documents and return metadata.

        This is a convenience wrapper around search_with_metadata().
        Returns thumbnail image data for display.
        """
        return self.search_with_metadata(query, k)

    def get_point_with_full_image(self, point_id: str) -> Optional[dict]:
        """Retrieve a specific point with full-resolution image data.

        Use this to fetch the full image when user wants to view details.

        Args:
            point_id: The page_id/point ID to retrieve

        Returns:
            Point payload with full image data, or None if not found
        """
        try:
            result = self.service.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False,
            )
            if result and len(result) > 0:
                return result[0].payload
            return None
        except Exception as exc:
            logger.error(f"Failed to retrieve point {point_id}: {exc}")
            return None
