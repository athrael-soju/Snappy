import logging
from typing import List, Optional, Tuple, Any, Dict
import uuid
import numpy as np
from qdrant_client import QdrantClient, models
from tqdm import tqdm
from PIL import Image

from config import (
    QDRANT_URL, 
    QDRANT_COLLECTION_NAME, 
    BATCH_SIZE, 
    QDRANT_SEARCH_LIMIT, 
    QDRANT_PREFETCH_LIMIT, 
    COLPALI_SERVICE_URL
)
from .minio_service import MinioService
from .colpali_service import ColPaliClient

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, colpali_client: Optional[ColPaliClient] = None):
        """
        Initialize QdrantService with ColPali client.
        
        Args:
            colpali_client: Optional instance of ColPaliClient. 
                          If None, a new instance will be created using COLPALI_SERVICE_URL.
        """
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = QDRANT_COLLECTION_NAME
        
        # Initialize ColPali client
        if colpali_client is None:
            colpali_client = ColPaliClient(base_url=COLPALI_SERVICE_URL)
        self.colpali_client = colpali_client
        
        # Initialize MinIO service for image storage
        try:
            self.minio_service = MinioService()
            if not self.minio_service.health_check():
                raise RuntimeError("MinIO service health check failed")
            logger.info("Successfully connected to MinIO service")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO service: {e}")
            raise
        
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self) -> None:
        """Create Qdrant collection for document storage if it doesn't exist."""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "original": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        ),
                        hnsw_config=models.HnswConfigDiff(m=0)
                    ),
                    "mean_pooling_columns": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        )
                    ),
                    "mean_pooling_rows": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        )
                    )
                }
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.debug(f"Collection {self.collection_name} already exists: {e}")

    def _embed_and_mean_pool_batch(
        self, 
        image_batch: List[Image.Image]
    ) -> Tuple[List[List[float]], List[List[float]], List[List[float]]]:
        """
        Embed images and create mean pooled representations using ColPali client.
        
        Args:
            image_batch: List of PIL Images to process
            
        Returns:
            Tuple of (original_embeddings, pooled_by_rows, pooled_by_columns)
        """
        try:
            return self.colpali_client.encode_images_with_pooling(image_batch)
        except Exception as e:
            logger.error(f"Error encoding image batch: {e}")
            raise RuntimeError(f"Failed to encode images: {e}")

    def index_documents(self, images: List[Image.Image]) -> str:
        """
        Index documents in Qdrant.
        
        Args:
            images: List of PIL Images to index
            
        Returns:
            Status message with number of documents indexed
        """
        batch_size = int(BATCH_SIZE)
        total_docs = 0
        
        with tqdm(total=len(images), desc="Indexing documents") as pbar:
            for i in range(0, len(images), batch_size):
                batch = images[i:i + batch_size]
                
                try:
                    # Get embeddings
                    original_batch, pooled_rows, pooled_cols = self._embed_and_mean_pool_batch(batch)
                    
                    # Store images in MinIO
                    try:
                        image_urls = self.minio_service.store_images_batch(batch)
                    except Exception as e:
                        raise RuntimeError(f"Failed to store images in MinIO: {e}")
                    
                    # Upload to Qdrant
                    for j, (orig, rows, cols, image_url) in enumerate(zip(
                        original_batch, pooled_rows, pooled_cols, image_urls
                    )):
                        doc_id = str(uuid.uuid4())
                        payload = {
                            "index": i + j,
                            "page": f"Page {i + j}",
                            "image_url": image_url,
                            "document_id": doc_id
                        }
                        
                        self.client.upload_collection(
                            collection_name=self.collection_name,
                            vectors={
                                "mean_pooling_columns": np.asarray([cols], dtype=np.float32),
                                "original": np.asarray([orig], dtype=np.float32),
                                "mean_pooling_rows": np.asarray([rows], dtype=np.float32)
                            },
                            payload=[payload],
                            ids=[doc_id]
                        )
                    
                    total_docs += len(batch)
                    pbar.update(len(batch))
                    
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size}: {e}")
                    raise
        
        return f"Successfully indexed {total_docs} documents"

    def search(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Tuple[Image.Image, str]]:
        """
        Search for relevant documents using Qdrant.
        
        Args:
            query: Text query to search for
            k: Number of results to return
            
        Returns:
            List of tuples containing (image, page_info)
        """
        try:
            # Get query embedding
            query_embedding = self._embed_query(query)
            
            # Perform search
            search_results = self._reranking_search_batch([query_embedding])
            
            # Process results
            results = []
            if search_results and search_results[0].points:
                for i, point in enumerate(search_results[0].points[:k]):
                    try:
                        image_url = point.payload.get('image_url')
                        page_info = point.payload.get('page', f"Page {point.payload.get('index', i)}")
                        
                        if image_url and self.minio_service:
                            image = self.minio_service.get_image(image_url)
                            results.append((image, page_info))
                        else:
                            logger.warning(f"Invalid image URL or MinIO service not available for point {i}")
                            
                    except Exception as e:
                        logger.error(f"Error retrieving image for point {i}: {e}")
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search failed: {e}")

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed query text using ColPali client."""
        try:
            return self.colpali_client.encode_query(query).numpy()
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise RuntimeError(f"Query embedding failed: {e}")

    def _reranking_search_batch(
        self, 
        query_batch: List[np.ndarray], 
        search_limit: int = QDRANT_SEARCH_LIMIT, 
        prefetch_limit: int = QDRANT_PREFETCH_LIMIT
    ) -> List[Any]:
        """Perform two-stage retrieval with multivectors."""
        search_queries = [
            models.QueryRequest(
                query=query,
                prefetch=[
                    models.Prefetch(
                        query=query,
                        limit=prefetch_limit,
                        using="mean_pooling_columns"
                    ),
                    models.Prefetch(
                        query=query,
                        limit=prefetch_limit,
                        using="mean_pooling_rows"
                    ),
                ],
                limit=search_limit,
                with_payload=True,
                with_vector=False,
                using="original"
            ) for query in query_batch
        ]
        return self.client.query_batch_points(
            collection_name=self.collection_name,
            requests=search_queries
        )