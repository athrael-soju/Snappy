import io
import logging
from typing import Any, List, Optional, Union

import numpy as np
import requests
from config import COLPALI_API_TIMEOUT, COLPALI_URL
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.timing import log_execution_time


class ColPaliClient:
    """Client for ColPali Embedding API"""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        default_base = COLPALI_URL or "http://localhost:7000"
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

    def cancel_job(self, job_id: str) -> bool:
        """Request cancellation of a job.

        Sends a cancellation request to the ColPali service for the given job_id.
        This is a best-effort operation - the service may or may not support it.

        Args:
            job_id: The job ID to cancel

        Returns:
            True if cancellation request was accepted, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/cancel",
                json={"job_id": job_id},
                timeout=5,  # Short timeout for cancellation
            )
            if response.status_code == 200:
                self._logger.info(f"ColPali job {job_id} cancellation requested")
                return True
            elif response.status_code == 404:
                self._logger.debug(f"ColPali service does not support cancellation API")
                return False
            else:
                self._logger.warning(
                    f"ColPali cancellation request failed: {response.status_code}"
                )
                return False
        except Exception as e:
            self._logger.debug(f"ColPali cancellation request failed: {e}")
            return False

    def restart(self) -> bool:
        """Request service restart to stop any ongoing processing.

        Sends a restart request to the ColPali service to forcefully stop
        any ongoing batch processing and reset the service state. The service
        will exit and automatically restart if configured with a restart policy.

        Returns:
            True if restart request was accepted, False otherwise
        """
        try:
            # Create a new session WITHOUT retry logic for restart
            # We expect connection errors/timeouts when service restarts
            import requests

            restart_session = requests.Session()

            response = restart_session.post(
                f"{self.base_url}/restart",
                timeout=2,  # Very short timeout - service will exit immediately
            )
            restart_session.close()

            if response.status_code == 200:
                self._logger.info("ColPali service restart requested")
                return True
            else:
                self._logger.warning(
                    f"ColPali restart request failed: {response.status_code}"
                )
                return False
        except Exception as e:
            # Connection errors are EXPECTED during restart - treat as success
            error_msg = str(e).lower()
            if any(
                keyword in error_msg for keyword in ["connection", "timeout", "read"]
            ):
                self._logger.info(
                    "ColPali service restart initiated (connection closed)"
                )
                return True
            self._logger.warning(f"ColPali restart request failed: {e}")
            return False

    def _validate_patch_results(
        self, results: list, expected_count: int
    ) -> List[dict[str, Union[int, str]]]:
        """Validate patch results from ColPali API.

        Args:
            results: Raw results from API
            expected_count: Expected number of results

        Returns:
            Validated results

        Raises:
            ValueError: If results are malformed
        """
        if not isinstance(results, list):
            raise ValueError(f"Expected list, got {type(results)}")

        if len(results) != expected_count:
            raise ValueError(f"Expected {expected_count} results, got {len(results)}")

        for i, result in enumerate(results):
            if not isinstance(result, dict):
                raise ValueError(f"Result {i} is not a dict: {type(result)}")

            if "error" in result:
                raise ValueError(f"Result {i} contains error: {result['error']}")

            for key in ["n_patches_x", "n_patches_y"]:
                if key not in result:
                    raise ValueError(f"Result {i} missing required key: {key}")
                if not isinstance(result[key], int):
                    raise ValueError(
                        f"Result {i} key {key} is not int: {type(result[key])}"
                    )

        return results

    def _validate_embeddings(
        self, embeddings: list, expected_count: int, context: str = "embeddings"
    ) -> List[List[List[float]]]:
        """Validate embeddings from ColPali API.

        Args:
            embeddings: Raw embeddings from API
            expected_count: Expected number of embeddings
            context: Context for error messages

        Returns:
            Validated embeddings

        Raises:
            ValueError: If embeddings are malformed
        """
        if not isinstance(embeddings, list):
            raise ValueError(f"{context}: Expected list, got {type(embeddings)}")

        if len(embeddings) != expected_count:
            raise ValueError(
                f"{context}: Expected {expected_count} embeddings, got {len(embeddings)}"
            )

        for i, embedding in enumerate(embeddings):
            if not isinstance(embedding, list):
                raise ValueError(
                    f"{context}: Embedding {i} is not a list: {type(embedding)}"
                )

            if not embedding:
                raise ValueError(f"{context}: Embedding {i} is empty")

            # Validate each vector in the embedding
            for j, vector in enumerate(embedding):
                if not isinstance(vector, list):
                    raise ValueError(
                        f"{context}: Embedding {i} vector {j} is not a list"
                    )
                # Validate each element is numeric
                if not all(isinstance(v, (int, float)) for v in vector):
                    raise ValueError(
                        f"{context}: Embedding {i} vector {j} contains non-numeric values"
                    )

        return embeddings

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

            # Validate response structure
            return self._validate_patch_results(result["results"], len(dimensions))
        except Exception as e:
            raise Exception(f"Failed to get patches: {e}")

    @log_execution_time("embed queries", log_level=logging.INFO, warn_threshold_ms=1000)
    def embed_queries(self, queries: Union[str, List[str]]) -> List[List[List[float]]]:
        """
        Generate embeddings for text queries

        Args:
            queries: Single query string or list of query strings

        Returns:
            List of embeddings (each embedding is a list of vectors)
        """
        try:
            query_count = 1 if isinstance(queries, str) else len(queries)
            self._logger.debug(f"Embedding {query_count} queries via ColPali API")

            payload = {"queries": queries}
            response = self.session.post(
                f"{self.base_url}/embed/queries", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if "embeddings" not in result:
                raise KeyError(
                    "Missing 'embeddings' in ColPali /embed/queries response"
                )

            # Validate embeddings structure
            return self._validate_embeddings(
                result["embeddings"], query_count, "query embeddings"
            )
        except Exception as e:
            self._logger.error(f"Failed to embed queries: {e}")
            raise

    def _encode_image_to_bytes(self, image: Image.Image, idx: int) -> tuple:
        """Encode a single image to bytes (for parallel execution)

        Returns a tuple with bytes data instead of open buffer to prevent resource leaks.
        """
        img_byte_arr = io.BytesIO()
        try:
            image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            # Read into bytes to avoid passing open buffer
            data = img_byte_arr.getvalue()
            return ("files", (f"image_{idx}.png", io.BytesIO(data), "image/png"))
        finally:
            img_byte_arr.close()

    @log_execution_time("embed images", log_level=logging.DEBUG, warn_threshold_ms=5000)
    def embed_images(self, images: List[Image.Image]) -> List[dict[str, Any]]:
        """
        Generate embeddings for images with proper resource cleanup

        Args:
            images: List of PIL Image objects

        Returns:
            List of ImageEmbeddingItem dicts containing:
            - embedding: List[List[float]] - The actual embedding vectors
            - image_patch_start: int - Index where image tokens begin
            - image_patch_len: int - Number of image tokens
            - image_patch_indices: List[int] - Explicit positions of image tokens
        """
        files = []
        buffers = []  # Track all BytesIO objects for cleanup
        try:
            self._logger.debug(f"Embedding {len(images)} images via ColPali API")

            # Parallelize image encoding to maximize CPU utilization
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=min(8, len(images))) as executor:
                files = list(
                    executor.map(
                        lambda args: self._encode_image_to_bytes(args[1], args[0]),
                        enumerate(images),
                    )
                )

            # Extract all BytesIO buffers for explicit tracking
            buffers = [buf for _, (_, buf, _) in files]

            response = self.session.post(
                f"{self.base_url}/embed/images", files=files, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            # Log response structure for debugging
            if "embeddings" not in result:
                self._logger.error(
                    f"ColPali API response missing 'embeddings' key. Response keys: {list(result.keys())}"
                )
                raise KeyError("Missing 'embeddings' in ColPali /embed/images response")

            embeddings = result["embeddings"]

            # Check if embeddings is a list
            if not isinstance(embeddings, list):
                self._logger.error(
                    f"ColPali API returned unexpected type: {type(embeddings)}. Expected list, got: {result}"
                )
                if isinstance(embeddings, dict) and "error" in embeddings:
                    raise ValueError(f"ColPali API error: {embeddings['error']}")
                raise ValueError(
                    f"ColPali API returned unexpected type for embeddings: {type(embeddings)}"
                )

            # Return embeddings as-is (new format: [{"embedding": [[...]], "image_patch_start": 0, ...}])
            # The embedding processor will handle extraction
            return embeddings
        except Exception as e:
            self._logger.error(f"Failed to embed images: {e}")
            raise
        finally:
            # Explicitly close all file buffers to prevent resource leaks
            for buf in buffers:
                try:
                    buf.close()
                except Exception as cleanup_err:
                    self._logger.warning(
                        f"Failed to close buffer during cleanup: {cleanup_err}"
                    )

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

    @log_execution_time("generate heatmaps", log_level=logging.INFO, warn_threshold_ms=5000)
    def generate_heatmaps(
        self, query: str, images: List[Image.Image]
    ) -> List[dict[str, Any]]:
        """
        Generate attention heatmaps for images given a query.

        Args:
            query: The search query string
            images: List of PIL Image objects

        Returns:
            List of heatmap results, each containing:
            - heatmap: Base64 encoded PNG image with heatmap overlay
            - width: Image width
            - height: Image height
        """
        files = []
        buffers = []
        try:
            self._logger.debug(
                f"Generating heatmaps for {len(images)} images via ColPali API"
            )

            # Parallelize image encoding
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=min(8, len(images))) as executor:
                files = list(
                    executor.map(
                        lambda args: self._encode_image_to_bytes(args[1], args[0]),
                        enumerate(images),
                    )
                )

            # Extract all BytesIO buffers for explicit tracking
            buffers = [buf for _, (_, buf, _) in files]

            # Send request with query as form data and images as files
            response = self.session.post(
                f"{self.base_url}/heatmap",
                data={"query": query},
                files=files,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            if "results" not in result:
                self._logger.error(
                    f"ColPali API response missing 'results' key. Response keys: {list(result.keys())}"
                )
                raise KeyError("Missing 'results' in ColPali /heatmap response")

            return result["results"]
        except Exception as e:
            self._logger.error(f"Failed to generate heatmaps: {e}")
            raise
        finally:
            # Explicitly close all file buffers to prevent resource leaks
            for buf in buffers:
                try:
                    buf.close()
                except Exception as cleanup_err:
                    self._logger.warning(
                        f"Failed to close buffer during cleanup: {cleanup_err}"
                    )
