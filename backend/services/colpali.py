import requests
import io
import logging
from typing import List, Union
from PIL import Image
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import COLPALI_MODE, COLPALI_CPU_URL, COLPALI_GPU_URL, COLPALI_API_TIMEOUT, LOG_LEVEL


class ColPaliService:
    """Client for ColPali Embedding API"""

    def __init__(self, base_url: str = None, timeout: int = None):
        default_base = COLPALI_GPU_URL if COLPALI_MODE == "gpu" else COLPALI_CPU_URL
        self.base_url = base_url or default_base
        self.timeout = timeout or COLPALI_API_TIMEOUT

        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")

        # Logger
        self._logger = logging.getLogger(__name__)

        # Session with retries/backoff
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def health_check(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            self._logger.warning(f"ColPali health check failed: {e}")
            return False

    def get_info(self) -> dict:
        """Get API version information"""
        try:
            response = self.session.get(f"{self.base_url}/info", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._logger.error(f"Failed to get API info: {e}")
            return {}

    def get_patches(
        self, dimensions: List[dict[str, int]]
    ) -> List[dict[str, Union[int, str]]]:
        """Get number of patches for given image dimensions (batch request)

        Args:
            dimensions: List of dictionaries containing 'width' and 'height' keys

        Returns:
            List of dictionaries containing patch information for each dimension
        """
        try:
            payload = {"dimensions": dimensions}
            response = self.session.post(
                f"{self.base_url}/patches", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if "results" not in result:
                raise KeyError("Missing 'results' in ColPali /patches response")
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
            response = self.session.post(
                f"{self.base_url}/embed/queries", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if "embeddings" not in result:
                raise KeyError("Missing 'embeddings' in ColPali /embed/queries response")
            return result["embeddings"]
        except Exception as e:
            self._logger.error(f"Failed to embed queries: {e}")
            raise

    def _encode_image_to_bytes(self, image: Image.Image, idx: int) -> tuple:
        """Encode a single image to bytes (for parallel execution)"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        return ("files", (f"image_{idx}.png", img_byte_arr, "image/png"))

    def embed_images(self, images: List[Image.Image]) -> List[List[List[float]]]:
        """
        Generate embeddings for images

        Args:
            images: List of PIL Image objects

        Returns:
            List of embeddings (each embedding is a list of vectors)
        """
        try:
            # Parallelize image encoding to maximize CPU utilization
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(8, len(images))) as executor:
                files = list(executor.map(
                    lambda args: self._encode_image_to_bytes(args[1], args[0]),
                    enumerate(images)
                ))

            response = self.session.post(
                f"{self.base_url}/embed/images", files=files, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if "embeddings" not in result:
                raise KeyError("Missing 'embeddings' in ColPali /embed/images response")
            return result["embeddings"]
        except Exception as e:
            self._logger.error(f"Failed to embed images: {e}")
            raise

    def embed_images_batch(
        self, images: List[Image.Image], batch_size: int = 4
    ) -> List[List[List[float]]]:
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
            batch = images[i : i + batch_size]
            try:
                batch_embeddings = self.embed_images(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                self._logger.error(
                    f"Failed to process batch {i // batch_size + 1}: {e}"
                )
                raise

        return all_embeddings

    def score_embeddings(
        self,
        query_embeddings: List[List[List[float]]],
        doc_embeddings: List[List[List[float]]],
    ) -> np.ndarray:
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
