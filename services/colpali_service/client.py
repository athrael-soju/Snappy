import requests
import base64
import io
import logging
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ColPaliClient:
    """
    Client for communicating with the ColPali service.
    Provides a clean interface for the main app to interact with the ColPali service.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize ColPali client.
        
        Args:
            base_url: Base URL of the ColPali service
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
    def _encode_image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def _images_to_base64_list(self, images: List[Image.Image]) -> List[str]:
        """Convert list of PIL images to base64 strings"""
        return [self._encode_image_to_base64(img) for img in images]
    
    def health_check(self) -> dict:
        """Check if the ColPali service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise RuntimeError(f"ColPali service health check failed: {e}")

    def encode_images_with_pooling(self, images: List[Image.Image], batch_size: int = 4) -> Tuple[List, List, List]:
        """
        Encode images with mean pooling using the ColPali service - maintains original functionality.
        
        Args:
            images: List of PIL Images
            batch_size: Batch size for processing
            
        Returns:
            Tuple of (original_embeddings, pooled_by_rows, pooled_by_columns)
        """
        if not images:
            raise ValueError("No images provided")
        
        try:
            # Convert images to base64
            images_b64 = self._images_to_base64_list(images)
            
            # Make request to service
            payload = {
                "images": images_b64,
                "batch_size": batch_size
            }
            
            response = self.session.post(
                f"{self.base_url}/encode/images_with_pooling",
                json=payload,
                timeout=300  # 5 minutes timeout for large batches
            )
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Successfully encoded {len(images)} images with mean pooling")
            return result["original"], result["mean_pooling_rows"], result["mean_pooling_columns"]
            
        except Exception as e:
            logger.error(f"Error encoding images with pooling: {e}")
            raise RuntimeError(f"Failed to encode images with pooling via ColPali service: {e}")
    
    def encode_query(self, query: str, max_length: int = 50) -> Tuple[List, List]:
        """
        Encode query using the ColPali service.
        
        Args:
            query: Text query to encode
            max_length: Maximum sequence length
            
        Returns:
            Tuple of (embedding_list, shape) - raw data without tensor conversion
        """
        if not query or not query.strip():
            raise ValueError("Empty query provided")
        
        try:
            payload = {
                "query": query,
                "max_length": max_length
            }
            
            response = self.session.post(
                f"{self.base_url}/encode/query",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Successfully encoded query")
            return result["embedding"], result["shape"]
            
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            raise RuntimeError(f"Failed to encode query via ColPali service: {e}")
    
    def wait_for_service(self, max_attempts: int = 30, delay: float = 2.0) -> bool:
        """
        Wait for the ColPali service to become available.
        
        Args:
            max_attempts: Maximum number of health check attempts
            delay: Delay between attempts in seconds
            
        Returns:
            True if service becomes available, False otherwise
        """
        import time
        
        for attempt in range(max_attempts):
            try:
                self.health_check()
                logger.info("ColPali service is ready")
                return True
            except Exception:
                if attempt < max_attempts - 1:
                    logger.info(f"Waiting for ColPali service... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(delay)
                else:
                    logger.error("ColPali service failed to become available")
        
        return False
