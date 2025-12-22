"""
Region relevance scoring based on interpretability maps.

This module provides utilities to compute relevance scores for OCR regions
based on ColPali interpretability maps, enabling query-focused region filtering.

Implements the IoU-weighted aggregation method from the paper:
"Spatially-Grounded Document Retrieval via Patch-to-Region Relevance Propagation"

The region relevance score is computed as:
    rel(q, r) = Σⱼ IoU(B'(r), patch_bbox(j)) · score_patch(j)
                ─────────────────────────────────────────────
                Σⱼ IoU(B'(r), patch_bbox(j))

where score_patch(j) = maxᵢ S[i,j] (max similarity of patch j to any query token)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def _compute_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """
    Compute Intersection over Union between two bounding boxes.

    Args:
        box1: (x1, y1, x2, y2) coordinates
        box2: (x1, y1, x2, y2) coordinates

    Returns:
        IoU value between 0 and 1
    """
    # Compute intersection
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)

    # Compute union
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def compute_region_relevance_scores(
    regions: List[Dict[str, Any]],
    similarity_maps: List[Dict[str, Any]],
    n_patches_x: int,
    n_patches_y: int,
    image_width: int,
    image_height: int,
    aggregation: str = "iou_weighted",
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Compute relevance scores for OCR regions based on interpretability maps.

    Implements the paper's IoU-weighted aggregation by default:
        rel(q, r) = Σⱼ IoU(B'(r), patch_bbox(j)) · score_patch(j)
                    ─────────────────────────────────────────────
                    Σⱼ IoU(B'(r), patch_bbox(j))

    Args:
        regions: List of OCR region dictionaries with 'bbox' field containing [x1, y1, x2, y2]
        similarity_maps: List of per-token similarity maps from interpretability response
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        aggregation: How to aggregate patch scores for a region:
            - 'iou_weighted': IoU-weighted average (paper's method, default)
            - 'max': Maximum patch score in region
            - 'mean': Simple average of patch scores

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
                token_map = np.array(map_data)
                token_maps.append(token_map)

        if not token_maps:
            logger.warning("No valid similarity maps found")
            return [(region, 0.0) for region in regions]

        # Stack token maps and compute per-patch score: score_patch(j) = max_i S[i,j]
        # This gives the maximum relevance of each patch to any query token
        stacked_maps = np.stack(token_maps, axis=0)  # Shape: (n_tokens, n_patches_y, n_patches_x)
        patch_scores = np.max(stacked_maps, axis=0)  # Shape: (n_patches_y, n_patches_x)

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
            region_x1, region_y1, region_x2, region_y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            region_bbox = (region_x1, region_y1, region_x2, region_y2)

            # Find patches that could overlap with this region
            patch_x1_idx = max(0, int(region_x1 / patch_width))
            patch_y1_idx = max(0, int(region_y1 / patch_height))
            patch_x2_idx = min(n_patches_x, int(np.ceil(region_x2 / patch_width)))
            patch_y2_idx = min(n_patches_y, int(np.ceil(region_y2 / patch_height)))

            if aggregation == "iou_weighted":
                # Paper's method: IoU-weighted aggregation
                # rel(q, r) = Σⱼ IoU(region, patch_j) · score_patch(j) / Σⱼ IoU(region, patch_j)
                weighted_sum = 0.0
                iou_sum = 0.0

                for py in range(patch_y1_idx, patch_y2_idx):
                    for px in range(patch_x1_idx, patch_x2_idx):
                        # Compute patch bounding box in pixels
                        patch_bbox = (
                            px * patch_width,
                            py * patch_height,
                            (px + 1) * patch_width,
                            (py + 1) * patch_height,
                        )

                        iou = _compute_iou(region_bbox, patch_bbox)
                        if iou > 0:
                            patch_score = float(patch_scores[py, px])
                            weighted_sum += iou * patch_score
                            iou_sum += iou

                if iou_sum > 0:
                    relevance_score = weighted_sum / iou_sum
                else:
                    relevance_score = 0.0

            elif aggregation == "max":
                # Max aggregation: rel_max(q, r) = max_{j in covered(r)} score_patch(j)
                region_patch_values = patch_scores[patch_y1_idx:patch_y2_idx, patch_x1_idx:patch_x2_idx]
                if region_patch_values.size > 0:
                    relevance_score = float(np.max(region_patch_values))
                else:
                    relevance_score = 0.0

            elif aggregation == "mean":
                # Mean aggregation: rel_mean(q, r) = mean_{j in covered(r)} score_patch(j)
                region_patch_values = patch_scores[patch_y1_idx:patch_y2_idx, patch_x1_idx:patch_x2_idx]
                if region_patch_values.size > 0:
                    relevance_score = float(np.mean(region_patch_values))
                else:
                    relevance_score = 0.0

            else:
                logger.warning(f"Unknown aggregation method: {aggregation}, using iou_weighted")
                # Fall back to IoU-weighted
                weighted_sum = 0.0
                iou_sum = 0.0
                for py in range(patch_y1_idx, patch_y2_idx):
                    for px in range(patch_x1_idx, patch_x2_idx):
                        patch_bbox = (
                            px * patch_width,
                            py * patch_height,
                            (px + 1) * patch_width,
                            (py + 1) * patch_height,
                        )
                        iou = _compute_iou(region_bbox, patch_bbox)
                        if iou > 0:
                            weighted_sum += iou * float(patch_scores[py, px])
                            iou_sum += iou
                relevance_score = weighted_sum / iou_sum if iou_sum > 0 else 0.0

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
    aggregation: str = "iou_weighted",
) -> List[Dict[str, Any]]:
    """
    Filter and rank OCR regions based on interpretability map relevance.

    Uses the paper's IoU-weighted aggregation by default.

    Args:
        regions: List of OCR region dictionaries
        similarity_maps: Per-token similarity maps from interpretability response
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        threshold: Minimum relevance score (0.0-1.0) to include a region
        top_k: Maximum number of regions to return (None = all above threshold)
        aggregation: How to aggregate patch scores ('iou_weighted', 'max', 'mean')

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
