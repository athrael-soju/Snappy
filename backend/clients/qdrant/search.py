"""Search operations for Qdrant."""

import logging
import numpy as np
from typing import List, Optional
from qdrant_client import models

from config import (
    QDRANT_SEARCH_LIMIT,
    QDRANT_PREFETCH_LIMIT,
    QDRANT_USE_BINARY,
    QDRANT_SEARCH_IGNORE_QUANT,
    QDRANT_SEARCH_RESCORE,
    QDRANT_SEARCH_OVERSAMPLING,
)
from api.utils import compute_page_label

logger = logging.getLogger(__name__)


class SearchManager:
    """Handles search operations in Qdrant."""

    def __init__(
        self,
        qdrant_client,
        collection_name: str,
        embedding_processor,
        muvera_post=None,
    ):
        """Initialize search manager.
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection
            embedding_processor: EmbeddingProcessor instance
            muvera_post: Optional MUVERA postprocessor
        """
        self.client = qdrant_client
        self.collection_name = collection_name
        self.embedding_processor = embedding_processor
        self.muvera_post = muvera_post

    def reranking_search_batch(
        self,
        query_embeddings_batch: List[np.ndarray],
        search_limit: int = QDRANT_SEARCH_LIMIT,
        prefetch_limit: int = QDRANT_PREFETCH_LIMIT,
        qdrant_filter: Optional[models.Filter] = None,
    ):
        """Perform two-stage retrieval with MUVERA-first (if enabled) and multivector rerank."""
        # Optional quantization-aware search params
        params = None
        if QDRANT_USE_BINARY:
            params = models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=QDRANT_SEARCH_IGNORE_QUANT,
                    rescore=QDRANT_SEARCH_RESCORE,
                    oversampling=QDRANT_SEARCH_OVERSAMPLING,
                )
            )
        search_queries = []
        for query_embedding in query_embeddings_batch:
            # If MUVERA available, compute query FDE
            muvera_query = None
            if self.muvera_post and self.muvera_post.enabled:
                try:
                    muvera_query = self.muvera_post.process_query(query_embedding.tolist())
                    logger.debug("MUVERA query FDE generated: len=%s", len(muvera_query) if muvera_query else None)
                except Exception as e:
                    logger.warning("MUVERA query FDE failed, falling back: %s", e)
                    muvera_query = None

            if muvera_query is not None:
                # First-stage using MUVERA single-vector, prefetch multivectors for rerank
                logger.info("Search using MUVERA first-stage with prefetch for rerank")
                req = models.QueryRequest(
                    query=muvera_query,
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
                    using="muvera_fde",
                    filter=qdrant_filter,
                    params=params,
                )
            else:
                # Fallback: original multivector pipeline
                logger.info("Search using multivector-only pipeline (MUVERA unavailable)")
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
        return self.client.query_batch_points(
            collection_name=self.collection_name, requests=search_queries
        )

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
                image_url = (
                    point.payload.get("image_url") if point.payload else None
                )
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
        For backwards compatibility, use get_image_from_url() to fetch PIL images.
        """
        return self.search_with_metadata(query, k)
