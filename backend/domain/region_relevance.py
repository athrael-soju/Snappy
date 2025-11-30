"""
Region relevance scoring based on interpretability maps.

This module provides utilities to compute relevance scores for OCR regions
based on ColPali interpretability maps, enabling query-focused region filtering.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def compute_region_relevance_scores(
    regions: List[Dict[str, Any]],
    similarity_maps: List[Dict[str, Any]],
    n_patches_x: int,
    n_patches_y: int,
    image_width: int,
    image_height: int,
    aggregation: str = "max",
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Compute relevance scores for OCR regions based on interpretability maps.

    Args:
        regions: List of OCR region dictionaries with 'bbox' field containing {x1, y1, x2, y2}
        similarity_maps: List of per-token similarity maps from interpretability response
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        aggregation: How to aggregate scores across query tokens ('max', 'mean', 'sum')

    Returns:
        List of tuples (region, relevance_score) sorted by score descending
    """
    if not regions or not similarity_maps:
        logger.warning("No regions or similarity maps provided for relevance scoring")
        return []

    try:
        # Convert similarity maps to numpy arrays for efficient computation
        # Each similarity map is a 2D array of shape (n_patches_y, n_patches_x)
        token_maps = []
        for sim_map in similarity_maps:
            map_data = sim_map.get("similarity_map", [])
            if map_data:
                # Convert to numpy array
                token_map = np.array(map_data)
                token_maps.append(token_map)

        if not token_maps:
            logger.warning("No valid similarity maps found")
            return [(region, 0.0) for region in regions]

        # Compute patch dimensions in pixels
        patch_width = image_width / n_patches_x
        patch_height = image_height / n_patches_y

        # Score each region
        region_scores = []
        for region in regions:
            bbox = region.get("bbox", [])
            if not bbox or not isinstance(bbox, list) or len(bbox) < 4:
                region_scores.append((region, 0.0))
                continue

            # Get region coordinates (in pixels)
            # bbox is stored as [x1, y1, x2, y2]
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

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

            # Extract region similarity values from each token's map
            token_scores = []
            for token_map in token_maps:
                # Get the similarity values for patches overlapping this region
                region_patch_values = token_map[patch_y1:patch_y2, patch_x1:patch_x2]

                if region_patch_values.size > 0:
                    # Use max similarity within the region for this token
                    token_score = float(np.max(region_patch_values))
                    token_scores.append(token_score)

            # Aggregate across query tokens
            if token_scores:
                if aggregation == "max":
                    relevance_score = max(token_scores)
                elif aggregation == "mean":
                    relevance_score = float(np.mean(token_scores))
                elif aggregation == "sum":
                    relevance_score = sum(token_scores)
                else:
                    logger.warning(
                        f"Unknown aggregation method: {aggregation}, using max"
                    )
                    relevance_score = max(token_scores)
            else:
                relevance_score = 0.0

            region_scores.append((region, relevance_score))

        # Sort by relevance score descending
        region_scores.sort(key=lambda x: x[1], reverse=True)

        return region_scores

    except Exception as e:
        logger.error(f"Error computing region relevance scores: {e}", exc_info=True)
        # Return regions with zero scores on error
        return [(region, 0.0) for region in regions]


def filter_regions_by_relevance(
    regions: List[Dict[str, Any]],
    similarity_maps: List[Dict[str, Any]],
    n_patches_x: int,
    n_patches_y: int,
    image_width: int,
    image_height: int,
    threshold: float = 0.0,
    top_k: Optional[int] = None,
    aggregation: str = "max",
) -> List[Dict[str, Any]]:
    """
    Filter and rank OCR regions based on interpretability map relevance.

    Args:
        regions: List of OCR region dictionaries
        similarity_maps: Per-token similarity maps from interpretability response
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        threshold: Minimum relevance score (0.0-1.0) to include a region
        top_k: Maximum number of regions to return (None = all above threshold)
        aggregation: How to aggregate scores across query tokens

    Returns:
        Filtered and ranked list of regions with relevance scores added
    """
    # Compute relevance scores
    region_scores = compute_region_relevance_scores(
        regions,
        similarity_maps,
        n_patches_x,
        n_patches_y,
        image_width,
        image_height,
        aggregation,
    )

    # Filter by threshold
    filtered = [
        (region, score) for region, score in region_scores if score >= threshold
    ]

    # Apply top-k limit
    if top_k is not None and top_k > 0:
        filtered = filtered[:top_k]

    # Add relevance score to region metadata
    result = []
    for region, score in filtered:
        region_with_score = region.copy()
        region_with_score["relevance_score"] = score
        result.append(region_with_score)

    logger.info(
        f"Filtered regions: {len(regions)} -> {len(result)} "
        f"(threshold={threshold}, top_k={top_k})"
    )

    # Log detailed region information at debug level
    if result and logger.isEnabledFor(logging.DEBUG):
        logger.debug("Filtered region details:")
        for idx, region in enumerate(result, 1):
            # Get text content (field name is "content" in OCR regions)
            text = region.get("content", "")
            text_preview = text[:100] if text else ""
            text_suffix = "..." if len(text) > 100 else ""
            score = region.get("relevance_score", 0.0)
            bbox = region.get("bbox", [])

            logger.debug(
                f"  Region {idx}: score={score:.4f}, bbox={bbox}, "
                f"label={region.get('label', 'N/A')}, "
                f"text='{text_preview}{text_suffix}'"
            )

    return result
