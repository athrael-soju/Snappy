"""Collection management for Qdrant vector database."""

import logging
from typing import TYPE_CHECKING, Optional

from qdrant_client import QdrantClient, models

if TYPE_CHECKING:
    from services.colpali import ColPaliService

    from backend import config as config  # type: ignore
else:  # pragma: no cover - runtime import for application execution
    import config  # type: ignore

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages Qdrant collection lifecycle operations."""

    def __init__(
        self,
        api_client: Optional["ColPaliService"] = None,
    ):
        """Initialize collection manager.

        Args:
            api_client: ColPali client for getting model dimensions
        """
        try:
            # Store API client (doesn't change)
            self.api_client = api_client
            self._service: Optional[QdrantClient] = None
            # Don't cache config values - read them dynamically via properties
            self._service: Optional[QdrantClient] = None
        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant client: {e}")

    @property
    def service(self) -> QdrantClient:
        """Get Qdrant client, reading URL from current config."""
        if self._service is None:
            if getattr(config, "QDRANT_EMBEDDED", False):
                self._service = QdrantClient(":memory:")
            else:
                timeout = int(getattr(config, "QDRANT_HTTP_TIMEOUT", 5))
                self._service = QdrantClient(
                    url=config.QDRANT_URL,
                    timeout=timeout,
                )
        return self._service

    @property
    def collection_name(self) -> str:
        """Get collection name from current config."""
        return config.QDRANT_COLLECTION_NAME

    @property
    def enable_mean_pooling(self) -> bool:
        """Get mean pooling setting from current config."""
        return config.QDRANT_MEAN_POOLING_ENABLED

    def _get_model_dimension(self) -> int:
        """Get the embedding dimension from the API."""
        if self.api_client is None:
            raise ValueError("ColPali API client is not initialized")
        info = self.api_client.get_info()
        if not info or "dim" not in info:
            raise ValueError(
                "Failed to get model dimension from API. The API might be down or misconfigured."
            )
        return info["dim"]

    def create_collection_if_not_exists(self):
        """Create Qdrant collection for document storage with proper dimension validation."""
        # Return early if the collection already exists
        try:
            self.service.get_collection(self.collection_name)
            logger.info("Using existing Qdrant collection '%s'", self.collection_name)
            return
        except Exception:
            pass

        try:
            # Get the model dimension from API
            model_dim = self._get_model_dimension()

            # Define vector configuration with the correct dimension
            def _vp(include_hnsw: bool = False) -> models.VectorParams:
                quant = (
                    models.BinaryQuantization(
                        binary=models.BinaryQuantizationConfig(
                            always_ram=config.QDRANT_BINARY_ALWAYS_RAM
                        )
                    )
                    if config.QDRANT_USE_BINARY
                    else None
                )
                return models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=(models.HnswConfigDiff(m=0) if include_hnsw else None),
                    on_disk=config.QDRANT_ON_DISK,
                    quantization_config=quant,
                )

            # Build vector config - only include mean pooling if enabled
            vector_config = {"original": _vp(include_hnsw=True)}
            if self.enable_mean_pooling:
                vector_config["mean_pooling_columns"] = _vp()
                vector_config["mean_pooling_rows"] = _vp()

            self.service.create_collection(
                collection_name=self.collection_name,
                vectors_config=vector_config,
                on_disk_payload=config.QDRANT_ON_DISK_PAYLOAD,
            )
            logger.info(
                "Created new collection '%s' with model_dim=%s and vectors: %s",
                self.collection_name,
                model_dim,
                list(vector_config.keys()),
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                model_dim = self._get_model_dimension()
                logger.info(
                    "Using existing collection '%s' with model_dim=%s",
                    self.collection_name,
                    model_dim,
                )
            else:
                raise Exception(f"Failed to create collection: {e}")

    def clear_collection(self) -> str:
        """Delete and recreate the configured collection to remove all points."""
        try:
            self.service.delete_collection(collection_name=self.collection_name)
        except Exception as e:
            # If not exists, ignore and proceed to (re)create
            if "not found" not in str(e).lower():
                raise Exception(f"Failed to delete collection: {e}")

        # Recreate with correct vectors config
        self.create_collection_if_not_exists()
        return f"Cleared Qdrant collection '{self.collection_name}'."

    def health_check(self) -> bool:
        """Check if Qdrant service is healthy and accessible."""
        try:
            _ = self.service.get_collection(self.collection_name)
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def delete_points_by_filename(
        self, filename: str, collection_name: Optional[str] = None
    ) -> int:
        """
        Delete all points associated with a specific filename.

        Args:
            filename: The filename to filter by
            collection_name: Optional collection name (defaults to configured collection)

        Returns:
            Number of points deleted

        Example:
            deleted_count = collection_manager.delete_points_by_filename("document.pdf")
        """
        collection = collection_name or self.collection_name

        try:
            # Create a filter for the filename
            points_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename),
                    )
                ]
            )

            # Count points before deletion (for reporting)
            count_result = self.service.count(
                collection_name=collection, count_filter=points_filter, exact=True
            )
            points_count = count_result.count if hasattr(count_result, "count") else 0

            if points_count == 0:
                logger.info(f"No points found for filename '{filename}' in collection '{collection}'")
                return 0

            # Delete the points
            self.service.delete(collection_name=collection, points_selector=points_filter)

            logger.info(
                f"Deleted {points_count} points for filename '{filename}' from collection '{collection}'"
            )
            return points_count

        except Exception as e:
            logger.error(
                f"Failed to delete points for filename '{filename}' from collection '{collection}': {e}",
                exc_info=True,
            )
            raise Exception(
                f"Failed to delete points for filename '{filename}': {e}"
            )
