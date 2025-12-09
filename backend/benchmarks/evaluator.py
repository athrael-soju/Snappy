"""
Spatial grounding evaluator using ColPali patch-level similarity.

This module integrates ColPali's interpretability maps with the benchmark
evaluation framework to validate spatial grounding claims from arXiv:2512.02660.

Implements the Snappy approach: OCR regions + ColPali patch-to-region relevance
propagation. Both services (DeepSeek OCR and ColPali) are required.
"""

import logging
from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from PIL import Image

from benchmarks.data_loader import BBoxDocVQASample
from benchmarks.metrics import (
    IoUMetrics,
    compute_context_reduction,
    compute_iou,
    evaluate_multi_region,
)
from benchmarks.strategies import FilteringStrategy, ScoredRegion

if TYPE_CHECKING:
    from clients.ocr.client import OcrClient

logger = logging.getLogger(__name__)


# Default ColPali configuration
DEFAULT_IMAGE_SIZE = 448
DEFAULT_PATCH_SIZE = 14
DEFAULT_GRID_SIZE = 32  # 448 / 14


@dataclass
class PatchConfig:
    """Configuration for patch-based processing."""

    image_size: int = DEFAULT_IMAGE_SIZE
    patch_size: int = DEFAULT_PATCH_SIZE

    @property
    def grid_size(self) -> int:
        return self.image_size // self.patch_size


@dataclass
class EvaluationResult:
    """Result from evaluating a single sample."""

    sample_id: str
    query: str
    instance_type: str
    category: str
    metrics: IoUMetrics
    predicted_bboxes: List[List[int]]  # Selected bboxes after filtering
    ground_truth_bboxes: List[List[int]]
    region_scores: List[
        Tuple[List[int], float, str]
    ]  # All (bbox, score, label) triples before filtering
    image_dimensions: List[Tuple[int, int]]  # Per-page (width, height)
    error: Optional[str] = None
    # For simplified reporting - all OCR regions detected
    all_ocr_regions: Optional[List[List[int]]] = None
    # Aggregated similarity map (max across tokens) for visualization
    aggregated_similarity_map: Optional[np.ndarray] = None
    # Per-prediction IoU with best matching GT
    prediction_ious: Optional[List[float]] = None


class SpatialGroundingEvaluator:
    """
    Evaluator for ColPali-based spatial grounding.

    Implements the Snappy approach (arXiv:2512.02660):
    - DeepSeek OCR extracts text regions with bounding boxes
    - ColPali generates patch-level similarity maps
    - Patch-to-region relevance propagation scores each OCR region

    Both ColPali and OCR services are required for evaluation.
    """

    def __init__(
        self,
        colpali_client: Optional[Any] = None,
        ocr_client: Optional["OcrClient"] = None,
        patch_config: Optional[PatchConfig] = None,
        score_aggregation: str = "max",
    ):
        """
        Initialize the evaluator.

        Args:
            colpali_client: ColPaliClient for generating interpretability maps (required)
            ocr_client: OcrClient for region extraction (required)
            patch_config: Patch configuration (defaults to standard ColPali)
            score_aggregation: How to aggregate patch scores ('max', 'mean', 'iou_weighted')
        """
        self.colpali_client = colpali_client
        self.ocr_client = ocr_client
        self.config = patch_config or PatchConfig()
        self.score_aggregation = score_aggregation

    def extract_ocr_regions(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Extract OCR regions from an image using DeepSeek OCR.

        Args:
            image: PIL Image to process

        Returns:
            List of region dictionaries with 'bbox' [x1, y1, x2, y2], 'label', and 'content'

        Raises:
            RuntimeError: If OCR client is not available or OCR fails
        """
        if self.ocr_client is None:
            raise RuntimeError("OCR client required for region extraction")

        # Run OCR with grounding enabled to get bounding boxes
        result = self.ocr_client.run_ocr_image(
            image,
            include_grounding=True,
            include_images=False,  # Don't need image extraction for benchmarking
        )

        # Extract bounding boxes from response
        bboxes = result.get("bounding_boxes", [])
        if not bboxes:
            raise RuntimeError("OCR returned no bounding boxes for image")

        regions = []
        for bbox in bboxes:
            x1 = int(bbox.get("x1", 0))
            y1 = int(bbox.get("y1", 0))
            x2 = int(bbox.get("x2", 0))
            y2 = int(bbox.get("y2", 0))
            label = bbox.get("label", "text")  # Default to 'text' if not specified

            # Validate bbox dimensions
            if x2 > x1 and y2 > y1:
                regions.append(
                    {
                        "bbox": [x1, y1, x2, y2],
                        "label": label,
                        "content": "",  # Content not available in benchmark mode
                    }
                )

        if not regions:
            raise RuntimeError("OCR returned no valid bounding boxes")

        logger.debug(f"Extracted {len(regions)} OCR regions from image")
        return regions

    def patch_to_pixel_bbox(self, patch_idx: int) -> List[int]:
        """
        Convert a patch index to pixel coordinates.

        Args:
            patch_idx: Flattened patch index (row-major order)

        Returns:
            Bbox as [x_min, y_min, x_max, y_max]
        """
        row = patch_idx // self.config.grid_size
        col = patch_idx % self.config.grid_size

        x_min = col * self.config.patch_size
        y_min = row * self.config.patch_size
        x_max = (col + 1) * self.config.patch_size
        y_max = (row + 1) * self.config.patch_size

        return [x_min, y_min, x_max, y_max]

    def get_overlapping_patches_dynamic(
        self,
        bbox: List[int],
        image_width: int,
        image_height: int,
        grid_rows: int,
        grid_cols: int,
    ) -> List[Tuple[int, int, float]]:
        """
        Find all patches overlapping with a bounding box using dynamic grid size.

        Args:
            bbox: Region bbox as [x1, y1, x2, y2] in original image coords
            image_width: Original image width
            image_height: Original image height
            grid_rows: Number of rows in the patch grid
            grid_cols: Number of columns in the patch grid

        Returns:
            List of (row, col, iou) tuples for overlapping patches
        """
        # Compute patch dimensions based on actual grid size
        patch_width = image_width / grid_cols
        patch_height = image_height / grid_rows

        # Convert bbox to patch indices
        col_start = max(0, int(bbox[0] / patch_width))
        col_end = min(grid_cols - 1, int(ceil(bbox[2] / patch_width)) - 1)
        row_start = max(0, int(bbox[1] / patch_height))
        row_end = min(grid_rows - 1, int(ceil(bbox[3] / patch_height)) - 1)

        # Ensure valid ranges
        col_end = max(col_start, col_end)
        row_end = max(row_start, row_end)

        patches = []
        bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                # Compute patch bbox in original image coordinates
                patch_bbox = [
                    col * patch_width,
                    row * patch_height,
                    (col + 1) * patch_width,
                    (row + 1) * patch_height,
                ]

                # Compute IoU
                xi1 = max(patch_bbox[0], bbox[0])
                yi1 = max(patch_bbox[1], bbox[1])
                xi2 = min(patch_bbox[2], bbox[2])
                yi2 = min(patch_bbox[3], bbox[3])

                inter_width = max(0, xi2 - xi1)
                inter_height = max(0, yi2 - yi1)
                intersection = inter_width * inter_height

                patch_area = patch_width * patch_height
                union = patch_area + bbox_area - intersection
                iou = intersection / union if union > 0 else 0

                if intersection > 0:
                    patches.append((row, col, iou))

        return patches

    def get_overlapping_patches(
        self,
        bbox: List[int],
        image_width: int,
        image_height: int,
    ) -> List[Tuple[int, float]]:
        """
        Find all patches overlapping with a bounding box (legacy fixed grid).

        Args:
            bbox: Region bbox as [x1, y1, x2, y2] in original image coords
            image_width: Original image width
            image_height: Original image height

        Returns:
            List of (patch_idx, iou) tuples for overlapping patches
        """
        # Use the dynamic version with default grid size
        dynamic_results = self.get_overlapping_patches_dynamic(
            bbox,
            image_width,
            image_height,
            self.config.grid_size,
            self.config.grid_size,
        )
        # Convert (row, col, iou) to (patch_idx, iou)
        return [
            (row * self.config.grid_size + col, iou)
            for row, col, iou in dynamic_results
        ]

    def compute_region_score(
        self,
        similarity_map: np.ndarray,
        bbox: List[int],
        image_width: int,
        image_height: int,
        grid_rows: Optional[int] = None,
        grid_cols: Optional[int] = None,
    ) -> float:
        """Compute relevance score for a region from a similarity map.

        Args:
            similarity_map: 2D array of shape (grid_rows, grid_cols)
            bbox: Region bbox in original image coordinates
            image_width: Original image width
            image_height: Original image height
            grid_rows: Number of rows in the patch grid (inferred from map if None)
            grid_cols: Number of columns in the patch grid (inferred from map if None)

        Returns:
            Aggregated relevance score
        """
        # Get actual grid dimensions from the similarity map if not provided
        if grid_rows is None or grid_cols is None:
            grid_rows, grid_cols = similarity_map.shape

        # Ensure type checker knows these are not None
        assert grid_rows is not None and grid_cols is not None

        # Get overlapping patches using dynamic grid size
        overlapping = self.get_overlapping_patches_dynamic(
            bbox, image_width, image_height, grid_rows, grid_cols
        )

        if not overlapping:
            return 0.0

        if self.score_aggregation == "max":
            # Max pooling: highest patch score
            scores = []
            for row, col, _ in overlapping:
                scores.append(similarity_map[row, col])
            return max(scores) if scores else 0.0

        elif self.score_aggregation == "mean":
            # Simple mean pooling
            scores = []
            for row, col, _ in overlapping:
                scores.append(similarity_map[row, col])
            return float(np.mean(scores)) if scores else 0.0

        elif self.score_aggregation == "iou_weighted":
            # IoU-weighted mean pooling
            weighted_sum = 0.0
            weight_total = 0.0
            for row, col, iou in overlapping:
                weighted_sum += similarity_map[row, col] * iou
                weight_total += iou
            return weighted_sum / weight_total if weight_total > 0 else 0.0

        else:
            raise ValueError(f"Unknown aggregation: {self.score_aggregation}")

    def score_regions_from_map(
        self,
        similarity_maps: List[np.ndarray],
        candidate_regions: List,  # Can be List[List[int]] or List[Dict]
        image_width: int,
        image_height: int,
        token_aggregation: str = "max",
        grid_rows: Optional[int] = None,
        grid_cols: Optional[int] = None,
    ) -> List[ScoredRegion]:
        """Score candidate regions using precomputed similarity maps.

        Args:
            similarity_maps: Per-token similarity maps, each (grid_rows, grid_cols)
            candidate_regions: List of regions (bbox lists or dicts with 'bbox' key)
            image_width: Original image width
            image_height: Original image height
            token_aggregation: How to aggregate across tokens ('max', 'mean')
            grid_rows: Actual number of rows in the patch grid (from ColPali)
            grid_cols: Actual number of columns in the patch grid (from ColPali)

        Returns:
            List of ScoredRegion objects with label metadata
        """
        # Use actual grid dimensions from similarity maps if not provided
        if grid_rows is None or grid_cols is None:
            if similarity_maps:
                grid_rows, grid_cols = similarity_maps[0].shape
            else:
                grid_rows = self.config.grid_size
                grid_cols = self.config.grid_size

        scored_regions = []

        for region in candidate_regions:
            # Handle both bbox lists and region dictionaries
            if isinstance(region, dict):
                bbox = region["bbox"]
                label = region.get("label", "")
                content = region.get("content", "")
            else:
                bbox = region
                label = ""
                content = ""

            # Compute score for each query token
            token_scores = []
            for sim_map in similarity_maps:
                score = self.compute_region_score(
                    sim_map, bbox, image_width, image_height, grid_rows, grid_cols
                )
                token_scores.append(score)

            # Aggregate across tokens
            if token_aggregation == "max":
                final_score = max(token_scores) if token_scores else 0.0
            elif token_aggregation == "mean":
                final_score = np.mean(token_scores) if token_scores else 0.0
            else:
                final_score = max(token_scores) if token_scores else 0.0

            scored_regions.append(
                ScoredRegion(
                    bbox=bbox, score=float(final_score), label=label, content=content
                )
            )

        # Sort by score descending
        scored_regions.sort(key=lambda r: r.score, reverse=True)
        return scored_regions

    def generate_candidate_regions(
        self,
        image_width: int,
        image_height: int,
        mode: str = "patches",
        grid_divisions: int = 4,
        grid_rows: Optional[int] = None,
        grid_cols: Optional[int] = None,
    ) -> List[List[int]]:
        """
        Generate candidate regions for evaluation.

        When OCR regions are not available, we can use patch-based
        or grid-based candidate regions.

        Args:
            image_width: Image width
            image_height: Image height
            mode: 'patches' (ColPali patches) or 'grid' (uniform grid)
            grid_divisions: Number of grid divisions (for 'grid' mode)
            grid_rows: Optional override for patch grid rows
            grid_cols: Optional override for patch grid columns

        Returns:
            List of candidate bboxes in original image coordinates
        """
        if mode == "patches":
            # Use individual patches as candidates
            # Use provided grid size or fall back to config default
            rows = grid_rows if grid_rows is not None else self.config.grid_size
            cols = grid_cols if grid_cols is not None else self.config.grid_size

            candidates = []
            patch_width = image_width / cols
            patch_height = image_height / rows

            for row in range(rows):
                for col in range(cols):
                    bbox = [
                        int(col * patch_width),
                        int(row * patch_height),
                        int((col + 1) * patch_width),
                        int((row + 1) * patch_height),
                    ]
                    candidates.append(bbox)
            return candidates

        elif mode == "grid":
            # Uniform grid
            candidates = []
            cell_width = image_width // grid_divisions
            cell_height = image_height // grid_divisions

            for row in range(grid_divisions):
                for col in range(grid_divisions):
                    bbox = [
                        col * cell_width,
                        row * cell_height,
                        (col + 1) * cell_width,
                        (row + 1) * cell_height,
                    ]
                    candidates.append(bbox)
            return candidates

        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def evaluate_sample_online(
        self,
        sample: BBoxDocVQASample,
        image: Image.Image,
        filtering_strategy: FilteringStrategy,
        candidate_regions: Optional[
            List
        ] = None,  # Can be List[List[int]] or List[Dict]
    ) -> EvaluationResult:
        """
        Evaluate a sample using online ColPali API.

        Args:
            sample: The BBox-DocVQA sample
            image: The document image
            filtering_strategy: Strategy for filtering scored regions
            candidate_regions: Optional candidate regions (defaults to patches)

        Returns:
            EvaluationResult with metrics
        """
        if self.colpali_client is None:
            raise ValueError("ColPali client required for online evaluation")

        try:
            # Get image dimensions
            image_width, image_height = image.size

            # Generate interpretability maps
            interp_result = self.colpali_client.generate_interpretability_maps(
                sample.query, image
            )

            # Extract similarity maps from ColPali interpretability response
            similarity_maps = []
            for token_data in interp_result.get("similarity_maps", []):
                if isinstance(token_data, dict):
                    sim_map = np.array(token_data.get("similarity_map", []))
                else:
                    sim_map = np.array(token_data)
                if sim_map.size > 0:
                    similarity_maps.append(sim_map)

            if not similarity_maps:
                raise RuntimeError("ColPali returned no similarity maps")

            # Extract actual patch grid dimensions from ColPali response
            # These may differ from the default grid size based on image dimensions
            actual_grid_rows = interp_result.get("n_patches_y", self.config.grid_size)
            actual_grid_cols = interp_result.get("n_patches_x", self.config.grid_size)
            logger.debug(
                f"Using patch grid: {actual_grid_rows}x{actual_grid_cols} "
                f"(image: {image_width}x{image_height})"
            )

            # Extract OCR regions - this is the core of the Snappy approach
            # No fallbacks: OCR regions are required for proper evaluation
            if candidate_regions is None:
                candidate_regions = self.extract_ocr_regions(image)
                logger.debug(
                    f"Using {len(candidate_regions)} OCR regions as candidates"
                )

            # Store all OCR region bboxes before scoring (for visualization)
            all_ocr_regions = [
                r["bbox"] if isinstance(r, dict) else r for r in candidate_regions
            ]

            # Create aggregated similarity map (max across all tokens)
            aggregated_map = np.max(np.stack(similarity_maps, axis=0), axis=0)

            # Score regions
            scored_regions = self.score_regions_from_map(
                similarity_maps,
                candidate_regions,
                image_width,
                image_height,
            )

            # Apply filtering strategy
            filtered_regions = filtering_strategy.filter(scored_regions)
            predicted_bboxes = [r.bbox for r in filtered_regions]

            # Get ground truth (first page only for now)
            gt_bboxes = sample.bboxes[0] if sample.bboxes else []

            # Compute metrics
            metrics = evaluate_multi_region(predicted_bboxes, gt_bboxes)
            metrics.context_reduction = compute_context_reduction(
                predicted_bboxes, image_width, image_height
            )

            # Compute per-prediction IoU with best matching GT
            prediction_ious = []
            for pred_bbox in predicted_bboxes:
                best_iou = 0.0
                for gt_bbox in gt_bboxes:
                    iou = compute_iou(pred_bbox, gt_bbox)
                    best_iou = max(best_iou, iou)
                prediction_ious.append(best_iou)

            return EvaluationResult(
                sample_id=f"{sample.doc_name}_{sample.evidence_pages[0]}",
                query=sample.query,
                instance_type=sample.instance_type,
                category=sample.category,
                metrics=metrics,
                predicted_bboxes=predicted_bboxes,
                ground_truth_bboxes=gt_bboxes,
                region_scores=[(r.bbox, r.score, r.label) for r in scored_regions],
                image_dimensions=[(image_width, image_height)],
                all_ocr_regions=all_ocr_regions,
                aggregated_similarity_map=aggregated_map,
                prediction_ious=prediction_ious,
            )

        except Exception as e:
            logger.error(f"Error evaluating sample {sample.doc_name}: {e}")
            return EvaluationResult(
                sample_id=f"{sample.doc_name}_{sample.evidence_pages[0] if sample.evidence_pages else 0}",
                query=sample.query,
                instance_type=sample.instance_type,
                category=sample.category,
                metrics=IoUMetrics(),
                predicted_bboxes=[],
                ground_truth_bboxes=sample.bboxes[0] if sample.bboxes else [],
                region_scores=[],
                image_dimensions=[],
                error=str(e),
            )

    def evaluate_sample_offline(
        self,
        sample: BBoxDocVQASample,
        similarity_maps: List[np.ndarray],
        image_dimensions: Tuple[int, int],
        filtering_strategy: FilteringStrategy,
        candidate_regions: Optional[List[List[int]]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a sample using precomputed similarity maps.

        Args:
            sample: The BBox-DocVQA sample
            similarity_maps: Precomputed per-token similarity maps
            image_dimensions: (width, height) of the image
            filtering_strategy: Strategy for filtering scored regions
            candidate_regions: Optional candidate regions

        Returns:
            EvaluationResult with metrics
        """
        try:
            image_width, image_height = image_dimensions

            # Generate candidates if not provided
            if candidate_regions is None:
                candidate_regions = self.generate_candidate_regions(
                    image_width, image_height, mode="patches"
                )

            # Score regions
            scored_regions = self.score_regions_from_map(
                similarity_maps,
                candidate_regions,
                image_width,
                image_height,
            )

            # Apply filtering strategy
            filtered_regions = filtering_strategy.filter(scored_regions)
            predicted_bboxes = [r.bbox for r in filtered_regions]

            # Get ground truth (first page only for now)
            gt_bboxes = sample.bboxes[0] if sample.bboxes else []

            # Compute metrics
            metrics = evaluate_multi_region(predicted_bboxes, gt_bboxes)
            metrics.context_reduction = compute_context_reduction(
                predicted_bboxes, image_width, image_height
            )

            return EvaluationResult(
                sample_id=f"{sample.doc_name}_{sample.evidence_pages[0]}",
                query=sample.query,
                instance_type=sample.instance_type,
                category=sample.category,
                metrics=metrics,
                predicted_bboxes=predicted_bboxes,
                ground_truth_bboxes=gt_bboxes,
                region_scores=[(r.bbox, r.score, r.label) for r in scored_regions],
                image_dimensions=[image_dimensions],
            )

        except Exception as e:
            logger.error(f"Error evaluating sample {sample.doc_name}: {e}")
            return EvaluationResult(
                sample_id=f"{sample.doc_name}_{sample.evidence_pages[0] if sample.evidence_pages else 0}",
                query=sample.query,
                instance_type=sample.instance_type,
                category=sample.category,
                metrics=IoUMetrics(),
                predicted_bboxes=[],
                ground_truth_bboxes=sample.bboxes[0] if sample.bboxes else [],
                region_scores=[],
                image_dimensions=[],
                error=str(e),
            )

    def merge_adjacent_patches(
        self,
        scored_regions: List[ScoredRegion],
        score_threshold: float = 0.3,
        adjacency_threshold: int = 1,
    ) -> List[ScoredRegion]:
        """
        Merge adjacent high-scoring patches into larger regions.

        This addresses the granularity mismatch between patches and
        semantic regions (paragraphs, tables).

        Args:
            scored_regions: Scored patch regions
            score_threshold: Minimum score to consider for merging
            adjacency_threshold: Max patch distance to consider adjacent

        Returns:
            Merged regions
        """
        # Filter by threshold
        high_scoring = [r for r in scored_regions if r.score >= score_threshold]

        if not high_scoring:
            return []

        # Group into connected components
        # (Simple approach: merge bboxes that overlap or are adjacent)
        merged = []
        used = set()

        for i, region in enumerate(high_scoring):
            if i in used:
                continue

            # Start a new merged region
            bbox = list(region.bbox)
            scores = [region.score]
            used.add(i)

            # Find all adjacent regions
            changed = True
            while changed:
                changed = False
                for j, other in enumerate(high_scoring):
                    if j in used:
                        continue

                    # Check if adjacent (within adjacency_threshold pixels)
                    expanded_bbox = [
                        bbox[0] - adjacency_threshold * self.config.patch_size,
                        bbox[1] - adjacency_threshold * self.config.patch_size,
                        bbox[2] + adjacency_threshold * self.config.patch_size,
                        bbox[3] + adjacency_threshold * self.config.patch_size,
                    ]

                    if self._bboxes_overlap(expanded_bbox, other.bbox):
                        # Merge
                        bbox[0] = min(bbox[0], other.bbox[0])
                        bbox[1] = min(bbox[1], other.bbox[1])
                        bbox[2] = max(bbox[2], other.bbox[2])
                        bbox[3] = max(bbox[3], other.bbox[3])
                        scores.append(other.score)
                        used.add(j)
                        changed = True

            merged.append(
                ScoredRegion(
                    bbox=bbox,
                    score=float(np.mean(scores)),
                )
            )

        return merged

    def _bboxes_overlap(self, bbox1: List[int], bbox2: List[int]) -> bool:
        """Check if two bboxes overlap."""
        return not (
            bbox1[2] <= bbox2[0]
            or bbox1[0] >= bbox2[2]
            or bbox1[3] <= bbox2[1]
            or bbox1[1] >= bbox2[3]
        )
