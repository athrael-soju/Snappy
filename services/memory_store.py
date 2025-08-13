from tqdm import tqdm
from typing import List
from PIL import Image
import numpy as np

from config import BATCH_SIZE
from .colqwen_api_client import ColQwenAPIClient

class MemoryStoreService:
    def __init__(self, api_client: ColQwenAPIClient = None):
        self.api_client = api_client or ColQwenAPIClient()
        
        # Check API health on initialization
        if not self.api_client.health_check():
            raise Exception("ColQwen API is not available. Please ensure the API server is running.")
    
    def index_gpu(self, images: List[Image.Image], ds: List):
        """Index documents using API-based approach"""
        try:
            # Process images in batches using the API
            embeddings = self.api_client.embed_images_batch(images, batch_size=int(BATCH_SIZE))
            ds.extend(embeddings)
            return f"Uploaded and converted {len(images)} pages"
        except Exception as e:
            raise Exception(f"Failed to index documents: {e}")

    def search(self, query: str, ds: List, images: List[Image.Image], k: int):
        """Search using API-based approach"""
        try:
            k = min(k, len(ds))
            
            # Generate query embeddings using API
            query_embeddings = self.api_client.embed_queries([query])
            
            # Calculate similarity scores
            scores = self.api_client.score_embeddings(query_embeddings, ds)
            
            # Get top-k indices
            top_k_indices = np.argsort(scores)[-k:][::-1]  # Sort descending and take top k
            
            results = []
            for idx in top_k_indices:
                results.append((images[idx], f"Page {idx}"))
            
            return results
        except Exception as e:
            raise Exception(f"Failed to search documents: {e}")
