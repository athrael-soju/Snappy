"""Collection management for Qdrant vector database."""

import logging
from typing import Optional
from qdrant_client import QdrantClient, models

from config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    QDRANT_ON_DISK,
    QDRANT_ON_DISK_PAYLOAD,
    QDRANT_USE_BINARY,
    QDRANT_BINARY_ALWAYS_RAM,
    QDRANT_MEAN_POOLING_ENABLED,
)

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages Qdrant collection lifecycle operations."""

    def __init__(
        self,
        api_client=None,
        muvera_post: Optional[object] = None,
    ):
        """Initialize collection manager.
        
        Args:
            api_client: ColPali client for getting model dimensions
            muvera_post: Optional MUVERA postprocessor for FDE embeddings
        """
        try:
            self.service = QdrantClient(url=QDRANT_URL)
            self.collection_name = QDRANT_COLLECTION_NAME
            self.api_client = api_client
            self.muvera_post = muvera_post
            self.enable_mean_pooling = QDRANT_MEAN_POOLING_ENABLED
        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant client: {e}")

    def _get_model_dimension(self) -> int:
        """Get the embedding dimension from the API."""
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
            coll = self.service.get_collection(self.collection_name)
            logger.info("Qdrant collection '%s' exists; checking MUVERA vector space", self.collection_name)
            # If MUVERA is enabled, ensure vector exists and has correct size
            if self.muvera_post and self.muvera_post.embedding_size:
                try:
                    vectors = coll.vectors_count or {}
                    # Try to fetch current vector config
                    coll_info = self.service.get_collection(self.collection_name)
                    # If 'muvera_fde' is missing, add it via update
                    if not getattr(coll_info.config.params, "vectors", None) or (
                        isinstance(coll_info.config.params.vectors, dict)
                        and "muvera_fde" not in coll_info.config.params.vectors
                    ):
                        logger.info(
                            "Adding MUVERA vector 'muvera_fde' (dim=%s) to existing collection",
                            int(self.muvera_post.embedding_size),
                        )
                        self.service.update_collection(
                            collection_name=self.collection_name,
                            vectors_config={
                                "muvera_fde": models.VectorParams(
                                    size=int(self.muvera_post.embedding_size),
                                    distance=models.Distance.COSINE,
                                    on_disk=QDRANT_ON_DISK,
                                )
                            },
                        )
                except Exception:
                    # Best-effort; if we can't introspect, proceed
                    logger.warning("Could not verify or add MUVERA vector space; proceeding without update")
                    pass
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
                            always_ram=QDRANT_BINARY_ALWAYS_RAM
                        )
                    )
                    if QDRANT_USE_BINARY
                    else None
                )
                return models.VectorParams(
                    size=model_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=(models.HnswConfigDiff(m=0) if include_hnsw else None),
                    on_disk=QDRANT_ON_DISK,
                    quantization_config=quant,
                )

            # Build vector config - only include mean pooling if enabled
            vector_config = {"original": _vp(include_hnsw=True)}
            if self.enable_mean_pooling:
                vector_config["mean_pooling_columns"] = _vp()
                vector_config["mean_pooling_rows"] = _vp()

            # Add MUVERA single-vector space if enabled
            if self.muvera_post and self.muvera_post.embedding_size:
                vector_config["muvera_fde"] = models.VectorParams(
                    size=int(self.muvera_post.embedding_size),
                    distance=models.Distance.COSINE,
                    on_disk=QDRANT_ON_DISK,
                )

            self.service.create_collection(
                collection_name=self.collection_name,
                vectors_config=vector_config,
                on_disk_payload=QDRANT_ON_DISK_PAYLOAD,
            )
            logger.info("Created new collection '%s' with model_dim=%s and vectors: %s", self.collection_name, model_dim, list(vector_config.keys()))
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
