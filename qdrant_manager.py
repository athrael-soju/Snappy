import numpy as np
import torch
import uuid
from tqdm import tqdm
from qdrant_client import QdrantClient, models
from typing import List, Tuple, Any


class QdrantManager:
    """Manager for Qdrant vector database operations with ColPali embeddings."""
    
    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "colpali_documents"):
        """Initialize Qdrant client and collection.
        
        Args:
            url: Qdrant server URL
            collection_name: Name of the collection to use
        """
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.create_collection_if_not_exists()
    
    def create_collection_if_not_exists(self):
        """Create a collection only if it doesn't already exist."""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name in collection_names:
            print(f"Collection '{self.collection_name}' already exists.")
            return False
        
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "original": models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=models.HnswConfigDiff(
                        m=0  # switching off HNSW
                    )
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
        print(f"Created collection '{self.collection_name}'")
        return True
    
    def clear_collection(self):
        """Clear all data from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.create_collection_if_not_exists()
            print(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def get_patches(self, image_size, model_processor, model):
        """Get number of patches for an image, handling different model types."""
        try:
            # Try with spatial_merge_size first (for ColQwen2_5)
            if hasattr(model, 'spatial_merge_size'):
                return model_processor.get_n_patches(image_size, spatial_merge_size=model.spatial_merge_size)
            else:
                # For ColIdefics3 and other models without spatial_merge_size
                try:
                    return model_processor.get_n_patches(image_size)
                except TypeError:
                    # Try with default spatial_merge_size
                    try:
                        return model_processor.get_n_patches(image_size, spatial_merge_size=1)
                    except TypeError:
                        # Last resort - call without any additional parameters
                        return model_processor.get_n_patches(image_size)
        except Exception as e:
            print(f"Error getting patches: {e}")
            # Fallback to reasonable defaults
            return 16, 16
    
    def embed_and_mean_pool_batch(self, image_batch, model_processor, model):
        """Embed images and compute mean pooling for rows and columns."""
        # Embed
        with torch.no_grad():
            processed_images = model_processor.process_images(image_batch).to(model.device)
            image_embeddings = model(**processed_images)

        image_embeddings_batch = image_embeddings.cpu().float().numpy().tolist()

        # Mean pooling
        pooled_by_rows_batch = []
        pooled_by_columns_batch = []

        for image_embedding, tokenized_image, image in zip(image_embeddings,
                                                           processed_images.input_ids,
                                                           image_batch):
            x_patches, y_patches = self.get_patches(image.size, model_processor, model)

            image_tokens_mask = (tokenized_image == model_processor.image_token_id)
            image_tokens = image_embedding[image_tokens_mask].view(x_patches, y_patches, model.dim)

            # Mean pooling by rows and columns
            pooled_by_rows = torch.mean(image_tokens, dim=1)  # Shape: (x_patches, dim)
            pooled_by_columns = torch.mean(image_tokens, dim=0)  # Shape: (y_patches, dim)

            pooled_by_rows_batch.append(pooled_by_rows.cpu().float().numpy().tolist())
            pooled_by_columns_batch.append(pooled_by_columns.cpu().float().numpy().tolist())

        return image_embeddings_batch, pooled_by_rows_batch, pooled_by_columns_batch
    
    def upload_batch(self, original_batch, pooled_by_rows_batch, pooled_by_columns_batch, payload_batch):
        """Upload a batch of embeddings to Qdrant."""
        try:
            # Convert to numpy arrays with explicit float32 dtype
            vectors = {
                "mean_pooling_columns": np.asarray(pooled_by_columns_batch, dtype=np.float32),
                "original": np.asarray(original_batch, dtype=np.float32),
                "mean_pooling_rows": np.asarray(pooled_by_rows_batch, dtype=np.float32)
            }
            
            self.client.upload_collection(
                collection_name=self.collection_name,
                vectors=vectors,
                payload=payload_batch,
                ids=[str(uuid.uuid4()) for _ in range(len(original_batch))]
            )
            return True
        except Exception as e:
            print(f"Error during upsert: {e}")
            return False
    
    def index_images(self, images, model_processor, model, batch_size=4):
        """Index a list of images into Qdrant."""
        print(f"Indexing {len(images)} images into Qdrant...")
        
        # Clear existing data
        self.clear_collection()
        
        # Process images in batches
        for i in tqdm(range(0, len(images), batch_size), desc="Indexing images"):
            batch = images[i:i + batch_size]
            
            # Get embeddings with mean pooling
            original_batch, pooled_rows_batch, pooled_columns_batch = self.embed_and_mean_pool_batch(
                batch, model_processor, model
            )
            
            # Create payload for each image
            payload_batch = []
            for j, image in enumerate(batch):
                payload_batch.append({
                    "page_index": i + j,
                    "image_size": image.size
                })
            
            # Upload to Qdrant
            success = self.upload_batch(
                original_batch, pooled_rows_batch, pooled_columns_batch, payload_batch
            )
            
            if not success:
                print(f"Failed to upload batch {i//batch_size + 1}")
                return False
        
        print(f"Successfully indexed {len(images)} images")
        return True
    
    def batch_embed_query(self, query_batch, model_processor, model):
        """Embed a batch of queries."""
        with torch.no_grad():
            batch_query = model_processor.process_queries(query_batch).to(model.device)
            embeddings_query = model(**batch_query)
        return embeddings_query.cpu().float().numpy().tolist()
    
    def reranking_search_batch(self, query_batch, search_limit=20, prefetch_limit=200):
        """Perform reranking search using prefetch strategy."""
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
    
    def search_with_reranking(self, query: str, model_processor, model, k: int = 5):
        """Convenience method to search with a single query and return top-k results."""
        # Embed the query
        query_embeddings = self.batch_embed_query([query], model_processor, model)
        
        # Perform reranking search
        search_results = self.reranking_search_batch(query_embeddings, search_limit=k)
        
        # Extract results
        results = []
        if search_results and len(search_results) > 0:
            for point in search_results[0].points:
                results.append({
                    'page_index': point.payload['page_index'],
                    'score': point.score,
                    'image_size': point.payload['image_size']
                })
        
        return results
    
    def get_collection_info(self):
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': info.config.params.vectors,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None
