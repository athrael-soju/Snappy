import requests
import io
from typing import List, Union
from PIL import Image
import numpy as np

from config import COLQWEN_API_BASE_URL, COLQWEN_API_TIMEOUT


class ColQwenAPIClient:
    """Client for ColQwen2.5 Embedding API"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or COLQWEN_API_BASE_URL
        self.timeout = timeout or COLQWEN_API_TIMEOUT
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip('/')
        
    def health_check(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def get_info(self) -> dict:
        """Get API version information"""
        try:
            response = requests.get(f"{self.base_url}/info", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get API info: {e}")
            return {}
    
    def get_patches(self, dimensions: List[dict[str, int]]) -> List[dict[str, Union[int, str]]]:
        """Get number of patches for given image dimensions (batch request)
        
        Args:
            dimensions: List of dictionaries containing 'width' and 'height' keys
            
        Returns:
            List of dictionaries containing patch information for each dimension
        """
        try:
            payload = {"dimensions": dimensions}
            response = requests.post(
                f"{self.base_url}/patches",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["results"]
        except Exception as e:
            raise Exception(f"Failed to get patches: {e}")
    
    def embed_queries(self, queries: Union[str, List[str]]) -> List[List[List[float]]]:
        """
        Generate embeddings for text queries
        
        Args:
            queries: Single query string or list of query strings
            
        Returns:
            List of embeddings (each embedding is a list of vectors)
        """
        try:
            payload = {"queries": queries}
            response = requests.post(
                f"{self.base_url}/embed/queries",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["embeddings"]
        except Exception as e:
            print(f"Failed to embed queries: {e}")
            raise
    
    def embed_images(self, images: List[Image.Image]) -> List[List[List[float]]]:
        """
        Generate embeddings for images
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of embeddings (each embedding is a list of vectors)
        """
        try:
            files = []
            for i, image in enumerate(images):
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                files.append(('files', (f'image_{i}.png', img_byte_arr, 'image/png')))
            
            response = requests.post(
                f"{self.base_url}/embed/images",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["embeddings"]
        except Exception as e:
            print(f"Failed to embed images: {e}")
            raise
    
    def embed_images_batch(self, images: List[Image.Image], batch_size: int = 4) -> List[List[List[float]]]:
        """
        Generate embeddings for images in batches
        
        Args:
            images: List of PIL Image objects
            batch_size: Number of images to process per batch
            
        Returns:
            List of embeddings (each embedding is a list of vectors)
        """
        all_embeddings = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            try:
                batch_embeddings = self.embed_images(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Failed to process batch {i//batch_size + 1}: {e}")
                raise
        
        return all_embeddings
    
    def score_embeddings(self, query_embeddings: List[List[List[float]]], 
                        doc_embeddings: List[List[List[float]]]) -> np.ndarray:
        """
        Calculate similarity scores between query and document embeddings
        
        Args:
            query_embeddings: Query embeddings from embed_queries
            doc_embeddings: Document embeddings from embed_images
            
        Returns:
            Similarity scores matrix
        """
        # Convert to numpy arrays for computation
        query_emb = np.array(query_embeddings[0])  # Take first query
        doc_embs = [np.array(doc_emb) for doc_emb in doc_embeddings]
        
        scores = []
        for doc_emb in doc_embs:
            # Calculate cosine similarity between query and document patches
            # Use maximum similarity across patches (similar to ColPali scoring)
            similarities = []
            for q_vec in query_emb:
                for d_vec in doc_emb:
                    # Normalize vectors
                    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
                    d_norm = d_vec / (np.linalg.norm(d_vec) + 1e-8)
                    sim = np.dot(q_norm, d_norm)
                    similarities.append(sim)
            scores.append(max(similarities) if similarities else 0.0)
        
        return np.array(scores)
