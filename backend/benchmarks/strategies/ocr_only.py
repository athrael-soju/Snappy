"""
OCR-only retrieval strategy.

Uses traditional OCR-based text retrieval without vision-language embeddings.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from benchmarks.strategies.base import BaseRetrievalStrategy, RetrievalResult

logger = logging.getLogger(__name__)


class OCROnlyStrategy(BaseRetrievalStrategy):
    """
    OCR-only retrieval strategy.

    This implements traditional text-based retrieval:
    1. Full-text search across OCR-extracted text in DuckDB
    2. Return matching pages with their OCR content
    3. No vision-language embeddings used

    This serves as a baseline to compare against ColPali-based approaches.
    """

    def __init__(
        self,
        duckdb_url: str = "http://localhost:8300",
        collection_name: str = "benchmark_documents",
        # Search settings
        use_fts: bool = True,  # Use DuckDB full-text search
        match_threshold: float = 0.1,  # Minimum match score
        **kwargs,
    ):
        super().__init__(
            duckdb_url=duckdb_url,
            collection_name=collection_name,
            **kwargs,
        )

        self.use_fts = use_fts
        self.match_threshold = match_threshold

        self._session = None

    @property
    def name(self) -> str:
        return "ocr_only"

    @property
    def description(self) -> str:
        return (
            "OCR-only strategy using traditional text search "
            "without vision-language embeddings"
        )

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self._session = requests.Session()

        health = await self.health_check()
        if not health.get("duckdb"):
            raise RuntimeError("DuckDB service not healthy")

        self._initialized = True
        self._logger.info("OCROnlyStrategy initialized")

    async def health_check(self) -> Dict[str, bool]:
        """Check DuckDB service health."""
        health = {}

        try:
            response = self._session.get(f"{self.duckdb_url}/health", timeout=5)
            health["duckdb"] = response.status_code == 200
        except Exception:
            health["duckdb"] = False

        return health

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve relevant documents using OCR text search.

        Args:
            query: Search query text
            top_k: Number of results to retrieve

        Returns:
            RetrievalResult with OCR text context
        """
        result = RetrievalResult()
        total_start = time.perf_counter()

        try:
            # Search OCR text in DuckDB
            search_results = await self._search_ocr_text(query, top_k)

            if not search_results:
                result.error = "No search results found"
                return result

            # Process results
            context_parts = []
            for item in search_results:
                page_num = item.get("page_number", 0)
                text = item.get("text", "") or item.get("markdown", "")
                regions = item.get("regions", [])
                score = item.get("score", 0.0)

                result.retrieved_pages.append(page_num)
                result.scores.append(score)

                if text:
                    context_parts.append(text)

                # Extract bboxes from regions
                for region in regions:
                    bbox = region.get("bbox")
                    if bbox:
                        result.retrieved_bboxes.append(bbox)
                    content = region.get("content", "")
                    if content:
                        result.context_regions.append(region)

            result.context_text = "\n\n".join(context_parts)
            result.raw_response = {"search_results": search_results}

        except Exception as e:
            result.error = str(e)
            self._logger.error(f"Retrieval failed: {e}", exc_info=True)

        result.retrieval_time_ms = (time.perf_counter() - total_start) * 1000

        return result

    async def _search_ocr_text(
        self, query: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search OCR text using DuckDB full-text search.

        This implements keyword-based retrieval as a baseline.
        """
        try:
            if self.use_fts:
                # Use DuckDB's built-in full-text search
                response = await asyncio.to_thread(
                    self._session.post,
                    f"{self.duckdb_url}/search",
                    json={
                        "query": query,
                        "limit": top_k,
                        "include_regions": True,
                    },
                    timeout=30,
                )
            else:
                # Fallback to LIKE-based search
                # Build SQL query for text matching
                sql = f"""
                SELECT
                    filename,
                    page_number,
                    text,
                    markdown,
                    regions
                FROM ocr_pages
                WHERE
                    text ILIKE '%' || $1 || '%'
                    OR markdown ILIKE '%' || $1 || '%'
                ORDER BY page_number
                LIMIT {top_k}
                """

                response = await asyncio.to_thread(
                    self._session.post,
                    f"{self.duckdb_url}/query",
                    json={
                        "sql": sql,
                        "params": [query],
                    },
                    timeout=30,
                )

            if response.status_code != 200:
                self._logger.warning(f"DuckDB search failed: {response.text}")
                return []

            data = response.json()
            return data.get("results", [])

        except Exception as e:
            self._logger.error(f"OCR text search failed: {e}")
            return []

    async def _search_with_bm25(
        self, query: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Alternative: BM25-based retrieval.

        This could be implemented using a dedicated search engine
        or computed in-memory for smaller datasets.
        """
        # Placeholder for BM25 implementation
        # Could integrate with Elasticsearch, Meilisearch, or compute BM25 directly
        return await self._search_ocr_text(query, top_k)

    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        **kwargs,
    ) -> bool:
        """Index documents for OCR-based search."""
        self._logger.warning(
            "OCROnlyStrategy uses shared indexing pipeline. "
            "Documents should be indexed via SnappyFullStrategy."
        )
        return True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            self._session.close()
        await super().cleanup()


class OCRWithEmbeddingsStrategy(OCROnlyStrategy):
    """
    Enhanced OCR strategy with text embeddings.

    Uses OCR-extracted text with dense embeddings for semantic search,
    as an alternative to pure keyword matching.
    """

    def __init__(
        self,
        duckdb_url: str = "http://localhost:8300",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        **kwargs,
    ):
        super().__init__(duckdb_url=duckdb_url, **kwargs)
        self.embedding_model = embedding_model
        self._embedder = None

    @property
    def name(self) -> str:
        return "ocr_with_embeddings"

    @property
    def description(self) -> str:
        return (
            "OCR strategy with dense text embeddings for semantic search "
            "(no vision-language model)"
        )

    async def initialize(self) -> None:
        """Initialize text embedding model."""
        await super().initialize()

        try:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(self.embedding_model)
            self._logger.info(f"Loaded embedding model: {self.embedding_model}")
        except ImportError:
            self._logger.warning(
                "sentence-transformers not installed. "
                "Falling back to keyword search."
            )

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve using semantic search over OCR text.
        """
        if self._embedder is None:
            # Fall back to keyword search
            return await super().retrieve(query, top_k, **kwargs)

        result = RetrievalResult()
        total_start = time.perf_counter()

        try:
            # Generate query embedding
            embed_start = time.perf_counter()
            query_embedding = await asyncio.to_thread(
                self._embedder.encode, query, convert_to_numpy=True
            )
            result.embedding_time_ms = (time.perf_counter() - embed_start) * 1000

            # Search using embeddings
            # This would require a vector store for OCR text embeddings
            # For now, fall back to keyword search
            search_results = await self._search_ocr_text(query, top_k)

            if not search_results:
                result.error = "No search results found"
                return result

            # Process results (same as parent)
            context_parts = []
            for item in search_results:
                page_num = item.get("page_number", 0)
                text = item.get("text", "") or item.get("markdown", "")

                result.retrieved_pages.append(page_num)
                if text:
                    context_parts.append(text)

            result.context_text = "\n\n".join(context_parts)
            result.raw_response = {"search_results": search_results}

        except Exception as e:
            result.error = str(e)
            self._logger.error(f"Retrieval failed: {e}", exc_info=True)

        result.retrieval_time_ms = (time.perf_counter() - total_start) * 1000

        return result
