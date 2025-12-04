"""
BBox-DocVQA dataset loader.

This module provides utilities for loading and processing the BBox-DocVQA dataset
for evaluation of spatially-grounded document retrieval.
"""

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Represents a bounding box with pixel coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_list(cls, bbox: List[float]) -> "BoundingBox":
        """Create from [x1, y1, x2, y2] format."""
        if len(bbox) != 4:
            raise ValueError(f"Expected 4 values, got {len(bbox)}")
        return cls(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3])

    @classmethod
    def from_xywh(cls, x: float, y: float, w: float, h: float) -> "BoundingBox":
        """Create from x, y, width, height format."""
        return cls(x1=x, y1=y, x2=x + w, y2=y + h)

    def to_list(self) -> List[float]:
        """Convert to [x1, y1, x2, y2] format."""
        return [self.x1, self.y1, self.x2, self.y2]

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return max(0, self.width) * max(0, self.height)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class OCRRegion:
    """Represents an OCR-extracted text region."""

    content: str
    bbox: BoundingBox
    label: str = "text"
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format compatible with region_relevance.py."""
        return {
            "content": self.content,
            "bbox": self.bbox.to_list(),
            "label": self.label,
            "confidence": self.confidence,
        }


@dataclass
class Sample:
    """A single evaluation sample from BBox-DocVQA."""

    sample_id: str
    question: str
    answer: str
    ground_truth_bbox: BoundingBox
    image_path: Path
    ocr_regions: List[OCRRegion] = field(default_factory=list)
    full_page_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def image(self) -> Image.Image:
        """Load and return the document image."""
        return Image.open(self.image_path)

    @property
    def image_dimensions(self) -> Tuple[int, int]:
        """Return (width, height) of the image."""
        with Image.open(self.image_path) as img:
            return img.size


class BBoxDocVQADataset:
    """
    Loader for the BBox-DocVQA dataset.

    The dataset should be organized as:
        dataset_root/
            images/
                doc_001.png
                doc_002.png
                ...
            annotations.json (or annotations/)
            ocr/ (optional, pre-extracted OCR)
                doc_001.json
                doc_002.json
                ...

    Annotations JSON format (per sample):
    {
        "sample_id": "unique_id",
        "image": "doc_001.png",
        "question": "What is the total amount?",
        "answer": "$1,234.56",
        "bbox": [x1, y1, x2, y2] or {"x": x, "y": y, "width": w, "height": h}
    }
    """

    def __init__(
        self,
        dataset_root: Path,
        annotations_file: Optional[Path] = None,
        ocr_dir: Optional[Path] = None,
        images_dir: Optional[Path] = None,
    ):
        """
        Initialize the dataset loader.

        Args:
            dataset_root: Root directory of the dataset
            annotations_file: Path to annotations JSON (default: dataset_root/annotations.json)
            ocr_dir: Directory with pre-extracted OCR (default: dataset_root/ocr/)
            images_dir: Directory with document images (default: dataset_root/images/)
        """
        self.dataset_root = Path(dataset_root)
        self.annotations_file = annotations_file or self.dataset_root / "annotations.json"
        self.ocr_dir = ocr_dir or self.dataset_root / "ocr"
        self.images_dir = images_dir or self.dataset_root / "images"

        self._samples: List[Sample] = []
        self._loaded = False

    def load(self) -> "BBoxDocVQADataset":
        """Load the dataset from disk."""
        if self._loaded:
            return self

        logger.info(f"Loading BBox-DocVQA dataset from {self.dataset_root}")

        # Load annotations
        if not self.annotations_file.exists():
            raise FileNotFoundError(f"Annotations file not found: {self.annotations_file}")

        with open(self.annotations_file, "r", encoding="utf-8") as f:
            annotations = json.load(f)

        # Handle both list and dict formats
        if isinstance(annotations, dict):
            # Format: {"samples": [...]} or {"data": [...]}
            samples_data = annotations.get("samples") or annotations.get("data") or []
        else:
            samples_data = annotations

        for ann in samples_data:
            try:
                sample = self._parse_annotation(ann)
                if sample:
                    self._samples.append(sample)
            except Exception as e:
                logger.warning(f"Failed to parse annotation: {e}")
                continue

        self._loaded = True
        logger.info(f"Loaded {len(self._samples)} samples")
        return self

    def _parse_annotation(self, ann: Dict[str, Any]) -> Optional[Sample]:
        """Parse a single annotation into a Sample."""
        # Extract sample ID
        sample_id = str(ann.get("sample_id") or ann.get("questionId") or ann.get("id", ""))

        # Extract question and answer
        question = ann.get("question", "")
        answer = ann.get("answer", "")
        if isinstance(answer, list):
            answer = answer[0] if answer else ""

        # Extract image path
        image_name = ann.get("image") or ann.get("image_name") or ann.get("docId", "")
        if not image_name:
            return None

        image_path = self.images_dir / image_name
        if not image_path.exists():
            # Try common extensions
            for ext in [".png", ".jpg", ".jpeg", ".tiff"]:
                alt_path = self.images_dir / f"{Path(image_name).stem}{ext}"
                if alt_path.exists():
                    image_path = alt_path
                    break

        # Extract bounding box
        bbox_data = ann.get("bbox") or ann.get("bounding_box") or ann.get("evidence_bbox")
        if not bbox_data:
            return None

        if isinstance(bbox_data, list):
            gt_bbox = BoundingBox.from_list(bbox_data)
        elif isinstance(bbox_data, dict):
            if "x1" in bbox_data:
                gt_bbox = BoundingBox(
                    x1=bbox_data["x1"],
                    y1=bbox_data["y1"],
                    x2=bbox_data["x2"],
                    y2=bbox_data["y2"],
                )
            else:
                gt_bbox = BoundingBox.from_xywh(
                    x=bbox_data.get("x", 0),
                    y=bbox_data.get("y", 0),
                    w=bbox_data.get("width", 0),
                    h=bbox_data.get("height", 0),
                )
        else:
            return None

        # Load pre-extracted OCR if available
        ocr_regions = []
        full_page_text = ""
        ocr_file = self.ocr_dir / f"{Path(image_name).stem}.json"
        if ocr_file.exists():
            ocr_regions, full_page_text = self._load_ocr(ocr_file)

        return Sample(
            sample_id=sample_id,
            question=question,
            answer=answer,
            ground_truth_bbox=gt_bbox,
            image_path=image_path,
            ocr_regions=ocr_regions,
            full_page_text=full_page_text,
            metadata=ann.get("metadata", {}),
        )

    def _load_ocr(self, ocr_file: Path) -> Tuple[List[OCRRegion], str]:
        """Load pre-extracted OCR data."""
        with open(ocr_file, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)

        regions = []
        full_text_parts = []

        # Handle different OCR formats
        ocr_regions = ocr_data.get("regions") or ocr_data.get("blocks") or []
        for region_data in ocr_regions:
            content = region_data.get("content") or region_data.get("text", "")
            bbox_data = region_data.get("bbox") or region_data.get("bounding_box", [])

            if content and bbox_data:
                if isinstance(bbox_data, list) and len(bbox_data) >= 4:
                    bbox = BoundingBox.from_list(bbox_data[:4])
                elif isinstance(bbox_data, dict):
                    bbox = BoundingBox(
                        x1=bbox_data.get("x1", 0),
                        y1=bbox_data.get("y1", 0),
                        x2=bbox_data.get("x2", 0),
                        y2=bbox_data.get("y2", 0),
                    )
                else:
                    continue

                regions.append(
                    OCRRegion(
                        content=content,
                        bbox=bbox,
                        label=region_data.get("label", "text"),
                        confidence=region_data.get("confidence", 1.0),
                    )
                )
                full_text_parts.append(content)

        # Also check for full_text field
        full_text = ocr_data.get("full_text") or ocr_data.get("text") or "\n".join(full_text_parts)

        return regions, full_text

    def __len__(self) -> int:
        if not self._loaded:
            self.load()
        return len(self._samples)

    def __getitem__(self, idx: int) -> Sample:
        if not self._loaded:
            self.load()
        return self._samples[idx]

    def __iter__(self) -> Iterator[Sample]:
        if not self._loaded:
            self.load()
        return iter(self._samples)

    def sample(self, n: int, seed: Optional[int] = None) -> List[Sample]:
        """Return a random sample of n items from the dataset."""
        if not self._loaded:
            self.load()

        if seed is not None:
            random.seed(seed)

        n = min(n, len(self._samples))
        return random.sample(self._samples, n)

    def filter(
        self,
        min_regions: int = 0,
        max_regions: Optional[int] = None,
        has_ocr: bool = False,
    ) -> List[Sample]:
        """Filter samples based on criteria."""
        if not self._loaded:
            self.load()

        result = []
        for sample in self._samples:
            if has_ocr and not sample.ocr_regions:
                continue
            if len(sample.ocr_regions) < min_regions:
                continue
            if max_regions is not None and len(sample.ocr_regions) > max_regions:
                continue
            result.append(sample)

        return result


def create_sample_from_raw(
    sample_id: str,
    question: str,
    answer: str,
    image_path: Path,
    ground_truth_bbox: List[float],
    ocr_regions: Optional[List[Dict[str, Any]]] = None,
    full_page_text: str = "",
) -> Sample:
    """
    Helper function to create a Sample from raw data.

    Useful for creating samples programmatically or from external sources.
    """
    gt_bbox = BoundingBox.from_list(ground_truth_bbox)

    parsed_regions = []
    if ocr_regions:
        for region in ocr_regions:
            parsed_regions.append(
                OCRRegion(
                    content=region.get("content", ""),
                    bbox=BoundingBox.from_list(region.get("bbox", [0, 0, 0, 0])),
                    label=region.get("label", "text"),
                    confidence=region.get("confidence", 1.0),
                )
            )

    return Sample(
        sample_id=sample_id,
        question=question,
        answer=answer,
        ground_truth_bbox=gt_bbox,
        image_path=image_path,
        ocr_regions=parsed_regions,
        full_page_text=full_page_text,
    )
