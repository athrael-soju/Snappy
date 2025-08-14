import uuid
import numpy as np
from typing import List
from PIL import Image
from qdrant_client import QdrantClient, models
from tqdm import tqdm

from config import QDRANT_URL, QDRANT_COLLECTION_NAME, BATCH_SIZE, QDRANT_SEARCH_LIMIT, QDRANT_PREFETCH_LIMIT
from .minio_service import MinioService
from .colqwen_api_client import ColQwenAPIClient


class QdrantService:
    def __init__(self, api_client: ColQwenAPIClient = None):
        # Initialize Qdrant client
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = QDRANT_COLLECTION_NAME
        
        # Use API client for embeddings
        self.api_client = api_client or ColQwenAPIClient()
        
        # Check API health on initialization
        if not self.api_client.health_check():
            raise Exception("ColQwen API is not available. Please ensure the API server is running.")
        
        # Initialize MinIO service for image storage
        try:
            self.minio_service = MinioService()
            if not self.minio_service.health_check():
                raise Exception("MinIO service health check failed")
        except Exception as e:
            raise Exception(f"Failed to initialize MinIO service: {e}")
        
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()
    
    def _create_collection_if_not_exists(self):
        """Create Qdrant collection for document storage"""
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
        except Exception as e:
            print(f"Collection already exists: {e}")
            pass
    
    def _get_patches(self, image_size):
        """Get number of patches for image using API"""
        width, height = image_size
        return self.api_client.get_patches(width, height)
    
    def _embed_and_mean_pool_batch(self, image_batch):
        """Embed images and create mean pooled representations using API"""
        # Get embeddings from API - this replaces the local model inference
        image_embeddings_batch = self.api_client.embed_images(image_batch)

        # Mean pooling - identical logic to original, just using API embeddings
        pooled_by_rows_batch = []
        pooled_by_columns_batch = []

        # The API should provide embeddings in the same format as the original model
        # Process each image's embeddings exactly like the original
        for image_embedding, image in zip(image_embeddings_batch, image_batch):
            x_patches, y_patches = self._get_patches(image.size)
            
            # Convert API embedding to numpy array (replaces original tensor operations)
            image_embedding_np = np.array(image_embedding)
            
            # Find image token boundaries - API should maintain same token structure
            # In the original: image_tokens_mask = (tokenized_image == self.processor.image_token_id)
            # The API embeddings should be structured so we can identify image patch tokens
            total_tokens = len(image_embedding_np)
            num_image_patches = x_patches * y_patches
            
            # Extract image patch tokens (middle section of embeddings)
            first_image_token_idx = (total_tokens - num_image_patches) // 2
            last_image_token_idx = first_image_token_idx + num_image_patches - 1
            
            # Extract sections: prefix tokens, image patch tokens, postfix tokens
            prefix_tokens = image_embedding_np[:first_image_token_idx]
            image_patch_tokens = image_embedding_np[first_image_token_idx:last_image_token_idx + 1]
            postfix_tokens = image_embedding_np[last_image_token_idx + 1:]
            
            # Reshape image tokens to patch grid and perform mean pooling
            image_tokens = np.array(image_patch_tokens).reshape(x_patches, y_patches, -1)
            pooled_by_rows = np.mean(image_tokens, axis=0)
            pooled_by_columns = np.mean(image_tokens, axis=1)

            # Adding back prefix and postfix special tokens
            pooled_by_rows = np.concatenate([prefix_tokens, pooled_by_rows.reshape(-1, pooled_by_rows.shape[-1]), postfix_tokens], axis=0).tolist()
            pooled_by_columns = np.concatenate([prefix_tokens, pooled_by_columns.reshape(-1, pooled_by_columns.shape[-1]), postfix_tokens], axis=0).tolist()

            pooled_by_rows_batch.append(pooled_by_rows)
            pooled_by_columns_batch.append(pooled_by_columns)

        return image_embeddings_batch, pooled_by_rows_batch, pooled_by_columns_batch
    
    def index_documents(self, images):
        """Index documents in Qdrant"""
        batch_size = int(BATCH_SIZE)
        
        with tqdm(total=len(images), desc="Uploading progress") as pbar:
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                current_batch_size = len(batch)
                
                try:
                    original_batch, pooled_by_rows_batch, pooled_by_columns_batch = self._embed_and_mean_pool_batch(batch)
                except Exception as e:
                    raise Exception(f"Error during embed: {e}")
                
                # Store images in MinIO (if available) and upload each document individually
                image_urls = []
                if self.minio_service:
                    try:
                        image_urls = self.minio_service.store_images_batch(batch)
                    except Exception as e:
                        raise Exception(f"Error storing images in MinIO for batch starting at {i}: {e}")
                else:
                    raise Exception("MinIO service not available")
                
                for j, (orig, rows, cols, image_url) in enumerate(zip(original_batch, pooled_by_rows_batch, pooled_by_columns_batch, image_urls)):
                    try:
                        # Create document ID
                        doc_id = str(uuid.uuid4())
                        
                        # Prepare payload with MinIO URL
                        payload = {
                            "index": i + j,
                            "page": f"Page {i + j}",
                            "image_url": image_url,  # Store MinIO URL in metadata
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
                    except Exception as e:
                        raise Exception(f"Error during upsert for image {i + j}: {e}")
                    
                pbar.update(current_batch_size)
        
        return f"Uploaded and converted {len(images)} pages"
    def _batch_embed_query(self, query_batch):
        """Embed query batch using API"""
        # Use API to embed queries
        query_embeddings = self.api_client.embed_queries(query_batch)
        # Convert to numpy format expected by the rest of the code
        return np.array(query_embeddings[0]) if query_embeddings else np.array([])
    
    def _reranking_search_batch(self, query_embeddings_batch, search_limit=QDRANT_SEARCH_LIMIT, prefetch_limit=QDRANT_PREFETCH_LIMIT):
        """Perform two-stage retrieval with multivectors"""
        search_queries = [
            models.QueryRequest(
                query=query_embedding.tolist(),
                prefetch=[
                    models.Prefetch(
                        query=query_embedding.tolist(),
                        limit=prefetch_limit,
                        using="mean_pooling_columns"
                    ),
                    models.Prefetch(
                        query=query_embedding.tolist(),
                        limit=prefetch_limit,
                        using="mean_pooling_rows"
                    ),
                ],
                limit=search_limit,
                with_payload=True,
                with_vector=False,
                using="original"
            ) for query_embedding in query_embeddings_batch
        ]
        return self.client.query_batch_points(
            collection_name=self.collection_name,
            requests=search_queries
        )
    
    def search(self, query, images=None, k=5):
        """Search for relevant documents using Qdrant and retrieve images from MinIO"""
        query_embedding = self._batch_embed_query([query])
        search_results = self._reranking_search_batch([query_embedding])
        
        # Extract relevant results
        results = []
        if search_results and search_results[0].points:
            for i, point in enumerate(search_results[0].points[:k]):
                try:
                    # Get image URL from metadata
                    image_url = point.payload.get('image_url')
                    page_info = point.payload.get('page', f"Page {point.payload.get('index', i)}")
                    
                    if image_url and self.minio_service:
                        # Retrieve image from MinIO
                        image = self.minio_service.get_image(image_url)
                        results.append((image, page_info))
                    else:
                        raise Exception(f"Cannot retrieve image for point {i}. Image URL: {image_url}, MinIO available: {self.minio_service is not None}")
                        
                except Exception as e:
                    raise Exception(f"Error retrieving image from MinIO for point {i}: {e}")
        
        return results