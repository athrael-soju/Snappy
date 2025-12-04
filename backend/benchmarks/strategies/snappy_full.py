"""
Snappy Full retrieval strategy.

Uses ColPali + OCR + Spatially-Grounded Region Relevance Propagation
as described in the research paper.
"""

import asyncio
import logging
import time
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from benchmarks.strategies.base import BaseRetrievalStrategy, RetrievalResult

logger = logging.getLogger(__name__)


class SnappyFullStrategy(BaseRetrievalStrategy):
    """
    Full Snappy retrieval strategy with spatially-grounded region relevance.

    This implements the complete pipeline:
    1. Query embedding via ColPali
    2. Two-stage vector search in Qdrant
    3. OCR region retrieval from DuckDB
    4. Region relevance filtering via interpretability maps
    5. Context extraction from relevant regions
    """

    def __init__(
        self,
        colpali_url: str = "http://localhost:7000",
        qdrant_url: str = "http://localhost:6333",
        duckdb_url: str = "http://localhost:8300",
        minio_url: str = "http://localhost:9000",
        collection_name: str = "benchmark_documents",
        # Region relevance settings
        region_relevance_threshold: float = 0.3,
        region_top_k: int = 10,
        region_score_aggregation: str = "max",
        # Search settings
        use_mean_pooling: bool = True,
        prefetch_limit: int = 100,
        **kwargs,
    ):
        super().__init__(
            colpali_url=colpali_url,
            qdrant_url=qdrant_url,
            duckdb_url=duckdb_url,
            minio_url=minio_url,
            collection_name=collection_name,
            **kwargs,
        )

        self.region_relevance_threshold = region_relevance_threshold
        self.region_top_k = region_top_k
        self.region_score_aggregation = region_score_aggregation
        self.use_mean_pooling = use_mean_pooling
        self.prefetch_limit = prefetch_limit

        # Clients (initialized lazily)
        self._colpali_client = None
        self._qdrant_client = None
        self._duckdb_client = None
        self._session = None

    @property
    def name(self) -> str:
        return "snappy_full"

    @property
    def description(self) -> str:
        return (
            "Full Snappy strategy with ColPali embeddings, OCR regions, "
            "and spatially-grounded region relevance propagation"
        )

    async def initialize(self) -> None:
        """Initialize clients for all required services."""
        from clients.colpali import ColPaliClient

        self._colpali_client = ColPaliClient(
            base_url=self.colpali_url,
            timeout=60,
        )

        # Initialize HTTP session for API calls
        self._session = requests.Session()

        # Verify services are healthy
        health = await self.health_check()
        if not all(health.values()):
            unhealthy = [k for k, v in health.items() if not v]
            raise RuntimeError(f"Services not healthy: {unhealthy}")

        self._initialized = True
        self._logger.info("SnappyFullStrategy initialized")

    async def health_check(self) -> Dict[str, bool]:
        """Check health of required services."""
        health = {}

        # Check ColPali
        try:
            if self._colpali_client:
                health["colpali"] = self._colpali_client.health_check()
            else:
                health["colpali"] = False
        except Exception:
            health["colpali"] = False

        # Check Qdrant
        try:
            response = self._session.get(f"{self.qdrant_url}/healthz", timeout=5)
            health["qdrant"] = response.status_code == 200
        except Exception:
            health["qdrant"] = False

        # Check DuckDB
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
        include_regions: bool = True,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve relevant documents using full Snappy pipeline.

        Args:
            query: Search query text
            top_k: Number of results to retrieve
            include_regions: Whether to include OCR regions
            **kwargs: Additional parameters

        Returns:
            RetrievalResult with retrieved documents and context
        """
        result = RetrievalResult()
        total_start = time.perf_counter()

        try:
            # Step 1: Generate query embedding
            embed_start = time.perf_counter()
            query_embedding = await asyncio.to_thread(
                self._colpali_client.embed_queries, query
            )
            result.embedding_time_ms = (time.perf_counter() - embed_start) * 1000

            # Step 2: Vector search in Qdrant
            search_start = time.perf_counter()
            search_results = await self._search_qdrant(query_embedding[0], top_k)
            result.retrieval_time_ms = (time.perf_counter() - search_start) * 1000

            if not search_results:
                result.error = "No search results found"
                return result

            # Step 3: Process results and fetch OCR regions
            context_parts = []
            retrieved_bboxes = []

            for item in search_results:
                payload = item.get("payload", {})
                score = item.get("score", 0.0)

                result.retrieved_pages.append(payload.get("pdf_page_index", 0))
                result.scores.append(score)

                if include_regions:
                    # Fetch OCR regions from DuckDB
                    filename = payload.get("filename")
                    page_num = payload.get("pdf_page_index")

                    if filename and page_num is not None:
                        regions = await self._fetch_ocr_regions(filename, page_num)

                        if regions:
                            # Apply region relevance filtering
                            filter_start = time.perf_counter()
                            filtered_regions = await self._filter_regions(
                                query=query,
                                regions=regions,
                                image_url=payload.get("image_url"),
                                page_width=payload.get("page_width_px"),
                                page_height=payload.get("page_height_px"),
                            )
                            result.region_filtering_time_ms += (
                                time.perf_counter() - filter_start
                            ) * 1000

                            # Extract context from filtered regions
                            for region in filtered_regions:
                                content = region.get("content", "")
                                if content:
                                    context_parts.append(content)
                                    result.context_regions.append(region)

                                bbox = region.get("bbox")
                                if bbox:
                                    retrieved_bboxes.append(bbox)

            result.context_text = "\n\n".join(context_parts)
            result.retrieved_bboxes = retrieved_bboxes
            result.raw_response = {"search_results": search_results}

        except Exception as e:
            result.error = str(e)
            self._logger.error(f"Retrieval failed: {e}", exc_info=True)

        # Total time
        result.retrieval_time_ms = (time.perf_counter() - total_start) * 1000 - (
            result.region_filtering_time_ms
        )

        return result

    async def _search_qdrant(
        self, query_embedding: List[List[float]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Execute vector search in Qdrant."""
        # Prepare search request
        if self.use_mean_pooling:
            # Two-stage search with prefetch
            request = {
                "query": query_embedding,
                "prefetch": [
                    {
                        "query": query_embedding,
                        "limit": self.prefetch_limit,
                        "using": "mean_pooling_columns",
                    },
                    {
                        "query": query_embedding,
                        "limit": self.prefetch_limit,
                        "using": "mean_pooling_rows",
                    },
                ],
                "limit": top_k,
                "with_payload": True,
                "using": "original",
            }
        else:
            request = {
                "query": query_embedding,
                "limit": top_k,
                "with_payload": True,
                "using": "original",
            }

        response = await asyncio.to_thread(
            self._session.post,
            f"{self.qdrant_url}/collections/{self.collection_name}/points/query",
            json=request,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Qdrant search failed: {response.text}")

        data = response.json()
        points = data.get("result", {}).get("points", [])

        return [
            {"payload": p.get("payload", {}), "score": p.get("score", 0.0)}
            for p in points
        ]

    async def _fetch_ocr_regions(
        self, filename: str, page_num: int
    ) -> List[Dict[str, Any]]:
        """Fetch OCR regions from DuckDB."""
        try:
            response = await asyncio.to_thread(
                self._session.get,
                f"{self.duckdb_url}/pages/{filename}/{page_num}/regions",
                timeout=10,
            )

            if response.status_code == 200:
                return response.json().get("regions", [])
        except Exception as e:
            self._logger.warning(f"Failed to fetch OCR regions: {e}")

        return []

    async def _filter_regions(
        self,
        query: str,
        regions: List[Dict[str, Any]],
        image_url: Optional[str],
        page_width: Optional[int],
        page_height: Optional[int],
    ) -> List[Dict[str, Any]]:
        """
        Filter regions using interpretability-based relevance scoring.

        This implements the Patch-to-Region Relevance Propagation from the paper.
        """
        if not regions or not image_url:
            return regions

        try:
            # Fetch the image
            img_response = await asyncio.to_thread(
                self._session.get, image_url, timeout=10
            )
            if img_response.status_code != 200:
                return regions

            image = Image.open(BytesIO(img_response.content))

            # Generate interpretability maps
            interp_result = await asyncio.to_thread(
                self._colpali_client.generate_interpretability_maps,
                query,
                image,
            )

            similarity_maps = interp_result.get("similarity_maps", [])
            n_patches_x = interp_result.get("n_patches_x", 0)
            n_patches_y = interp_result.get("n_patches_y", 0)
            image_width = interp_result.get("image_width", page_width or image.width)
            image_height = interp_result.get("image_height", page_height or image.height)

            if not similarity_maps or not n_patches_x or not n_patches_y:
                return regions

            # Import the region relevance module
            from domain.region_relevance import filter_regions_by_relevance

            filtered = filter_regions_by_relevance(
                regions=regions,
                similarity_maps=similarity_maps,
                n_patches_x=n_patches_x,
                n_patches_y=n_patches_y,
                image_width=image_width,
                image_height=image_height,
                threshold=self.region_relevance_threshold,
                top_k=self.region_top_k if self.region_top_k > 0 else None,
                aggregation=self.region_score_aggregation,
            )

            return filtered

        except Exception as e:
            self._logger.warning(f"Region filtering failed: {e}")
            return regions

    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        **kwargs,
    ) -> bool:
        """
        Index documents for retrieval.

        Note: For benchmarking, we typically use the existing Snappy
        indexing pipeline. This method is for direct API usage.
        """
        # For full indexing, use the Snappy backend API
        try:
            for doc in documents:
                response = await asyncio.to_thread(
                    self._session.post,
                    f"{self.minio_url.replace('9000', '8000')}/api/index",
                    files={"file": doc.get("file")},
                    timeout=300,
                )
                if response.status_code != 200:
                    self._logger.error(f"Indexing failed: {response.text}")
                    return False

            return True

        except Exception as e:
            self._logger.error(f"Index failed: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            self._session.close()
        await super().cleanup()
