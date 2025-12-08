"""
Visualization utilities for debugging and qualitative analysis.

Generates overlay images showing:
- Original image
- Patch-level heatmap
- OCR bounding boxes
- Predicted regions (green)
- Ground truth regions (red)
- Overlap regions (yellow)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .aggregation import RegionScore
from .utils.coordinates import NormalizedBox

# Import shared visualization utilities from backend/utils
from utils.colormaps import ColorScale, create_heatmap_rgba
from utils.normalization import NormalizationStrategy, normalize_array

logger = logging.getLogger(__name__)


# Color definitions (RGBA)
COLORS = {
    "prediction": (0, 255, 0, 180),      # Green
    "prediction_hit": (0, 200, 0, 200),  # Dark green for matching predictions
    "prediction_miss": (255, 128, 0, 200),  # Orange for non-matching predictions
    "ground_truth": (255, 0, 0, 180),    # Red
    "overlap": (255, 255, 0, 200),       # Yellow
    "ocr_region": (0, 0, 255, 100),      # Blue (light)
    "heatmap_low": (0, 0, 255),          # Blue
    "heatmap_high": (255, 0, 0),         # Red
}


class BenchmarkVisualizer:
    """
    Generates debug visualizations for benchmark analysis.

    Creates overlay images combining:
    - Base document image
    - Patch-level similarity heatmap
    - OCR region boundaries
    - Predicted and ground truth bounding boxes
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        dpi: int = 150,
        show_scores: bool = True,
        show_labels: bool = True,
        color_scale: ColorScale = ColorScale.YLORRD,
        normalization: NormalizationStrategy = NormalizationStrategy.PERCENTILE,
    ):
        """
        Initialize the visualizer.

        Args:
            output_dir: Directory for saving visualizations
            dpi: Resolution for saved images
            show_scores: Whether to show relevance scores on boxes
            show_labels: Whether to show region labels
            color_scale: ColorBrewer color scale for heatmaps (default: YlOrRd)
            normalization: Normalization strategy for heatmap values (default: percentile)
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.dpi = dpi
        self.show_scores = show_scores
        self.show_labels = show_labels
        self.color_scale = color_scale
        self.normalization = normalization

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_sample(
        self,
        image: Image.Image,
        heatmap: Optional[np.ndarray] = None,
        ocr_regions: Optional[List[Dict[str, Any]]] = None,
        predictions: Optional[List[RegionScore]] = None,
        ground_truth: Optional[List[NormalizedBox]] = None,
        sample_id: str = "",
        query: str = "",
        show_region_heatmap: bool = True,
        all_region_scores: Optional[List[RegionScore]] = None,
    ) -> Image.Image:
        """
        Create a clean visualization for a single sample.

        Shows:
        - Original document with subtle heatmap overlay
        - Ground truth boxes (red outline)
        - Predicted regions (green=HIT, orange=MISS)

        Args:
            image: Original document image
            heatmap: 2D array of patch-level similarity scores
            ocr_regions: List of OCR region dictionaries (unused)
            predictions: Selected/predicted regions with scores
            ground_truth: Ground truth bounding boxes
            sample_id: Identifier for saving
            query: Query text to display
            show_region_heatmap: Whether to show region-level heatmap
            all_region_scores: All OCR regions with scores for heatmap coloring

        Returns:
            Visualization image
        """
        # Create a copy to draw on
        vis_image = image.convert("RGBA")
        width, height = vis_image.size

        # Add subtle patch-level heatmap if available (shows model attention)
        if heatmap is not None:
            heatmap_overlay = self._create_heatmap_overlay(heatmap, width, height, alpha=60)
            vis_image = Image.alpha_composite(vis_image, heatmap_overlay)

        # Create overlay for boxes
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw ground truth boxes first (red outline, thicker)
        if ground_truth:
            for bbox in ground_truth:
                self._draw_normalized_box(
                    draw,
                    bbox,
                    width,
                    height,
                    color=COLORS["ground_truth"],
                    line_width=4,
                )

        # Draw predictions (green=HIT, orange=MISS)
        if predictions:
            from .utils.coordinates import compute_iou

            iou_threshold = 0.25  # Threshold for considering a match
            for pred in predictions:
                # Calculate max IoU with any ground truth
                max_iou = 0.0
                if ground_truth:
                    for gt in ground_truth:
                        iou = compute_iou(pred.bbox, gt)
                        max_iou = max(max_iou, iou)

                # Choose color based on match status
                is_hit = max_iou >= iou_threshold
                color = COLORS["prediction_hit"] if is_hit else COLORS["prediction_miss"]

                # Build label with score and match status
                label = None
                if self.show_scores:
                    status = "HIT" if is_hit else "MISS"
                    label = f"{pred.score:.2f} ({status} IoU={max_iou:.2f})"

                self._draw_normalized_box(
                    draw,
                    pred.bbox,
                    width,
                    height,
                    color=color,
                    line_width=3,
                    label=label,
                )

        # Composite overlay onto image
        vis_image = Image.alpha_composite(vis_image, overlay)

        # Add header with metadata
        vis_image = self._add_header(vis_image, sample_id, query)

        # Save if output directory is set
        if self.output_dir and sample_id:
            output_path = self.output_dir / f"{sample_id}_debug.png"
            vis_image.convert("RGB").save(output_path, dpi=(self.dpi, self.dpi))
            logger.info(f"Saved visualization to {output_path}")

        return vis_image

    def _create_heatmap_overlay(
        self,
        heatmap: np.ndarray,
        width: int,
        height: int,
        alpha: int = 100,
    ) -> Image.Image:
        """
        Create a heatmap overlay from patch scores.

        Uses shared colormap and normalization utilities for professional
        visualization consistent with the frontend.

        Args:
            heatmap: 2D array of scores
            width: Target width
            height: Target height
            alpha: Transparency (0-255)

        Returns:
            RGBA image overlay
        """
        # Normalize heatmap using the configured strategy
        heatmap_norm = normalize_array(heatmap, self.normalization)

        # Apply colormap using shared utilities
        rgba = create_heatmap_rgba(heatmap_norm, self.color_scale, alpha)

        # Create image and resize with smooth interpolation
        heatmap_img = Image.fromarray(rgba, mode="RGBA")
        heatmap_img = heatmap_img.resize((width, height), Image.BILINEAR)

        return heatmap_img

    def _create_region_heatmap_overlay(
        self,
        predictions: List[RegionScore],
        width: int,
        height: int,
        alpha: int = 160,
    ) -> Image.Image:
        """
        Create a region-level heatmap overlay from aggregated region scores.

        Each OCR region is filled with a color based on its aggregated score.
        This shows the actual differences between aggregation methods.

        Uses shared colormap and normalization utilities for professional
        visualization consistent with the frontend.

        Args:
            predictions: List of RegionScore objects with scores
            width: Target width
            height: Target height
            alpha: Transparency (0-255)

        Returns:
            RGBA image overlay
        """
        # Create transparent overlay
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if not predictions:
            logger.warning("No predictions provided for region heatmap")
            return overlay

        # Normalize scores using the configured strategy
        scores = np.array([p.score for p in predictions])
        normalized_scores = normalize_array(scores, self.normalization)

        logger.debug(
            f"Region scores: min={scores.min():.4f}, max={scores.max():.4f}, "
            f"normalized range=[{normalized_scores.min():.2f}, {normalized_scores.max():.2f}]"
        )

        # Import colormap utility for getting individual colors
        from utils.colormaps import get_color

        # Draw each region filled with its score color
        for pred, norm_score in zip(predictions, normalized_scores):
            # Get color from the configured color scale
            r, g, b = get_color(float(norm_score), self.color_scale)

            # Convert normalized bbox to pixel coordinates
            x1, y1, x2, y2 = pred.bbox
            px1 = int(x1 * width)
            py1 = int(y1 * height)
            px2 = int(x2 * width)
            py2 = int(y2 * height)

            # Fill region with score-based color and add border for visibility
            draw.rectangle([px1, py1, px2, py2], fill=(r, g, b, alpha))
            # Add darker border to make regions more distinct
            border_color = (max(0, r - 50), max(0, g - 50), max(0, b - 50), min(255, alpha + 50))
            draw.rectangle([px1, py1, px2, py2], outline=border_color, width=2)

        return overlay

    def _draw_region_box(
        self,
        draw: ImageDraw.Draw,
        bbox: List[float],
        width: int,
        height: int,
        color: Tuple[int, int, int, int],
        line_width: int = 2,
        label: Optional[str] = None,
    ) -> None:
        """Draw a bounding box from OCR format (0-999 or pixels)."""
        if len(bbox) < 4:
            return

        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

        # Detect and normalize coordinates
        max_coord = max(x1, y1, x2, y2)
        if max_coord <= 1.0:
            # Already normalized
            pass
        elif max_coord <= 999:
            # DeepSeek format
            x1, y1, x2, y2 = x1 / 999, y1 / 999, x2 / 999, y2 / 999
        else:
            # Assume pixel coordinates matching image size
            x1, y1, x2, y2 = x1 / width, y1 / height, x2 / width, y2 / height

        # Convert to pixel coordinates
        px1 = int(x1 * width)
        py1 = int(y1 * height)
        px2 = int(x2 * width)
        py2 = int(y2 * height)

        draw.rectangle([px1, py1, px2, py2], outline=color, width=line_width)

        if label:
            self._draw_label(draw, label, px1, py1, color)

    def _draw_normalized_box(
        self,
        draw: ImageDraw.Draw,
        bbox: NormalizedBox,
        width: int,
        height: int,
        color: Tuple[int, int, int, int],
        line_width: int = 2,
        label: Optional[str] = None,
    ) -> None:
        """Draw a normalized bounding box."""
        x1, y1, x2, y2 = bbox

        px1 = int(x1 * width)
        py1 = int(y1 * height)
        px2 = int(x2 * width)
        py2 = int(y2 * height)

        draw.rectangle([px1, py1, px2, py2], outline=color, width=line_width)

        if label:
            self._draw_label(draw, label, px1, py1 - 15, color)

    def _draw_label(
        self,
        draw: ImageDraw.Draw,
        text: str,
        x: int,
        y: int,
        color: Tuple[int, int, int, int],
    ) -> None:
        """Draw a text label with background."""
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((x, y), text, font=font)
        padding = 2

        # Draw background
        draw.rectangle(
            [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
            fill=(255, 255, 255, 200),
        )

        # Draw text
        draw.text((x, y), text, fill=(0, 0, 0, 255), font=font)

    def _draw_overlaps(
        self,
        draw: ImageDraw.Draw,
        predictions: List[RegionScore],
        ground_truth: List[NormalizedBox],
        width: int,
        height: int,
    ) -> None:
        """Highlight overlapping regions between predictions and ground truth."""
        from .utils.coordinates import compute_iou

        for pred in predictions:
            for gt in ground_truth:
                iou = compute_iou(pred.bbox, gt)
                if iou > 0.1:  # Show overlaps with IoU > 10%
                    # Compute intersection box
                    x1 = max(pred.bbox[0], gt[0])
                    y1 = max(pred.bbox[1], gt[1])
                    x2 = min(pred.bbox[2], gt[2])
                    y2 = min(pred.bbox[3], gt[3])

                    if x2 > x1 and y2 > y1:
                        px1 = int(x1 * width)
                        py1 = int(y1 * height)
                        px2 = int(x2 * width)
                        py2 = int(y2 * height)

                        # Fill with yellow
                        draw.rectangle(
                            [px1, py1, px2, py2],
                            fill=COLORS["overlap"],
                        )

    def _add_header(
        self,
        image: Image.Image,
        sample_id: str,
        query: str,
    ) -> Image.Image:
        """Add a header bar with sample info and legend."""
        header_height = 40
        width, height = image.size

        # Create new image with header
        new_image = Image.new("RGBA", (width, height + header_height), (255, 255, 255, 255))
        new_image.paste(image, (0, header_height))

        draw = ImageDraw.Draw(new_image)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Draw header text (query only, sample_id is in filename)
        if query:
            # Truncate query to fit
            max_query_len = 80
            display_query = query[:max_query_len] + ("..." if len(query) > max_query_len else "")
            draw.text((10, 10), f"Q: {display_query}", fill=(0, 0, 0, 255), font=font)

        # Draw compact legend on the right
        legend_items = [
            ("HIT", COLORS["prediction_hit"]),
            ("MISS", COLORS["prediction_miss"]),
            ("GT", COLORS["ground_truth"]),
        ]

        legend_x = width - 280
        for i, (label, color) in enumerate(legend_items):
            x = legend_x + i * 90
            draw.rectangle([x, 10, x + 15, 25], fill=color, outline=(0, 0, 0, 255))
            draw.text((x + 20, 10), label, fill=(0, 0, 0, 255), font=font)

        return new_image

    def create_comparison_grid(
        self,
        images: List[Image.Image],
        titles: List[str],
        columns: int = 3,
    ) -> Image.Image:
        """
        Create a grid of comparison images.

        Args:
            images: List of images to arrange
            titles: Titles for each image
            columns: Number of columns in grid

        Returns:
            Grid image
        """
        if not images:
            return Image.new("RGB", (100, 100), (255, 255, 255))

        # Calculate grid dimensions
        n = len(images)
        rows = (n + columns - 1) // columns

        # Get max dimensions
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)

        title_height = 30
        cell_width = max_width
        cell_height = max_height + title_height

        # Create grid image
        grid = Image.new(
            "RGB",
            (columns * cell_width, rows * cell_height),
            (255, 255, 255),
        )
        draw = ImageDraw.Draw(grid)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()

        for i, (img, title) in enumerate(zip(images, titles)):
            row = i // columns
            col = i % columns

            x = col * cell_width
            y = row * cell_height

            # Draw title
            draw.text((x + 5, y + 5), title, fill=(0, 0, 0), font=font)

            # Paste image
            img_rgb = img.convert("RGB") if img.mode != "RGB" else img
            grid.paste(img_rgb, (x, y + title_height))

        return grid


def save_debug_overlay(
    image: Union[Image.Image, np.ndarray, str],
    heatmap: Optional[np.ndarray],
    ocr_boxes: List[Dict[str, Any]],
    pred_boxes: List[RegionScore],
    gt_boxes: List[NormalizedBox],
    output_path: str,
    query: str = "",
    sample_id: str = "",
    color_scale: ColorScale = ColorScale.YLORRD,
    normalization: NormalizationStrategy = NormalizationStrategy.PERCENTILE,
) -> None:
    """
    Convenience function to save a debug overlay.

    Args:
        image: Document image (PIL Image, numpy array, or file path)
        heatmap: Patch-level similarity heatmap
        ocr_boxes: OCR region dictionaries
        pred_boxes: Predicted regions
        gt_boxes: Ground truth boxes
        output_path: Path to save the visualization
        query: Query text
        sample_id: Sample identifier
        color_scale: ColorBrewer color scale for heatmaps (default: YlOrRd)
        normalization: Normalization strategy for heatmap values (default: percentile)
    """
    # Load image if needed
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    visualizer = BenchmarkVisualizer(
        color_scale=color_scale,
        normalization=normalization,
    )
    vis = visualizer.visualize_sample(
        image=image,
        heatmap=heatmap,
        ocr_regions=ocr_boxes,
        predictions=pred_boxes,
        ground_truth=gt_boxes,
        sample_id=sample_id,
        query=query,
    )

    vis.convert("RGB").save(output_path)
    logger.info(f"Saved debug overlay to {output_path}")
