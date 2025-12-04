"""
On-the-fly benchmark strategy.

Processes images directly without storage (Qdrant/DuckDB).
Tests region filtering quality by comparing retrieved regions vs ground truth bboxes.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from benchmarks.strategies.base import BaseRetrievalStrategy, RetrievalResult
from benchmarks.utils.images import decode_base64_image
from utils.ocr import extract_region_content


class OnTheFlyStrategy(BaseRetrievalStrategy):
    """
    On-the-fly benchmark strategy that processes images without storage.

    Flow:
    1. Receive image directly from benchmark runner
    2. OCR image via DeepSeek -> get regions (text + bbox)
    3. Generate interpretability maps via ColPali
    4. Filter regions by relevance score
    5. Return filtered region text for LLM

    This tests the region filtering quality independently of retrieval accuracy.
    """

    def __init__(
        self,
        colpali_url: str = "http://localhost:7000",
        deepseek_url: str = "http://localhost:8200",
        # Region relevance settings
        region_relevance_threshold: float = 0.3,
        region_top_k: int = 10,
        region_score_aggregation: str = "max",
        # OCR settings
        ocr_mode: str = "Gundam",
        ocr_task: str = "markdown",  # markdown with include_grounding returns bboxes
        ocr_max_concurrent: int = 2,  # Limit concurrent OCR requests to prevent overload
        **kwargs,
    ):
        super().__init__(
            colpali_url=colpali_url,
            **kwargs,
        )

        self.deepseek_url = deepseek_url.rstrip("/")
        self.region_relevance_threshold = region_relevance_threshold
        self.region_top_k = region_top_k
        self.region_score_aggregation = region_score_aggregation
        self.ocr_mode = ocr_mode
        self.ocr_task = ocr_task
        self.ocr_max_concurrent = ocr_max_concurrent

        self._colpali_client = None
        self._session = None
        self._ocr_semaphore: Optional[asyncio.Semaphore] = None

    @property
    def name(self) -> str:
        return "on_the_fly"

    @property
    def description(self) -> str:
        return (
            "On-the-fly processing: OCR + interpretability + region filtering. "
            "No storage required. Tests region filtering quality directly."
        )

    async def initialize(self) -> None:
        """Initialize clients."""
        from clients.colpali import ColPaliClient

        self._colpali_client = ColPaliClient(
            base_url=self.colpali_url,
            timeout=60,
        )

        self._session = requests.Session()
        self._ocr_semaphore = asyncio.Semaphore(self.ocr_max_concurrent)

        health = await self.health_check()
        if not all(health.values()):
            unhealthy = [k for k, v in health.items() if not v]
            raise RuntimeError(f"Services not healthy: {unhealthy}")

        self._initialized = True
        self._logger.info(
            f"OnTheFlyStrategy initialized (max {self.ocr_max_concurrent} concurrent OCR)"
        )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of required services."""
        health = {}

        # Check ColPali
        try:
            if self._colpali_client:
                health["colpali"] = self._colpali_client.health_check()
            else:
                health["colpali"] = False
        except Exception:
            health["colpali"] = False

        # Check DeepSeek OCR
        try:
            response = self._session.get(f"{self.deepseek_url}/health", timeout=5)
            health["deepseek"] = response.status_code == 200
        except Exception:
            health["deepseek"] = False

        return health

    async def retrieve(
        self,
        query: str,
        image: Optional[Image.Image] = None,
        **kwargs,
    ) -> RetrievalResult:
        """
        Process image on-the-fly and retrieve relevant regions.

        Args:
            query: Search query text
            image: PIL Image to process (required for on-the-fly mode)
            **kwargs: Additional parameters

        Returns:
            RetrievalResult with filtered regions
        """
        result = RetrievalResult()
        total_start = time.perf_counter()

        if image is None:
            result.error = "Image required for on-the-fly processing"
            return result

        try:
            # Step 1: OCR the image
            self._logger.debug(f"Running OCR on image ({image.width}x{image.height})")
            ocr_start = time.perf_counter()
            ocr_result = await self._run_ocr(image)
            ocr_time = time.perf_counter() - ocr_start

            if not ocr_result:
                result.error = "OCR failed - no response from DeepSeek"
                return result

            self._logger.debug(
                f"OCR completed: {len(ocr_result.get('bounding_boxes', []))} bboxes, "
                f"{len(ocr_result.get('raw', ''))} chars raw text"
            )

            # Extract regions from OCR result
            regions = self._extract_regions(ocr_result, image)

            # Extract cropped images (base64) for figure/image regions
            crops = ocr_result.get("crops", [])

            self._logger.debug(
                f"Extracted {len(regions)} regions with content, {len(crops)} crops"
            )

            if not regions:
                result.error = f"No regions extracted from OCR (bboxes={len(ocr_result.get('bounding_boxes', []))})"
                return result

            # Step 2: Generate interpretability maps
            interp_start = time.perf_counter()
            interp_result = await asyncio.to_thread(
                self._colpali_client.generate_interpretability_maps,
                query,
                image,
            )
            interp_time = time.perf_counter() - interp_start

            similarity_maps = interp_result.get("similarity_maps", [])
            n_patches_x = interp_result.get("n_patches_x", 0)
            n_patches_y = interp_result.get("n_patches_y", 0)
            image_width = interp_result.get("image_width", image.width)
            image_height = interp_result.get("image_height", image.height)

            if not similarity_maps or not n_patches_x or not n_patches_y:
                result.error = "Interpretability maps generation failed"
                return result

            # Step 3: Filter regions by relevance
            from domain.region_relevance import filter_regions_by_relevance

            filter_start = time.perf_counter()
            filtered_regions = filter_regions_by_relevance(
                regions=regions,
                similarity_maps=similarity_maps,
                n_patches_x=n_patches_x,
                n_patches_y=n_patches_y,
                image_width=image_width,
                image_height=image_height,
                threshold=self.region_relevance_threshold,
                top_k=self.region_top_k if self.region_top_k > 0 else None,
                aggregation=self.region_score_aggregation,
            )
            result.region_filtering_time_s = time.perf_counter() - filter_start

            # Build context from filtered regions only - structured format
            context_parts = []
            retrieved_images = []

            for region in filtered_regions:
                content = region.get("content", "")
                label = region.get("label", "unknown")

                if content:
                    # Include region metadata for context
                    context_parts.append(f"[{label}]: {content}")
                    result.context_regions.append(region)

                # For image/figure regions, include the cropped image
                if label.lower() in ("image", "figure") and "image_index" in region:
                    img_idx = region["image_index"]
                    if img_idx < len(crops):
                        crop_img = self._decode_crop(crops[img_idx])
                        if crop_img:
                            retrieved_images.append(crop_img)

            result.context_text = "\n".join(context_parts)
            # Only include cropped images from relevant figure/image regions
            result.retrieved_images = retrieved_images
            result.retrieved_pages = [1]  # Single page, ground truth
            result.scores = [1.0]  # Perfect retrieval (oracle mode)

            # Log filtering stats
            self._logger.debug(
                f"Region filtering: {len(regions)} total -> {len(filtered_regions)} relevant, "
                f"context={len(result.context_text)} chars, images={len(retrieved_images)}"
            )

        except Exception as e:
            result.error = str(e)
            self._logger.error(f"On-the-fly processing failed: {e}", exc_info=True)

        result.retrieval_time_s = time.perf_counter() - total_start
        return result

    async def _run_ocr(
        self,
        image: Image.Image,
        max_retries: int = 3,
        base_delay: float = 5.0,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """
        Run DeepSeek OCR on the image with retry and exponential backoff.

        Uses a semaphore to limit concurrent OCR requests and prevent service overload.

        Args:
            image: PIL Image to process
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            timeout: Request timeout in seconds

        Returns:
            OCR result dictionary or None on failure
        """
        import io

        # Convert PIL image to bytes once
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        last_error = None

        # Use semaphore to limit concurrent OCR requests (create lazily if needed)
        if self._ocr_semaphore is None:
            self._ocr_semaphore = asyncio.Semaphore(self.ocr_max_concurrent)

        async with self._ocr_semaphore:
            for attempt in range(max_retries + 1):
                try:
                    # Send to DeepSeek OCR
                    response = await asyncio.to_thread(
                        self._session.post,
                        f"{self.deepseek_url}/api/ocr",
                        files={"image": ("page.png", image_bytes, "image/png")},
                        data={
                            "mode": self.ocr_mode,
                            "task": self.ocr_task,
                            "include_grounding": "true",
                            "include_images": "true",  # Extract cropped images for figures
                        },
                        timeout=timeout,
                    )

                    if response.status_code == 200:
                        return response.json()

                    # Non-200 status - log and potentially retry
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    self._logger.warning(
                        f"OCR request failed (attempt {attempt + 1}/{max_retries + 1}): {last_error}"
                    )

                except Exception as e:
                    last_error = str(e)
                    self._logger.warning(
                        f"OCR request error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )

                # Retry with exponential backoff if not last attempt
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)  # 5s, 10s, 20s
                    self._logger.info(f"Retrying OCR in {delay:.1f}s...")
                    await asyncio.sleep(delay)

        self._logger.error(f"OCR failed after {max_retries + 1} attempts: {last_error}")
        return None

    def _extract_regions(
        self, ocr_result: Dict[str, Any], image: Image.Image
    ) -> List[Dict[str, Any]]:
        """
        Extract regions with bboxes and content from OCR result.

        Uses the same approach as Snappy's OcrProcessor._build_regions_from_bboxes:
        - bounding_boxes from response provides bbox coordinates
        - raw text is parsed to extract content for each region

        Returns list of regions with: id, label, bbox, content
        """
        regions = []
        bounding_boxes = ocr_result.get("bounding_boxes", [])

        if not bounding_boxes:
            self._logger.warning("No bounding_boxes in OCR response")
            return regions

        # Extract content mapping from raw text
        raw_text = ocr_result.get("raw", "")
        content_map = self._extract_region_content(raw_text) if raw_text else {}

        # Track image index for mapping crops to regions
        image_idx = 0

        for i, bbox in enumerate(bounding_boxes):
            label = bbox.get("label", "unknown")
            region = {
                "id": f"region-{i+1}",
                "label": label,
                "bbox": [
                    int(bbox.get("x1", 0)),
                    int(bbox.get("y1", 0)),
                    int(bbox.get("x2", 0)),
                    int(bbox.get("y2", 0)),
                ],
            }

            # Add content if available (same logic as Snappy's processor)
            if label in content_map and content_map[label]:
                content_list = content_map[label]
                if content_list:
                    region["content"] = content_list.pop(0)

            # Track image index for mapping to extracted crops
            if label.lower() in ("image", "figure"):
                region["image_index"] = image_idx
                image_idx += 1

            regions.append(region)

        return regions

    def _decode_crop(self, crop_b64: str) -> Optional[Image.Image]:
        """Decode a base64-encoded crop to PIL Image."""
        return decode_base64_image(crop_b64)

    def _extract_region_content(self, raw_text: str) -> Dict[str, List[str]]:
        """
        Extract content for each labeled region from raw OCR output.

        Delegates to the shared utility function for parsing grounding markers.

        Returns:
            Dictionary mapping labels to lists of their content
        """
        return extract_region_content(raw_text)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            self._session.close()
        await super().cleanup()
