"""
Snappy Spatial Grounding strategy.

This strategy implements the Patch-to-Region Relevance Propagation
approach from the research paper.

Steps:
1. Run OCR to extract regions with bounding boxes
2. Generate ColPali embeddings (query + image)
3. Compute interpretability maps (per-token similarity heatmaps)
4. Filter regions by relevance score (IoU-weighted aggregation)
5. Send filtered regions to LLM for answer generation

This approach provides:
- Sub-page localization of relevant content
- Reduced token usage (only relevant regions)
- Spatial grounding of answers
"""

import io
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from PIL import Image

from ..config import BenchmarkConfig
from ..dataset import BenchmarkSample
from ..metrics import Timer, TimingMetrics, TokenMetrics
from .base import BaseStrategy, StrategyResult

logger = logging.getLogger(__name__)


class SpatialGroundingStrategy(BaseStrategy):
    """
    Snappy Spatial Grounding: Patch-to-Region Relevance Propagation.

    This approach:
    - Uses ColPali's interpretability maps for per-token attention
    - Maps attention to OCR regions via IoU-weighted aggregation
    - Filters regions by relevance threshold
    - Returns spatially-grounded, query-relevant regions
    """

    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return "spatial_grounding"

    def process(
        self,
        sample: BenchmarkSample,
        image: Image.Image,
    ) -> StrategyResult:
        """
        Process a sample using Spatial Grounding approach.

        Steps:
        1. Run OCR to extract regions with bounding boxes
        2. Generate interpretability maps
        3. Filter regions by relevance
        4. Send filtered regions to LLM
        """
        result = StrategyResult()
        total_timer = Timer()

        try:
            with total_timer:
                # Step 1: Run OCR to get regions with bounding boxes
                ocr_result = self._run_ocr(image, result.timing)
                if not ocr_result:
                    result.error = "OCR returned no results"
                    return result

                # Extract regions from OCR result
                all_regions = self._extract_regions(ocr_result)
                result.ocr_content = ocr_result.get("text", "") or ocr_result.get("markdown", "")

                if not all_regions:
                    # Fall back to full page if no regions extracted
                    result.regions = [{
                        "content": result.ocr_content,
                        "bbox": [0, 0, image.width, image.height],
                        "label": "full_page",
                    }]
                else:
                    # Step 2: Generate interpretability maps
                    interp_result = self._generate_interpretability_maps(
                        sample.query, image, result.timing
                    )

                    if interp_result:
                        # Step 3: Filter regions by relevance
                        result.regions = self._filter_regions_by_relevance(
                            all_regions,
                            interp_result,
                            image.width,
                            image.height,
                            result.timing,
                        )
                    else:
                        # Fall back to all regions if interpretability failed
                        result.regions = all_regions

                # Step 4: Generate answer with LLM using filtered regions
                context = self._format_regions_as_context(result.regions)
                if not context:
                    context = result.ocr_content

                llm_response, llm_tokens = self._call_llm(
                    sample.query, context, result.timing
                )
                result.llm_response = llm_response
                result.tokens = llm_tokens

            result.timing.total_time_ms = total_timer.elapsed_ms

        except Exception as e:
            logger.error(f"Error in Spatial Grounding strategy: {e}", exc_info=True)
            result.error = str(e)

        return result

    def _run_ocr(
        self,
        image: Image.Image,
        timing: TimingMetrics,
    ) -> Optional[Dict[str, Any]]:
        """Run OCR with grounding enabled to get regions."""
        ocr_timer = Timer()

        try:
            with ocr_timer:
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                files = {"file": ("image.png", img_buffer, "image/png")}
                data = {
                    "mode": self.config.ocr_mode,
                    "task": self.config.ocr_task,
                    "include_grounding": "true",  # Always enable grounding
                    "include_images": "false",
                }

                response = self._session.post(
                    f"{self.config.ocr_url}/ocr/process-page",
                    files=files,
                    data=data,
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

        finally:
            timing.ocr_time_ms = ocr_timer.elapsed_ms

    def _extract_regions(
        self,
        ocr_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract regions with bounding boxes from OCR result."""
        regions = []
        bounding_boxes = ocr_result.get("bounding_boxes", [])

        for bbox in bounding_boxes:
            region = {
                "content": bbox.get("label", ""),
                "bbox": [bbox.get("x1", 0), bbox.get("y1", 0), bbox.get("x2", 0), bbox.get("y2", 0)],
                "label": "text",
            }
            # Only include regions with valid bounding boxes
            if any(region["bbox"]):
                regions.append(region)

        return regions

    def _generate_interpretability_maps(
        self,
        query: str,
        image: Image.Image,
        timing: TimingMetrics,
    ) -> Optional[Dict[str, Any]]:
        """Generate ColPali interpretability maps."""
        interp_timer = Timer()

        try:
            with interp_timer:
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                files = {"file": ("image.png", img_buffer, "image/png")}
                data = {"query": query}

                response = self._session.post(
                    f"{self.config.colpali_url}/interpret",
                    files=files,
                    data=data,
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Interpretability generation failed: {e}")
            return None

        finally:
            timing.interpretability_time_ms = interp_timer.elapsed_ms

    def _filter_regions_by_relevance(
        self,
        regions: List[Dict[str, Any]],
        interp_result: Dict[str, Any],
        image_width: int,
        image_height: int,
        timing: TimingMetrics,
    ) -> List[Dict[str, Any]]:
        """
        Filter regions based on interpretability maps using IoU-weighted aggregation.

        This implements the Patch-to-Region Relevance Propagation algorithm.
        """
        filter_timer = Timer()

        try:
            with filter_timer:
                similarity_maps = interp_result.get("similarity_maps", [])
                n_patches_x = interp_result.get("n_patches_x", 0)
                n_patches_y = interp_result.get("n_patches_y", 0)

                if not similarity_maps or not n_patches_x or not n_patches_y:
                    logger.warning("Invalid interpretability result, returning all regions")
                    return regions

                # Convert similarity maps to numpy arrays
                token_maps = []
                for sim_map in similarity_maps:
                    map_data = sim_map.get("similarity_map", [])
                    if map_data:
                        token_maps.append(np.array(map_data))

                if not token_maps:
                    return regions

                # Compute patch dimensions in pixels
                patch_width = image_width / n_patches_x
                patch_height = image_height / n_patches_y

                # Score each region using IoU-weighted aggregation
                scored_regions = []
                for region in regions:
                    bbox = region.get("bbox", [])
                    if not bbox or len(bbox) < 4:
                        continue

                    x1, y1, x2, y2 = bbox[:4]

                    # Convert pixel coordinates to patch indices
                    patch_x1 = int(x1 / patch_width)
                    patch_y1 = int(y1 / patch_height)
                    patch_x2 = int(np.ceil(x2 / patch_width))
                    patch_y2 = int(np.ceil(y2 / patch_height))

                    # Clamp to valid patch range
                    patch_x1 = max(0, min(patch_x1, n_patches_x - 1))
                    patch_y1 = max(0, min(patch_y1, n_patches_y - 1))
                    patch_x2 = max(patch_x1 + 1, min(patch_x2, n_patches_x))
                    patch_y2 = max(patch_y1 + 1, min(patch_y2, n_patches_y))

                    # Compute relevance score using IoU-weighted aggregation
                    token_scores = []
                    for token_map in token_maps:
                        region_patch_values = token_map[patch_y1:patch_y2, patch_x1:patch_x2]
                        if region_patch_values.size > 0:
                            # Use max similarity within the region for this token
                            token_score = float(np.max(region_patch_values))
                            token_scores.append(token_score)

                    # Aggregate across tokens based on config
                    if token_scores:
                        if self.config.relevance_aggregation == "max":
                            relevance_score = max(token_scores)
                        elif self.config.relevance_aggregation == "mean":
                            relevance_score = float(np.mean(token_scores))
                        elif self.config.relevance_aggregation == "sum":
                            relevance_score = sum(token_scores)
                        else:
                            relevance_score = max(token_scores)
                    else:
                        relevance_score = 0.0

                    region_with_score = region.copy()
                    region_with_score["relevance_score"] = relevance_score
                    scored_regions.append((region_with_score, relevance_score))

                # Sort by relevance score
                scored_regions.sort(key=lambda x: x[1], reverse=True)

                # Filter by threshold
                filtered = [
                    r for r, score in scored_regions
                    if score >= self.config.relevance_threshold
                ]

                # Apply top-k limit if configured
                if self.config.region_top_k > 0:
                    filtered = filtered[:self.config.region_top_k]

                logger.info(
                    f"Region filtering: {len(regions)} -> {len(filtered)} "
                    f"(threshold={self.config.relevance_threshold})"
                )

                return filtered if filtered else regions  # Fall back to all if none pass threshold

        except Exception as e:
            logger.error(f"Region filtering failed: {e}")
            return regions

        finally:
            timing.region_filtering_time_ms = filter_timer.elapsed_ms

    def _call_llm(
        self,
        query: str,
        context: str,
        timing: TimingMetrics,
    ) -> tuple[str, TokenMetrics]:
        """Call LLM to generate answer."""
        llm_timer = Timer()
        tokens = TokenMetrics()

        try:
            with llm_timer:
                prompt = self._build_llm_prompt(query, context)
                tokens.input_tokens = self._count_tokens(prompt)

                response = self._session.post(
                    f"{self.config.llm_url}/v1/chat/completions",
                    json={
                        "model": self.config.llm_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.config.llm_temperature,
                        "max_tokens": self.config.llm_max_tokens,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()

                answer = result["choices"][0]["message"]["content"]

                usage = result.get("usage", {})
                tokens.input_tokens = usage.get("prompt_tokens", tokens.input_tokens)
                tokens.output_tokens = usage.get("completion_tokens", self._count_tokens(answer))
                tokens.total_tokens = tokens.input_tokens + tokens.output_tokens

                return answer, tokens

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Error: {e}", tokens

        finally:
            timing.llm_time_ms = llm_timer.elapsed_ms
