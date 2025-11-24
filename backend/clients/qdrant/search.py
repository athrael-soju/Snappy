"""Search operations for Qdrant."""

import logging
from typing import List, Optional

import config  # Import module for dynamic config access
import numpy as np
from api.utils import compute_page_label
from qdrant_client import models

logger = logging.getLogger(__name__)


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

    def reranking_search_batch(
        self,
        query_embeddings_batch: List[np.ndarray],
        search_limit: Optional[int] = None,
        prefetch_limit: Optional[int] = None,
        qdrant_filter: Optional[models.Filter] = None,
    ):
        """Perform two-stage retrieval with prefetch and multivector rerank.

        If QDRANT_MEAN_POOLING_ENABLED is False, performs simple single-vector search.
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
        search_queries = []
        for query_embedding in query_embeddings_batch:
            if not config.QDRANT_MEAN_POOLING_ENABLED:
                # Simple single-vector search without reranking
                logger.info("Search using simple single-vector (mean pooling disabled)")
                req = models.QueryRequest(
                    query=query_embedding.tolist(),
                    limit=search_limit,
                    with_payload=True,
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
                    with_payload=True,
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
        self, query: str, k: int = 5, payload_filter: Optional[dict] = None
    ):
        """Search and return metadata with image URLs.

        Returns search results with payload metadata including image_url.
        Images are NOT fetched from MinIO to optimize latency - the frontend
        uses URLs directly for display and chat.

        payload_filter: optional dict of equality filters, e.g.
          {"filename": "doc.pdf", "pdf_page_index": 3}
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
        # Ensure we request at least k results from Qdrant; otherwise k>QDRANT_SEARCH_LIMIT
        # would be silently capped by the default.
        effective_limit = max(int(k), 1)
        search_results = self.reranking_search_batch(
            [query_embedding], search_limit=effective_limit, qdrant_filter=q_filter
        )

        items = []
        if search_results and search_results[0].points:
            for i, point in enumerate(search_results[0].points[:k]):
                image_url = point.payload.get("image_url") if point.payload else None
                if not image_url:
                    logger.warning(f"Point {i} missing image_url in payload")
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
        """Search for relevant documents and return metadata with URLs.

        This is a convenience wrapper around search_with_metadata().
        Use get_image_from_url() to fetch PIL images from the returned URLs.
        """
        return self.search_with_metadata(query, k)
