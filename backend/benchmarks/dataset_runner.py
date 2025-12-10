from __future__ import annotations

import json
import logging
import sys
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import requests
import tiktoken
from PIL import Image

# Ensure backend root is on the import path so `config` and clients resolve.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from clients.colpali import ColPaliClient
from clients.ocr.processor import OcrProcessor
from benchmarks.metrics import (
    Box,
    SampleMetrics,
    compute_iou,
    evaluate_boxes,
    summarize_samples,
)

# Type alias for embedding clients (ColPaliClient or TomoroColQwenClient)
# Both must implement generate_interpretability_maps(query, image) -> dict
EmbeddingClient = Any

logger = logging.getLogger(__name__)


@dataclass
class BBoxDocVQASample:
    """Single BBox-DocVQA sample."""

    sample_id: int  # 0-indexed line number in the JSONL file
    question: str
    answer: str
    image_path: Path
    bboxes: List[Box]
    doc_name: str
    category: str
    evidence_page: List[int] = field(default_factory=list)


@dataclass
class RegionScore:
    bbox: Box
    score: float
    label: str | None = None
    content: str | None = None  # Text content for token counting


@dataclass
class TokenStats:
    """Token usage statistics for a sample."""

    tokens_selected: int = 0  # Tokens in selected regions
    tokens_all_ocr: int = 0  # Tokens in all OCR regions
    tokens_full_image: int = 0  # Estimated tokens for full image (VLM approach)
    image_regions_selected: int = 0  # Number of image regions selected
    image_regions_all: int = 0  # Total image regions detected


@dataclass
class SampleResult:
    sample: BBoxDocVQASample
    metrics: SampleMetrics
    predicted_boxes: List[Box]
    region_scores: List[RegionScore]
    elapsed_ms: float
    detection_metrics: Optional[SampleMetrics] = None
    ocr_boxes: List[Box] = field(default_factory=list)
    patch_scores: Optional[np.ndarray] = None
    token_stats: Optional[TokenStats] = None
    failed: bool = False  # True if sample processing failed (excludes from aggregates)
    error_message: Optional[str] = None  # Error details if failed


# Lazy-loaded tiktoken encoder
_tiktoken_encoder: Optional[tiktoken.Encoding] = None


def _get_encoder() -> tiktoken.Encoding:
    """Get or create tiktoken encoder (cl100k_base for GPT-4/Claude compatibility)."""
    global _tiktoken_encoder
    if _tiktoken_encoder is None:
        _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
    return _tiktoken_encoder


def _count_text_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    if not text:
        return 0
    return len(_get_encoder().encode(text))


def _estimate_image_tokens(width: int, height: int) -> int:
    """Estimate tokens for an image based on dimensions.

    Uses Claude's approximate formula: images are resized to fit within
    1568x1568, then token count is roughly (width * height) / 750.
    """
    # Claude resizes to fit within 1568x1568 maintaining aspect ratio
    max_dim = 1568
    if width > max_dim or height > max_dim:
        scale = min(max_dim / width, max_dim / height)
        width = int(width * scale)
        height = int(height * scale)

    # Approximate token count
    return max(1, (width * height) // 750)


def _flatten_bboxes(raw_bbox: Any) -> List[Box]:
    """Flatten nested bbox arrays from the dataset into a list of (x1,y1,x2,y2)."""
    boxes: List[Box] = []
    if not raw_bbox:
        return boxes

    def _maybe_append(box_like: Sequence[Any]) -> None:
        if len(box_like) >= 4:
            try:
                x1, y1, x2, y2 = [float(v) for v in box_like[:4]]
                boxes.append((x1, y1, x2, y2))
            except (TypeError, ValueError) as e:
                logger.warning("Failed to parse bbox %r: %s", box_like[:4], e)
                return

    if isinstance(raw_bbox, (list, tuple)):
        for entry in raw_bbox:
            if (
                isinstance(entry, (list, tuple))
                and entry
                and isinstance(entry[0], (list, tuple))
            ):
                for inner in entry:
                    _maybe_append(inner)
            else:
                _maybe_append(entry)

    return boxes


def _discover_dataset_root(explicit_root: Optional[Path]) -> Path:
    """Resolve dataset root, preferring an explicit path and falling back to cache."""
    if explicit_root:
        json_path = explicit_root / "BBox_DocVQA_Bench.jsonl"
        if not json_path.exists():
            raise FileNotFoundError(f"Dataset file not found at {json_path}")
        return explicit_root

    cache_root = Path(__file__).resolve().parent / ".eval_cache"
    dataset_root = cache_root / "datasets--Yuwh07--BBox_DocVQA_Bench" / "snapshots"
    if not dataset_root.exists():
        raise FileNotFoundError(
            "BBox-DocVQA cache not found. Expected under benchmarks/.eval_cache "
            "or pass --dataset-root explicitly."
        )

    snapshots = sorted(
        dataset_root.iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for snap in snapshots:
        if (snap / "BBox_DocVQA_Bench.jsonl").exists():
            return snap

    raise FileNotFoundError("No snapshot with BBox_DocVQA_Bench.jsonl found.")


def load_samples(
    dataset_root: Optional[Path],
    limit: Optional[int] = None,
    filter_docs: Optional[List[str]] = None,
    filter_samples: Optional[List[int]] = None,
) -> List[BBoxDocVQASample]:
    """Load BBox-DocVQA samples from jsonl.

    Args:
        dataset_root: Path to dataset directory
        limit: Maximum number of samples to load
        filter_docs: If provided, only load samples from these doc names
        filter_samples: If provided, only load samples with these IDs (0-indexed line numbers)
    """
    root = _discover_dataset_root(dataset_root)
    json_path = root / "BBox_DocVQA_Bench.jsonl"
    samples: List[BBoxDocVQASample] = []
    skipped_missing_image = 0
    skipped_no_image_ref = 0
    empty_question_count = 0
    filter_doc_set = set(filter_docs) if filter_docs else None
    filter_sample_set = set(filter_samples) if filter_samples else None

    with json_path.open("r", encoding="utf-8") as fh:
        for sample_id, line in enumerate(fh):
            # Apply sample ID filter first (most specific)
            if filter_sample_set is not None and sample_id not in filter_sample_set:
                continue

            record = json.loads(line)

            # Apply doc filter if specified
            doc_name = record.get("doc_name", "")
            if filter_doc_set is not None and doc_name not in filter_doc_set:
                continue

            image_rel = record.get("images", []) or record.get("image_paths", [])
            if not image_rel:
                skipped_no_image_ref += 1
                continue
            image_path = root / image_rel[0]
            if not image_path.exists():
                logger.warning("Image path missing: %s", image_path)
                skipped_missing_image += 1
                continue

            question = record.get("question") or record.get("query") or ""
            if not question.strip():
                empty_question_count += 1
                logger.warning(
                    "Empty question for doc '%s' - may produce degenerate results",
                    doc_name or "unknown",
                )

            boxes = _flatten_bboxes(record.get("bbox"))
            samples.append(
                BBoxDocVQASample(
                    sample_id=sample_id,
                    question=question,
                    answer=record.get("answer") or "",
                    image_path=image_path,
                    bboxes=boxes,
                    doc_name=doc_name,
                    category=record.get("category", ""),
                    evidence_page=record.get("evidence_page") or [],
                )
            )
            if limit is not None and len(samples) >= limit:
                break

    # Log summary of skipped samples
    if skipped_missing_image > 0 or skipped_no_image_ref > 0:
        logger.warning(
            "Skipped %d sample(s): %d missing images, %d without image reference",
            skipped_missing_image + skipped_no_image_ref,
            skipped_missing_image,
            skipped_no_image_ref,
        )
    if empty_question_count > 0:
        logger.warning(
            "%d sample(s) have empty questions which may affect ColPali scoring",
            empty_question_count,
        )
    if filter_sample_set:
        logger.info(
            "Filtered to %d sample(s) from %d sample ID(s)",
            len(samples),
            len(filter_sample_set),
        )
    elif filter_doc_set:
        logger.info(
            "Filtered to %d sample(s) from %d doc(s)", len(samples), len(filter_doc_set)
        )

    return samples


def _stack_patch_scores(
    similarity_maps: Sequence[Dict[str, Any]],
    n_patches_x: int,
    n_patches_y: int,
    aggregation: str = "max",
) -> np.ndarray:
    """Aggregate token similarity maps into a single patch score heatmap.

    Args:
        similarity_maps: List of per-token similarity maps from ColPali
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        aggregation: Aggregation method - "max" (MaxSim), "mean", or "sum"

    Returns:
        Aggregated 2D heatmap of shape (n_patches_y, n_patches_x)
    """
    token_maps = []
    for token_map in similarity_maps:
        sim_map = token_map.get("similarity_map")
        if sim_map is None:
            continue
        arr = np.asarray(sim_map, dtype=np.float32)
        if arr.ndim != 2:
            raise ValueError(f"Similarity map must be 2D, got shape {arr.shape}")
        # Normalize orientation: we want [patch_y, patch_x]
        if arr.shape == (n_patches_x, n_patches_y):
            arr = arr.T
        elif arr.shape != (n_patches_y, n_patches_x):
            raise ValueError(
                f"Unexpected similarity map shape {arr.shape}; expected "
                f"({n_patches_y}, {n_patches_x}) or ({n_patches_x}, {n_patches_y})"
            )
        token_maps.append(arr)

    if not token_maps:
        raise ValueError("No valid similarity maps found in interpretability output.")

    stacked = np.stack(token_maps, axis=0)

    if aggregation == "mean":
        return np.mean(stacked, axis=0)
    elif aggregation == "sum":
        # Sum all token maps - areas with multiple token matches get boosted
        return np.sum(stacked, axis=0)
    else:  # default to max (MaxSim)
        return np.max(stacked, axis=0)


def _score_regions_iou_weighted(
    patch_scores: np.ndarray,
    regions: Sequence[Dict[str, Any]],
    image_width: int,
    image_height: int,
    n_patches_x: int,
    n_patches_y: int,
    min_overlap: float = 0.0,
    scoring_method: str = "weighted_avg",
) -> List[RegionScore]:
    """Compute region scores based on patch heatmap.

    Args:
        patch_scores: 2D heatmap of shape (n_patches_y, n_patches_x)
        regions: List of OCR regions with bbox coordinates
        image_width: Original image width
        image_height: Original image height
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension
        min_overlap: Minimum IoU overlap with a patch to count
        scoring_method: "weighted_avg" (IoU-weighted average) or "max" (max patch score)

    Returns:
        List of RegionScore sorted by score descending
    """
    patch_w = image_width / n_patches_x
    patch_h = image_height / n_patches_y

    patches: List[Tuple[Box, float]] = []
    for y in range(n_patches_y):
        for x in range(n_patches_x):
            bbox = (
                x * patch_w,
                y * patch_h,
                (x + 1) * patch_w,
                (y + 1) * patch_h,
            )
            patches.append((bbox, float(patch_scores[y, x])))

    scored: List[RegionScore] = []
    for region in regions:
        bbox = region.get("bbox")
        if not bbox or len(bbox) < 4:
            continue
        rx1, ry1, rx2, ry2 = [float(v) for v in bbox[:4]]
        region_box: Box = (rx1, ry1, rx2, ry2)

        if scoring_method == "max":
            # Use the maximum patch score within the region
            max_score = 0.0
            for patch_box, patch_score in patches:
                iou = compute_iou(region_box, patch_box)
                if iou > min_overlap:
                    max_score = max(max_score, patch_score)
            region_score = max_score
        else:
            # Default: IoU-weighted average
            weight_sum = 0.0
            score_sum = 0.0
            for patch_box, patch_score in patches:
                iou = compute_iou(region_box, patch_box)
                if iou <= min_overlap:
                    continue
                weight_sum += iou
                score_sum += iou * patch_score
            if weight_sum == 0.0:
                region_score = 0.0
            else:
                region_score = score_sum / (weight_sum + 1e-8)

        scored.append(
            RegionScore(
                bbox=region_box,
                score=region_score,
                label=region.get("label"),
                content=region.get("content"),
            )
        )
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored


def _threshold_regions(
    region_scores: Sequence[RegionScore],
    method: str,
    *,
    percentile: float = 80.0,
    top_k: Optional[int] = None,
) -> List[RegionScore]:
    """Select regions based on a thresholding strategy.

    Methods:
        - adaptive: threshold = mean + std (selects outliers)
        - percentile: threshold = given percentile of scores
        - max: threshold = max score (selects only the top scorer)
        - none: no threshold, return all regions
    """
    if not region_scores:
        return []

    # "none" method skips thresholding entirely
    if method == "none":
        selected = list(region_scores)  # already sorted by score desc
        if top_k is not None and top_k > 0:
            selected = selected[:top_k]
        return selected

    scores = np.array([r.score for r in region_scores], dtype=np.float32)

    if method == "adaptive":
        threshold = float(scores.mean() + scores.std())
    elif method == "percentile":
        pct = max(0.0, min(100.0, percentile))
        threshold = float(np.percentile(scores, pct))
    elif method == "max":
        threshold = float(scores.max())
    else:
        raise ValueError(f"Unknown threshold method: {method}")

    selected = [r for r in region_scores if r.score >= threshold]

    if top_k is not None and top_k > 0:
        selected = selected[:top_k]

    return selected


def _to_regions_from_ocr(ocr_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract region list from DeepSeek OCR response."""
    if not ocr_payload:
        return []
    if "regions" in ocr_payload and isinstance(ocr_payload["regions"], list):
        return ocr_payload["regions"]
    if "bounding_boxes" in ocr_payload and isinstance(
        ocr_payload["bounding_boxes"], list
    ):
        # Extract content from raw text using grounding markers
        raw_text = ocr_payload.get("raw") or ""
        content_map = OcrProcessor._extract_region_content(raw_text)

        boxes = []
        for bbox in ocr_payload["bounding_boxes"]:
            if not isinstance(bbox, dict):
                continue
            label = bbox.get("label") or "unknown"

            # Get content for this label (consume from list in order)
            content = None
            if label in content_map and content_map[label]:
                content = content_map[label].pop(0)

            boxes.append(
                {
                    "bbox": [
                        bbox.get("x1", 0),
                        bbox.get("y1", 0),
                        bbox.get("x2", 0),
                        bbox.get("y2", 0),
                    ],
                    "label": label,
                    "content": content,
                }
            )
        return boxes
    return []


def _compute_region_tokens(region: Dict[str, Any]) -> int:
    """Compute tokens for a single region (text or image)."""
    label = (region.get("label") or "").lower()

    # Image regions: estimate based on bbox size
    if label in ("image", "figure", "chart", "diagram"):
        bbox = region.get("bbox", [0, 0, 0, 0])
        if len(bbox) >= 4:
            width = abs(bbox[2] - bbox[0])
            height = abs(bbox[3] - bbox[1])
            return _estimate_image_tokens(width, height)
        return 100  # Default estimate for images

    # Text regions: count tokens in content
    content = region.get("content") or ""
    return _count_text_tokens(content)


def _compute_token_stats(
    all_regions: Sequence[Dict[str, Any]],
    selected_regions: Sequence[RegionScore],
    image_width: int,
    image_height: int,
) -> TokenStats:
    """Compute token statistics for a sample."""
    # Tokens for all OCR regions
    tokens_all = 0
    image_regions_all = 0
    for region in all_regions:
        tokens_all += _compute_region_tokens(region)
        label = (region.get("label") or "").lower()
        if label in ("image", "figure", "chart", "diagram"):
            image_regions_all += 1

    # Tokens for selected regions
    tokens_selected = 0
    image_regions_selected = 0
    for rs in selected_regions:
        label = (rs.label or "").lower()
        if label in ("image", "figure", "chart", "diagram"):
            # Image region: estimate from bbox
            width = abs(rs.bbox[2] - rs.bbox[0])
            height = abs(rs.bbox[3] - rs.bbox[1])
            tokens_selected += _estimate_image_tokens(int(width), int(height))
            image_regions_selected += 1
        else:
            # Text region: count tokens in content
            tokens_selected += _count_text_tokens(rs.content or "")

    # Full image tokens (VLM approach)
    tokens_full_image = _estimate_image_tokens(image_width, image_height)

    return TokenStats(
        tokens_selected=tokens_selected,
        tokens_all_ocr=tokens_all,
        tokens_full_image=tokens_full_image,
        image_regions_selected=image_regions_selected,
        image_regions_all=image_regions_all,
    )


def _run_deepseek_ocr(
    image: Image.Image,
    *,
    base_url: str,
    timeout: int,
    mode: str,
    task: str,
) -> Dict[str, Any]:
    """Call DeepSeek OCR service directly."""
    import io

    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    buf.seek(0)

    files = {"image": ("page.png", buf, "image/png")}
    data = {
        "mode": mode,
        "task": task,
        "include_grounding": "true",
        "include_images": "true",
    }
    resp = requests.post(
        f"{base_url.rstrip('/')}/api/ocr",
        files=files,
        data=data,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


@dataclass
class BenchmarkConfig:
    dataset_root: Optional[Path] = None
    sample_limit: Optional[int] = 25
    filter_docs: Optional[List[str]] = None  # Filter to specific doc names
    filter_samples: Optional[List[int]] = (
        None  # Filter to specific sample IDs (0-indexed)
    )
    threshold_method: str = "adaptive"
    percentile: float = 80.0
    top_k: Optional[int] = None
    min_patch_overlap: float = 0.0
    token_aggregation: str = "max"  # "max" (MaxSim) or "mean"
    region_scoring: str = "weighted_avg"  # "weighted_avg" or "max"
    hit_iou_threshold: float = 0.5  # IoU threshold for counting as a "hit"
    deepseek_url: Optional[str] = None
    deepseek_mode: Optional[str] = None
    deepseek_task: Optional[str] = None
    deepseek_timeout: Optional[int] = None
    output_dir: Path = Path("benchmarks") / "runs"
    visualize: bool = False
    visualize_limit: Optional[int] = 10
    visualize_heatmap: bool = True
    # Embedding model: "colmodernvbert" (remote), "colqwen3-4b", or "colqwen3-8b" (local)
    embedding_model: str = "colmodernvbert"


class BBoxDocVQARunner:
    """Benchmark runner for BBox-DocVQA using ColPali/Tomoro + DeepSeek OCR."""

    def __init__(
        self,
        bench_config: BenchmarkConfig,
        *,
        embedding_client: Optional[EmbeddingClient] = None,
    ):
        self.config = bench_config

        # Initialize embedding client based on config or provided client
        if embedding_client is not None:
            self.embedding_client = embedding_client
        elif bench_config.embedding_model in ("colqwen3-4b", "colqwen3-8b"):
            from benchmarks.local_client import TomoroColQwenClient

            self.embedding_client = TomoroColQwenClient(
                model_variant=bench_config.embedding_model
            )
            logger.info(
                "Using local %s model for embeddings", bench_config.embedding_model
            )
        else:
            # colmodernvbert uses remote ColPali service (always localhost from WSL)
            colpali_url = "http://localhost:7000"
            self.embedding_client = ColPaliClient(base_url=colpali_url)
            logger.info(
                "Using ColPali service for embeddings (%s)",
                bench_config.embedding_model,
            )

        # Configure DeepSeek OCR URL (always localhost from WSL)
        default_deepseek = "http://localhost:8200"
        self.deepseek_url = (
            bench_config.deepseek_url
            or getattr(config, "DEEPSEEK_OCR_URL", None)
            or default_deepseek
        )

        self.deepseek_timeout = int(
            bench_config.deepseek_timeout
            or getattr(config, "DEEPSEEK_OCR_API_TIMEOUT", 600)
        )
        self.deepseek_mode = bench_config.deepseek_mode or getattr(
            config, "DEEPSEEK_OCR_MODE", "Gundam"
        )
        self.deepseek_task = bench_config.deepseek_task or getattr(
            config, "DEEPSEEK_OCR_TASK", "markdown"
        )

    def _predict_boxes(
        self,
        sample: BBoxDocVQASample,
        *,
        return_ocr_boxes: bool = False,
    ) -> Dict[str, Any]:
        """Run OCR + interpretability scoring and return boxes and metadata."""
        image = Image.open(sample.image_path).convert("RGB")

        ocr_payload = _run_deepseek_ocr(
            image,
            base_url=self.deepseek_url,
            timeout=self.deepseek_timeout,
            mode=self.deepseek_mode,
            task=self.deepseek_task,
        )
        regions = _to_regions_from_ocr(ocr_payload)
        detection_boxes: List[Box] = []
        for reg in regions:
            bbox = reg.get("bbox")
            if bbox and len(bbox) >= 4:
                detection_boxes.append(
                    (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                )
        detection_metrics = evaluate_boxes(detection_boxes, sample.bboxes)
        ocr_boxes = detection_boxes

        interp = self.embedding_client.generate_interpretability_maps(
            sample.question, image
        )
        similarity_maps = interp.get("similarity_maps", [])
        n_patches_x = int(interp.get("n_patches_x", 0))
        n_patches_y = int(interp.get("n_patches_y", 0))

        if not similarity_maps or not n_patches_x or not n_patches_y:
            raise RuntimeError("Invalid interpretability output from ColPali.")

        patch_scores = _stack_patch_scores(
            similarity_maps, n_patches_x, n_patches_y, self.config.token_aggregation
        )
        # Use ORIGINAL image dimensions for region scoring, since OCR bboxes
        # are in original image coordinates. The ColPali image dimensions
        # may differ if the image was resized for processing.
        region_scores = _score_regions_iou_weighted(
            patch_scores,
            regions,
            image_width=image.width,
            image_height=image.height,
            n_patches_x=n_patches_x,
            n_patches_y=n_patches_y,
            min_overlap=self.config.min_patch_overlap,
            scoring_method=self.config.region_scoring,
        )
        selected = _threshold_regions(
            region_scores,
            method=self.config.threshold_method,
            percentile=self.config.percentile,
            top_k=self.config.top_k,
        )
        predicted_boxes = [r.bbox for r in selected]

        # Compute token statistics
        token_stats = _compute_token_stats(
            all_regions=regions,
            selected_regions=selected,
            image_width=image.width,
            image_height=image.height,
        )

        return {
            "region_scores": region_scores,
            "predicted_boxes": predicted_boxes,
            "detection_metrics": detection_metrics,
            "ocr_boxes": ocr_boxes,
            "patch_scores": patch_scores,
            "token_stats": token_stats,
        }

    def _render_visualization(
        self,
        *,
        sample: BBoxDocVQASample,
        ocr_boxes: List[Box],
        pred_boxes: List[Box],
        run_dir: Path,
        patch_scores: Optional[np.ndarray],
    ) -> None:
        """Draw GT, OCR, and predicted boxes on the image."""
        from PIL import ImageDraw, ImageFont

        image = Image.open(sample.image_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")

        def _draw(
            boxes: List[Box], color: Tuple[int, int, int, int], width: int
        ) -> None:
            for b in boxes:
                draw.rectangle(b, outline=color, width=width)

        # Optional heatmap overlay from patch_scores
        if self.config.visualize_heatmap and patch_scores is not None:
            heat = np.clip(patch_scores, 0, None)
            if heat.max() > 0:
                heat = heat / (heat.max() + 1e-8)
            heat_rgba = np.zeros((heat.shape[0], heat.shape[1], 4), dtype=np.uint8)
            heat_rgba[..., 0] = (heat * 255).astype(np.uint8)  # red channel
            heat_rgba[..., 3] = (heat * 180).astype(np.uint8)  # alpha
            heat_img = Image.fromarray(heat_rgba, mode="RGBA").resize(
                image.size, resample=Image.BILINEAR
            )
            image = Image.alpha_composite(image.convert("RGBA"), heat_img).convert(
                "RGB"
            )
            draw = ImageDraw.Draw(image, "RGBA")

        # Colors: GT green, OCR blue, Pred magenta
        _draw(sample.bboxes, (0, 255, 0, 255), 4)
        _draw(ocr_boxes, (0, 102, 255, 180), 2)
        _draw(pred_boxes, (255, 0, 255, 255), 4)

        legend: List[str] = [
            "GT: green  |  OCR: blue  |  Pred: magenta",
            "",
            "Question:",
        ]
        for line in textwrap.wrap(sample.question, width=60):
            legend.append(f"  {line}")
        legend.append("")
        legend.append("Answer:")
        for line in textwrap.wrap(sample.answer, width=60):
            legend.append(f"  {line}")

        # Use a larger, more readable font size
        font_size = 32
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("segoeui.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()
                    font_size = 20

        # Measure text sizes per line to fit the backdrop
        pad = 16
        line_sizes: List[Tuple[int, int]] = []
        max_width = 0
        for line in legend:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
            except Exception:
                width = len(line) * (font_size // 2)
                height = font_size + 2
            max_width = max(max_width, width)
            line_sizes.append((width, height))

        text_block_height = sum(h for _, h in line_sizes)
        margin = 12
        backdrop = [
            margin,
            margin,
            margin + max_width + pad * 2,
            margin + text_block_height + pad * 2,
        ]
        draw.rectangle(backdrop, fill=(0, 0, 0, 200))

        y = margin + pad
        for line, (_, height) in zip(legend, line_sizes):
            draw.text((margin + pad, y), line, fill=(255, 255, 255, 255), font=font)
            y += height

        vis_dir = run_dir / "visualizations"
        vis_dir.mkdir(parents=True, exist_ok=True)
        image.save(vis_dir / f"sample_{sample.sample_id:05d}.png")

    def _write_progress_report(
        self,
        run_dir: Path,
        results: List[SampleResult],
        total_samples: int,
    ) -> None:
        """Write/update the markdown progress report."""
        report_path = run_dir / "progress.md"

        # Calculate stats (exclude failed samples from success metrics)
        total_processed = len(results)
        successful_results = [r for r in results if not r.failed]
        failed_count = total_processed - len(successful_results)
        hit_threshold = self.config.hit_iou_threshold
        hits = sum(1 for r in successful_results if r.metrics.mean_iou >= hit_threshold)
        misses = len(successful_results) - hits
        success_ratio = hits / len(successful_results) if successful_results else 0.0

        # Build filter description if applicable
        filter_desc = "None"
        if self.config.filter_samples:
            filter_desc = f"Sample IDs: {self.config.filter_samples}"
        elif self.config.filter_docs:
            filter_desc = f"Docs: {self.config.filter_docs}"

        lines = [
            "# BBox-DocVQA Benchmark Progress",
            "",
            "## Configuration",
            "",
            "### Model & Environment",
            "",
            "| Setting | Value |",
            "|---------|-------|",
            f"| Embedding Model | `{self.config.embedding_model}` |",
            f"| DeepSeek Mode | `{self.deepseek_mode}` |",
            f"| DeepSeek Task | `{self.deepseek_task}` |",
            "",
            "### Scoring & Thresholding",
            "",
            "| Setting | Value |",
            "|---------|-------|",
            f"| Threshold Method | `{self.config.threshold_method}` |",
            f"| Token Aggregation | `{self.config.token_aggregation}` |",
            f"| Region Scoring | `{self.config.region_scoring}` |",
            f"| Percentile | `{self.config.percentile}` |",
            f"| Top-K | `{self.config.top_k or 'None'}` |",
            f"| Min Patch Overlap | `{self.config.min_patch_overlap}` |",
            f"| Hit IoU Threshold | `{hit_threshold}` |",
            "",
            "### Dataset",
            "",
            "| Setting | Value |",
            "|---------|-------|",
            f"| Sample Limit | `{self.config.sample_limit or 'None'}` |",
            f"| Filter | `{filter_desc}` |",
            "",
            "## Progress",
            "",
            f"**Processed:** {total_processed}/{total_samples}"
            + (f" ({failed_count} failed)" if failed_count > 0 else ""),
            "",
            f"**Success Ratio (IoU ≥ {hit_threshold}):** {hits}/{len(successful_results)} ({success_ratio:.1%})",
            "",
            "## Results",
            "",
            "| ID | Document | Category | OCR'd | Sel | IoU | Tok Sel | Tok OCR | Tok Img | Save OCR | Save Img | Result |",
            "|----|----------|----------|-------|-----|-----|---------|---------|---------|----------|----------|--------|",
        ]

        for r in results:
            if r.failed:
                # Show failed samples with error indicator
                lines.append(
                    f"| {r.sample.sample_id} | {r.sample.doc_name} | {r.sample.category} | "
                    f"- | - | - | - | - | - | - | - | ⚠️ Failed |"
                )
                continue

            ocr_count = len(r.ocr_boxes) if r.ocr_boxes else 0
            selected_count = len(r.predicted_boxes)
            iou = r.metrics.mean_iou
            result = "✅ Hit" if iou >= hit_threshold else "❌ Miss"

            # Token stats
            if r.token_stats:
                tok_sel = r.token_stats.tokens_selected
                tok_ocr = r.token_stats.tokens_all_ocr
                tok_img = r.token_stats.tokens_full_image
                save_ocr = (
                    f"{(1 - tok_sel / tok_ocr) * 100:.0f}%" if tok_ocr > 0 else "-"
                )
                save_img = (
                    f"{(1 - tok_sel / tok_img) * 100:.0f}%" if tok_img > 0 else "-"
                )
            else:
                tok_sel = tok_ocr = tok_img = 0
                save_ocr = save_img = "-"

            lines.append(
                f"| {r.sample.sample_id} | {r.sample.doc_name} | {r.sample.category} | "
                f"{ocr_count} | {selected_count} | {iou:.3f} | "
                f"{tok_sel:,} | {tok_ocr:,} | {tok_img:,} | {save_ocr} | {save_img} | {result} |"
            )

        # Add summary section (only for successful samples)
        if successful_results:
            mean_iou = sum(r.metrics.mean_iou for r in successful_results) / len(
                successful_results
            )

            # Token statistics (only from successful samples)
            total_tokens_selected = sum(
                r.token_stats.tokens_selected
                for r in successful_results
                if r.token_stats
            )
            total_tokens_all_ocr = sum(
                r.token_stats.tokens_all_ocr
                for r in successful_results
                if r.token_stats
            )
            total_tokens_full_image = sum(
                r.token_stats.tokens_full_image
                for r in successful_results
                if r.token_stats
            )
            savings_vs_ocr = (
                f"{(1 - total_tokens_selected / total_tokens_all_ocr) * 100:.1f}%"
                if total_tokens_all_ocr > 0
                else "N/A"
            )
            savings_vs_image = (
                f"{(1 - total_tokens_selected / total_tokens_full_image) * 100:.1f}%"
                if total_tokens_full_image > 0
                else "N/A"
            )

            summary_lines = [
                "",
                "## Summary",
                "",
                f"- **Mean IoU:** {mean_iou:.3f}",
                f"- **Hits (IoU ≥ {hit_threshold}):** {hits}",
                f"- **Misses:** {misses}",
                f"- **Success Rate:** {success_ratio:.1%}",
            ]
            if failed_count > 0:
                summary_lines.append(f"- **Failed:** {failed_count}")
            summary_lines.extend(
                [
                    "",
                    f"**Token Totals:** Selected {total_tokens_selected:,} | "
                    f"All OCR {total_tokens_all_ocr:,} | Full Image {total_tokens_full_image:,}",
                    "",
                    f"**Savings:** {savings_vs_ocr} vs All OCR | {savings_vs_image} vs Full Image",
                ]
            )
            lines.extend(summary_lines)

        lines.append("")
        report_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_summary_json(
        self,
        run_dir: Path,
        results: List[SampleResult],
    ) -> Path:
        """Write/update the summary.json file incrementally."""
        # Exclude failed samples from aggregate metrics
        successful_results = [r for r in results if not r.failed]
        failed_count = len(results) - len(successful_results)

        summary = summarize_samples(res.metrics for res in successful_results)
        detection_summary = summarize_samples(
            res.detection_metrics for res in successful_results if res.detection_metrics
        )

        # Aggregate token statistics (only from successful samples)
        total_tokens_selected = sum(
            r.token_stats.tokens_selected for r in successful_results if r.token_stats
        )
        total_tokens_all_ocr = sum(
            r.token_stats.tokens_all_ocr for r in successful_results if r.token_stats
        )
        total_tokens_full_image = sum(
            r.token_stats.tokens_full_image for r in successful_results if r.token_stats
        )

        token_summary = {
            "total_tokens_selected": total_tokens_selected,
            "total_tokens_all_ocr": total_tokens_all_ocr,
            "total_tokens_full_image": total_tokens_full_image,
            "savings_vs_all_ocr": (
                f"{(1 - total_tokens_selected / total_tokens_all_ocr) * 100:.1f}%"
                if total_tokens_all_ocr > 0
                else "N/A"
            ),
            "savings_vs_full_image": (
                f"{(1 - total_tokens_selected / total_tokens_full_image) * 100:.1f}%"
                if total_tokens_full_image > 0
                else "N/A"
            ),
        }

        # Build config dict for reproducibility
        config_dict = {
            "embedding_model": self.config.embedding_model,
            "deepseek_mode": self.deepseek_mode,
            "deepseek_task": self.deepseek_task,
            "deepseek_url": self.deepseek_url,
            "threshold_method": self.config.threshold_method,
            "token_aggregation": self.config.token_aggregation,
            "region_scoring": self.config.region_scoring,
            "percentile": self.config.percentile,
            "top_k": self.config.top_k,
            "min_patch_overlap": self.config.min_patch_overlap,
            "hit_iou_threshold": self.config.hit_iou_threshold,
            "sample_limit": self.config.sample_limit,
            "filter_docs": self.config.filter_docs,
            "filter_samples": self.config.filter_samples,
        }

        summary_path = run_dir / "summary.json"
        summary_payload = {
            "config": config_dict,
            "summary": summary,
            "detection_summary": detection_summary,
            "token_summary": token_summary,
            "failed_count": failed_count,
            "sample_results": [
                {
                    "sample_id": r.sample.sample_id,
                    "question": r.sample.question,
                    "doc_name": r.sample.doc_name,
                    "category": r.sample.category,
                    "gt_bboxes": r.sample.bboxes,
                    "pred_bboxes": r.predicted_boxes,
                    "mean_iou": r.metrics.mean_iou,
                    "iou_at_0_5": r.metrics.iou_at_0_5,
                    "detection_mean_iou": (
                        r.detection_metrics.mean_iou if r.detection_metrics else None
                    ),
                    "detection_iou_at_0_5": (
                        r.detection_metrics.iou_at_0_5 if r.detection_metrics else None
                    ),
                    "elapsed_ms": r.elapsed_ms,
                    "tokens_selected": (
                        r.token_stats.tokens_selected if r.token_stats else None
                    ),
                    "tokens_all_ocr": (
                        r.token_stats.tokens_all_ocr if r.token_stats else None
                    ),
                    "tokens_full_image": (
                        r.token_stats.tokens_full_image if r.token_stats else None
                    ),
                    "failed": r.failed,
                    "error_message": r.error_message,
                }
                for r in results
            ],
        }
        summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
        return summary_path

    def run(self) -> Tuple[List[SampleResult], dict[str, Any], Path]:
        """Execute the benchmark and return per-sample and aggregate metrics."""
        samples = load_samples(
            dataset_root=self.config.dataset_root,
            limit=self.config.sample_limit,
            filter_docs=self.config.filter_docs,
            filter_samples=self.config.filter_samples,
        )
        if not samples:
            raise RuntimeError("No samples loaded for BBox-DocVQA benchmark.")

        run_dir = (
            Path(self.config.output_dir)
            / f"bbox_docvqa_benchmark_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        run_dir.mkdir(parents=True, exist_ok=True)

        results: List[SampleResult] = []
        visualized = 0
        for idx, sample in enumerate(samples, start=1):
            start = time.perf_counter()
            try:
                pred_result = self._predict_boxes(sample, return_ocr_boxes=True)
                region_scores = pred_result["region_scores"]
                predicted_boxes = pred_result["predicted_boxes"]
                detection_metrics = pred_result["detection_metrics"]
                ocr_boxes = pred_result["ocr_boxes"]
                patch_scores = pred_result["patch_scores"]
                token_stats = pred_result["token_stats"]

                metrics = evaluate_boxes(predicted_boxes, sample.bboxes)
                elapsed_ms = (time.perf_counter() - start) * 1000
                results.append(
                    SampleResult(
                        sample=sample,
                        metrics=metrics,
                        predicted_boxes=predicted_boxes,
                        region_scores=region_scores,
                        elapsed_ms=elapsed_ms,
                        detection_metrics=detection_metrics,
                        ocr_boxes=ocr_boxes,
                        patch_scores=patch_scores,
                        token_stats=token_stats,
                    )
                )
                if self.config.visualize and (
                    self.config.visualize_limit is None
                    or visualized < self.config.visualize_limit
                ):
                    self._render_visualization(
                        sample=sample,
                        ocr_boxes=ocr_boxes,
                        pred_boxes=predicted_boxes,
                        run_dir=run_dir,
                        patch_scores=patch_scores,
                    )
                    visualized += 1
                logger.info(
                    "Processed sample %d/%d (mean_iou=%.3f, preds=%d)",
                    idx,
                    len(samples),
                    metrics.mean_iou,
                    len(predicted_boxes),
                )
                # Update progress report and summary after each successful sample
                self._write_progress_report(run_dir, results, len(samples))
                self._write_summary_json(run_dir, results)
            except Exception as exc:  # pragma: no cover - benchmark robustness
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.exception("Failed sample %d: %s", idx, exc)
                results.append(
                    SampleResult(
                        sample=sample,
                        metrics=SampleMetrics(mean_iou=0.0, max_ious=[]),
                        predicted_boxes=[],
                        region_scores=[],
                        elapsed_ms=elapsed_ms,
                        detection_metrics=None,
                        failed=True,
                        error_message=str(exc),
                    )
                )
                # Update progress report and summary even for failed samples
                self._write_progress_report(run_dir, results, len(samples))
                self._write_summary_json(run_dir, results)

        # Final summary write (already written incrementally, but ensure final state)
        summary_path = self._write_summary_json(run_dir, results)

        # Compute summary for return value and logging (exclude failed samples)
        successful_results = [r for r in results if not r.failed]
        failed_count = len(results) - len(successful_results)
        summary = summarize_samples(res.metrics for res in successful_results)
        detection_summary = summarize_samples(
            res.detection_metrics for res in successful_results if res.detection_metrics
        )
        summary["detection_summary"] = detection_summary
        summary["failed_count"] = failed_count

        if failed_count > 0:
            logger.warning(
                "%d sample(s) failed and were excluded from aggregate metrics",
                failed_count,
            )

        # Log token summary (only from successful samples)
        total_tokens_selected = sum(
            r.token_stats.tokens_selected for r in successful_results if r.token_stats
        )
        total_tokens_all_ocr = sum(
            r.token_stats.tokens_all_ocr for r in successful_results if r.token_stats
        )
        total_tokens_full_image = sum(
            r.token_stats.tokens_full_image for r in successful_results if r.token_stats
        )
        savings_vs_ocr = (
            f"{(1 - total_tokens_selected / total_tokens_all_ocr) * 100:.1f}%"
            if total_tokens_all_ocr > 0
            else "N/A"
        )
        savings_vs_image = (
            f"{(1 - total_tokens_selected / total_tokens_full_image) * 100:.1f}%"
            if total_tokens_full_image > 0
            else "N/A"
        )
        logger.info(
            "Token usage: selected=%d, all_ocr=%d, full_image=%d | "
            "Savings vs all OCR: %s, vs full image: %s",
            total_tokens_selected,
            total_tokens_all_ocr,
            total_tokens_full_image,
            savings_vs_ocr,
            savings_vs_image,
        )

        return results, summary, summary_path
