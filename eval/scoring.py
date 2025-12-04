"""
Standalone region scoring wrapper for evaluation.

This module provides a clean interface to the patch-to-region relevance
scoring algorithm, decoupled from Qdrant and other infrastructure.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

# Add backend to path for importing region_relevance
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from domain.region_relevance import (
    compute_region_relevance_scores,
    filter_regions_by_relevance,
)

from eval.dataset import BoundingBox, OCRRegion, Sample

logger = logging.getLogger(__name__)


class RegionScorer:
    """
    Standalone region scorer using patch-to-region relevance propagation.

    This class wraps the core scoring algorithm for use in evaluation,
    without requiring Qdrant or other infrastructure.
    """

    def __init__(
        self,
        colpali_url: str = "http://localhost:8001",
        default_n_patches_x: int = 128,
        default_n_patches_y: int = 96,
        timeout: float = 30.0,
    ):
        """
        Initialize the region scorer.

        Args:
            colpali_url: URL of the ColPali service
            default_n_patches_x: Default patch grid width
            default_n_patches_y: Default patch grid height
            timeout: Request timeout in seconds
        """
        self.colpali_url = colpali_url.rstrip("/")
        self.default_n_patches_x = default_n_patches_x
        self.default_n_patches_y = default_n_patches_y
        self.timeout = timeout

        self._session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp

            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_interpretability_maps(
        self,
        query: str,
        image: Union[Image.Image, Path, str],
    ) -> Dict[str, Any]:
        """
        Get interpretability maps from ColPali service.

        Args:
            query: Query string
            image: PIL Image or path to image file

        Returns:
            Interpretability response with similarity_maps, n_patches_x, etc.
        """
        import aiohttp
        import base64
        from io import BytesIO

        # Load image if path
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        # Convert to base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        session = await self._get_session()

        async with session.post(
            f"{self.colpali_url}/interpret",
            json={"query": query, "image": image_b64},
        ) as response:
            response.raise_for_status()
            return await response.json()

    def score_regions(
        self,
        regions: List[Union[OCRRegion, Dict[str, Any]]],
        similarity_maps: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
        n_patches_x: Optional[int] = None,
        n_patches_y: Optional[int] = None,
        aggregation: str = "max",
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score regions using patch-to-region relevance propagation.

        Args:
            regions: List of OCR regions with bounding boxes
            similarity_maps: Per-token similarity maps from interpretability
            image_width: Original image width in pixels
            image_height: Original image height in pixels
            n_patches_x: Patch grid width (default: self.default_n_patches_x)
            n_patches_y: Patch grid height (default: self.default_n_patches_y)
            aggregation: Score aggregation method ('max', 'mean', 'sum')

        Returns:
            List of (region, score) tuples sorted by score descending
        """
        # Convert OCRRegion to dict if needed
        region_dicts = []
        for region in regions:
            if isinstance(region, OCRRegion):
                region_dicts.append(region.to_dict())
            else:
                region_dicts.append(region)

        return compute_region_relevance_scores(
            regions=region_dicts,
            similarity_maps=similarity_maps,
            n_patches_x=n_patches_x or self.default_n_patches_x,
            n_patches_y=n_patches_y or self.default_n_patches_y,
            image_width=image_width,
            image_height=image_height,
            aggregation=aggregation,
        )

    def filter_regions(
        self,
        regions: List[Union[OCRRegion, Dict[str, Any]]],
        similarity_maps: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
        n_patches_x: Optional[int] = None,
        n_patches_y: Optional[int] = None,
        threshold: float = 0.0,
        top_k: Optional[int] = None,
        aggregation: str = "max",
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank regions by relevance.

        Args:
            regions: List of OCR regions with bounding boxes
            similarity_maps: Per-token similarity maps from interpretability
            image_width: Original image width in pixels
            image_height: Original image height in pixels
            n_patches_x: Patch grid width
            n_patches_y: Patch grid height
            threshold: Minimum relevance score (0.0-1.0)
            top_k: Maximum number of regions to return
            aggregation: Score aggregation method

        Returns:
            Filtered list of regions with relevance_score added
        """
        # Convert OCRRegion to dict if needed
        region_dicts = []
        for region in regions:
            if isinstance(region, OCRRegion):
                region_dicts.append(region.to_dict())
            else:
                region_dicts.append(region)

        return filter_regions_by_relevance(
            regions=region_dicts,
            similarity_maps=similarity_maps,
            n_patches_x=n_patches_x or self.default_n_patches_x,
            n_patches_y=n_patches_y or self.default_n_patches_y,
            image_width=image_width,
            image_height=image_height,
            threshold=threshold,
            top_k=top_k,
            aggregation=aggregation,
        )

    async def score_sample(
        self,
        sample: Sample,
        threshold: float = 0.0,
        top_k: Optional[int] = None,
        aggregation: str = "max",
    ) -> List[Dict[str, Any]]:
        """
        Score and filter regions for a complete sample.

        This is a convenience method that handles the full pipeline:
        1. Get interpretability maps from ColPali
        2. Score regions
        3. Filter by threshold/top_k

        Args:
            sample: Evaluation sample with image and OCR regions
            threshold: Minimum relevance score
            top_k: Maximum number of regions
            aggregation: Score aggregation method

        Returns:
            Filtered and scored regions
        """
        if not sample.ocr_regions:
            logger.warning(f"Sample {sample.sample_id} has no OCR regions")
            return []

        # Get image dimensions
        image_width, image_height = sample.image_dimensions

        # Get interpretability maps
        interp_response = await self.get_interpretability_maps(
            query=sample.question,
            image=sample.image_path,
        )

        similarity_maps = interp_response.get("similarity_maps", [])
        n_patches_x = interp_response.get("n_patches_x", self.default_n_patches_x)
        n_patches_y = interp_response.get("n_patches_y", self.default_n_patches_y)

        if not similarity_maps:
            logger.warning(f"No similarity maps returned for sample {sample.sample_id}")
            return []

        # Filter regions
        return self.filter_regions(
            regions=sample.ocr_regions,
            similarity_maps=similarity_maps,
            image_width=image_width,
            image_height=image_height,
            n_patches_x=n_patches_x,
            n_patches_y=n_patches_y,
            threshold=threshold,
            top_k=top_k,
            aggregation=aggregation,
        )


class MockRegionScorer:
    """
    Mock scorer for testing without ColPali service.

    Generates synthetic similarity maps based on text overlap with query.
    """

    def __init__(
        self,
        n_patches_x: int = 128,
        n_patches_y: int = 96,
    ):
        self.n_patches_x = n_patches_x
        self.n_patches_y = n_patches_y

    def _generate_mock_similarity_map(
        self,
        query: str,
        regions: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
    ) -> List[Dict[str, Any]]:
        """Generate mock similarity maps based on text overlap."""
        # Tokenize query (simple whitespace split)
        query_tokens = query.lower().split()

        similarity_maps = []
        for token in query_tokens:
            # Create empty similarity map
            sim_map = np.zeros((self.n_patches_y, self.n_patches_x))

            # For each region, if it contains the token, boost that area
            patch_width = image_width / self.n_patches_x
            patch_height = image_height / self.n_patches_y

            for region in regions:
                content = region.get("content", "").lower()
                if token in content:
                    bbox = region.get("bbox", [0, 0, 0, 0])
                    # Convert to patch indices
                    px1 = int(bbox[0] / patch_width)
                    py1 = int(bbox[1] / patch_height)
                    px2 = int(np.ceil(bbox[2] / patch_width))
                    py2 = int(np.ceil(bbox[3] / patch_height))

                    # Clamp
                    px1 = max(0, min(px1, self.n_patches_x - 1))
                    py1 = max(0, min(py1, self.n_patches_y - 1))
                    px2 = max(px1 + 1, min(px2, self.n_patches_x))
                    py2 = max(py1 + 1, min(py2, self.n_patches_y))

                    # Set high similarity for matching regions
                    sim_map[py1:py2, px1:px2] = 0.8 + 0.2 * np.random.random()

            similarity_maps.append({
                "token": token,
                "similarity_map": sim_map.tolist(),
            })

        return similarity_maps

    def score_regions(
        self,
        regions: List[Union[OCRRegion, Dict[str, Any]]],
        query: str,
        image_width: int,
        image_height: int,
        aggregation: str = "max",
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Score regions using mock similarity maps."""
        # Convert to dicts
        region_dicts = []
        for region in regions:
            if isinstance(region, OCRRegion):
                region_dicts.append(region.to_dict())
            else:
                region_dicts.append(region)

        # Generate mock maps
        similarity_maps = self._generate_mock_similarity_map(
            query, region_dicts, image_width, image_height
        )

        return compute_region_relevance_scores(
            regions=region_dicts,
            similarity_maps=similarity_maps,
            n_patches_x=self.n_patches_x,
            n_patches_y=self.n_patches_y,
            image_width=image_width,
            image_height=image_height,
            aggregation=aggregation,
        )

    def filter_regions(
        self,
        regions: List[Union[OCRRegion, Dict[str, Any]]],
        query: str,
        image_width: int,
        image_height: int,
        threshold: float = 0.0,
        top_k: Optional[int] = None,
        aggregation: str = "max",
    ) -> List[Dict[str, Any]]:
        """Filter regions using mock scoring."""
        # Convert to dicts
        region_dicts = []
        for region in regions:
            if isinstance(region, OCRRegion):
                region_dicts.append(region.to_dict())
            else:
                region_dicts.append(region)

        # Generate mock maps
        similarity_maps = self._generate_mock_similarity_map(
            query, region_dicts, image_width, image_height
        )

        return filter_regions_by_relevance(
            regions=region_dicts,
            similarity_maps=similarity_maps,
            n_patches_x=self.n_patches_x,
            n_patches_y=self.n_patches_y,
            image_width=image_width,
            image_height=image_height,
            threshold=threshold,
            top_k=top_k,
            aggregation=aggregation,
        )
