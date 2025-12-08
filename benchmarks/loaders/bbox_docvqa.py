"""
BBox_DocVQA Dataset Loader.

Dataset: Yuwh07/BBox_DocVQA_Bench (1,623 QA pairs, 80 documents)
Paper: arxiv.org/abs/2512.02660 - Spatially-Grounded Document Retrieval

Complexity categories:
- SPSBB: Single-Page Single-Box (46%)
- SPMBB: Single-Page Multi-Box (34%)
- MPMBB: Multi-Page Multi-Box (20%)

Region types:
- text (61%)
- image (25%)
- table (14%)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import numpy as np

from benchmarks.utils.coordinates import Box, normalize_bbox_pixels

logger = logging.getLogger(__name__)


class ComplexityType(str, Enum):
    """Sample complexity categories."""

    SPSBB = "SPSBB"  # Single-Page Single-Box
    SPMBB = "SPMBB"  # Single-Page Multi-Box
    MPMBB = "MPMBB"  # Multi-Page Multi-Box


class RegionType(str, Enum):
    """Region type categories."""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"


@dataclass
class GroundTruthBox:
    """Ground truth bounding box with metadata."""

    box: Box
    page_idx: int
    region_type: Optional[RegionType] = None
    text_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "box": self.box.to_tuple(),
            "page_idx": self.page_idx,
            "region_type": self.region_type.value if self.region_type else None,
            "text_content": self.text_content,
        }


@dataclass
class BBoxDocVQASample:
    """A single sample from the BBox_DocVQA dataset."""

    sample_id: str
    question: str
    answer: str
    document_id: str
    page_indices: List[int]
    ground_truth_boxes: List[GroundTruthBox]
    complexity: ComplexityType
    domain: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    image_dimensions: List[Tuple[int, int]] = field(default_factory=list)

    @property
    def is_single_page(self) -> bool:
        """Check if sample involves only one page."""
        return len(set(self.page_indices)) == 1

    @property
    def num_boxes(self) -> int:
        """Number of ground truth boxes."""
        return len(self.ground_truth_boxes)

    def get_boxes_for_page(self, page_idx: int) -> List[Box]:
        """Get ground truth boxes for a specific page."""
        return [
            gt.box for gt in self.ground_truth_boxes if gt.page_idx == page_idx
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_id": self.sample_id,
            "question": self.question,
            "answer": self.answer,
            "document_id": self.document_id,
            "page_indices": self.page_indices,
            "ground_truth_boxes": [gt.to_dict() for gt in self.ground_truth_boxes],
            "complexity": self.complexity.value,
            "domain": self.domain,
            "image_paths": self.image_paths,
            "image_dimensions": self.image_dimensions,
        }


def _determine_complexity(
    evidence_pages: List[int],
    num_boxes: int,
) -> ComplexityType:
    """
    Determine complexity category based on evidence pages and boxes.

    Args:
        evidence_pages: List of page indices where evidence is found
        num_boxes: Number of ground truth bounding boxes

    Returns:
        ComplexityType enum value
    """
    unique_pages = len(set(evidence_pages))

    if unique_pages == 1:
        if num_boxes == 1:
            return ComplexityType.SPSBB
        else:
            return ComplexityType.SPMBB
    else:
        return ComplexityType.MPMBB


def _parse_region_type(type_str: Optional[str]) -> Optional[RegionType]:
    """Parse region type string to enum."""
    if not type_str:
        return None

    type_lower = type_str.lower()
    if "text" in type_lower:
        return RegionType.TEXT
    elif "image" in type_lower or "figure" in type_lower:
        return RegionType.IMAGE
    elif "table" in type_lower:
        return RegionType.TABLE

    return None


class BBoxDocVQALoader:
    """
    Loader for BBox_DocVQA benchmark dataset.

    This loader handles the HuggingFace dataset format and provides
    easy access to samples with normalized coordinates.
    """

    def __init__(
        self,
        dataset_path: str = "Yuwh07/BBox_DocVQA_Bench",
        cache_dir: Optional[str] = None,
        filter_type: str = "single_page",
    ):
        """
        Initialize the dataset loader.

        Args:
            dataset_path: HuggingFace dataset path
            cache_dir: Optional cache directory for dataset
            filter_type: Filter samples by type:
                - 'single_page': Only single-page samples (80.4%)
                - 'multi_page': Only multi-page samples
                - 'all': All samples
        """
        self.dataset_path = dataset_path
        self.cache_dir = cache_dir
        self.filter_type = filter_type
        self._dataset = None
        self._samples: Optional[List[BBoxDocVQASample]] = None

    def load(self) -> "BBoxDocVQALoader":
        """
        Load the dataset from HuggingFace.

        Returns:
            Self for chaining
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "datasets library is required. Install with: pip install datasets"
            )

        logger.info(f"Loading dataset from {self.dataset_path}")

        self._dataset = load_dataset(
            self.dataset_path,
            cache_dir=self.cache_dir,
            trust_remote_code=True,
        )

        self._parse_samples()

        logger.info(
            f"Loaded {len(self._samples)} samples "
            f"(filter: {self.filter_type})"
        )

        return self

    def _parse_samples(self) -> None:
        """Parse raw dataset into BBoxDocVQASample objects."""
        if self._dataset is None:
            raise RuntimeError("Dataset not loaded. Call load() first.")

        self._samples = []

        # The dataset may have 'train', 'test', or other splits
        # We'll process all available splits
        splits = (
            self._dataset.keys()
            if hasattr(self._dataset, "keys")
            else ["train"]
        )

        for split in splits:
            data = (
                self._dataset[split]
                if hasattr(self._dataset, "__getitem__")
                else self._dataset
            )

            for idx, item in enumerate(data):
                sample = self._parse_item(item, f"{split}_{idx}")
                if sample is not None:
                    if self._should_include(sample):
                        self._samples.append(sample)

    def _parse_item(
        self,
        item: Dict[str, Any],
        fallback_id: str,
    ) -> Optional[BBoxDocVQASample]:
        """
        Parse a single dataset item into a BBoxDocVQASample.

        Args:
            item: Raw dataset item
            fallback_id: ID to use if not present in item

        Returns:
            Parsed sample or None if invalid
        """
        try:
            # Extract basic fields
            sample_id = str(item.get("id", item.get("sample_id", fallback_id)))
            question = item.get("question", item.get("query", ""))
            answer = item.get("answer", item.get("answers", [""]))[0] if isinstance(
                item.get("answer", item.get("answers", "")), list
            ) else item.get("answer", item.get("answers", ""))
            document_id = str(item.get("document_id", item.get("doc_id", "")))
            domain = item.get("domain", item.get("category", None))

            # Extract evidence pages
            evidence_pages = item.get(
                "evidence_page",
                item.get("evidence_pages", item.get("page_indices", [0])),
            )
            if not isinstance(evidence_pages, list):
                evidence_pages = [evidence_pages]
            evidence_pages = [int(p) for p in evidence_pages]

            # Extract ground truth bounding boxes
            gt_boxes = []
            bboxes = item.get("bboxes", item.get("bbox", item.get("ground_truth_boxes", [])))

            if isinstance(bboxes, dict):
                # Format: {page_idx: [[x1,y1,x2,y2], ...]}
                for page_str, boxes in bboxes.items():
                    page_idx = int(page_str) if isinstance(page_str, str) else page_str
                    for box_coords in boxes:
                        if len(box_coords) >= 4:
                            # Get image dimensions for this page
                            img_dims = self._get_image_dimensions(item, page_idx)
                            if img_dims:
                                norm_box = normalize_bbox_pixels(
                                    tuple(box_coords[:4]),
                                    img_dims[0],
                                    img_dims[1],
                                )
                                gt_boxes.append(
                                    GroundTruthBox(box=norm_box, page_idx=page_idx)
                                )
            elif isinstance(bboxes, list):
                # Format: [[x1,y1,x2,y2], ...] all on first evidence page
                default_page = evidence_pages[0] if evidence_pages else 0
                img_dims = self._get_image_dimensions(item, default_page)

                for box_data in bboxes:
                    if isinstance(box_data, dict):
                        coords = box_data.get("bbox", box_data.get("coordinates", []))
                        page_idx = box_data.get("page", box_data.get("page_idx", default_page))
                        region_type = _parse_region_type(
                            box_data.get("type", box_data.get("region_type"))
                        )
                        text = box_data.get("text", box_data.get("content"))
                    else:
                        coords = box_data
                        page_idx = default_page
                        region_type = None
                        text = None

                    if len(coords) >= 4 and img_dims:
                        norm_box = normalize_bbox_pixels(
                            tuple(coords[:4]),
                            img_dims[0],
                            img_dims[1],
                        )
                        gt_boxes.append(
                            GroundTruthBox(
                                box=norm_box,
                                page_idx=page_idx,
                                region_type=region_type,
                                text_content=text,
                            )
                        )

            if not gt_boxes:
                logger.debug(f"Skipping sample {sample_id}: no valid ground truth boxes")
                return None

            # Determine complexity
            complexity = _determine_complexity(evidence_pages, len(gt_boxes))

            # Get image paths
            image_paths = item.get(
                "image_paths",
                item.get("images", item.get("image", [])),
            )
            if isinstance(image_paths, str):
                image_paths = [image_paths]

            # Get image dimensions
            image_dims = []
            dims = item.get("image_dimensions", item.get("dimensions", []))
            if dims:
                for d in dims:
                    if isinstance(d, (list, tuple)) and len(d) >= 2:
                        image_dims.append((int(d[0]), int(d[1])))
                    elif isinstance(d, dict):
                        image_dims.append(
                            (int(d.get("width", 0)), int(d.get("height", 0)))
                        )

            return BBoxDocVQASample(
                sample_id=sample_id,
                question=question,
                answer=answer,
                document_id=document_id,
                page_indices=evidence_pages,
                ground_truth_boxes=gt_boxes,
                complexity=complexity,
                domain=domain,
                image_paths=image_paths,
                image_dimensions=image_dims,
            )

        except Exception as e:
            logger.warning(f"Error parsing item {fallback_id}: {e}")
            return None

    def _get_image_dimensions(
        self,
        item: Dict[str, Any],
        page_idx: int,
    ) -> Optional[Tuple[int, int]]:
        """Get image dimensions for a specific page."""
        dims = item.get("image_dimensions", item.get("dimensions", []))

        if not dims:
            # Try to get from image metadata
            images = item.get("images", item.get("image", []))
            if images:
                try:
                    from PIL import Image

                    img_data = images[page_idx] if page_idx < len(images) else images[0]
                    if hasattr(img_data, "size"):
                        return img_data.size
                except (IndexError, ImportError):
                    pass

            # Default fallback dimensions
            return (1000, 1000)

        if page_idx < len(dims):
            d = dims[page_idx]
        elif dims:
            d = dims[0]
        else:
            return (1000, 1000)

        if isinstance(d, (list, tuple)) and len(d) >= 2:
            return (int(d[0]), int(d[1]))
        elif isinstance(d, dict):
            return (int(d.get("width", 1000)), int(d.get("height", 1000)))

        return (1000, 1000)

    def _should_include(self, sample: BBoxDocVQASample) -> bool:
        """Check if sample should be included based on filter."""
        if self.filter_type == "all":
            return True
        elif self.filter_type == "single_page":
            return sample.is_single_page
        elif self.filter_type == "multi_page":
            return not sample.is_single_page
        else:
            return True

    @property
    def samples(self) -> List[BBoxDocVQASample]:
        """Get all loaded samples."""
        if self._samples is None:
            raise RuntimeError("Dataset not loaded. Call load() first.")
        return self._samples

    def __len__(self) -> int:
        """Get number of samples."""
        return len(self.samples)

    def __iter__(self) -> Iterator[BBoxDocVQASample]:
        """Iterate over samples."""
        return iter(self.samples)

    def __getitem__(self, idx: int) -> BBoxDocVQASample:
        """Get sample by index."""
        return self.samples[idx]

    def get_by_complexity(
        self,
        complexity: ComplexityType,
    ) -> List[BBoxDocVQASample]:
        """Get samples by complexity type."""
        return [s for s in self.samples if s.complexity == complexity]

    def get_by_domain(self, domain: str) -> List[BBoxDocVQASample]:
        """Get samples by domain."""
        return [s for s in self.samples if s.domain == domain]

    def get_stratified_sample(
        self,
        n_per_category: int = 5,
        categories: Optional[List[ComplexityType]] = None,
    ) -> List[BBoxDocVQASample]:
        """
        Get stratified sample across complexity categories.

        Args:
            n_per_category: Number of samples per category
            categories: Categories to include (default: all)

        Returns:
            Stratified list of samples
        """
        if categories is None:
            categories = list(ComplexityType)

        result = []
        for cat in categories:
            cat_samples = self.get_by_complexity(cat)
            n = min(n_per_category, len(cat_samples))
            if n > 0:
                indices = np.random.choice(len(cat_samples), n, replace=False)
                result.extend([cat_samples[i] for i in indices])

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        samples = self.samples

        complexity_counts = {}
        for c in ComplexityType:
            complexity_counts[c.value] = len(self.get_by_complexity(c))

        domain_counts: Dict[str, int] = {}
        for s in samples:
            if s.domain:
                domain_counts[s.domain] = domain_counts.get(s.domain, 0) + 1

        region_type_counts: Dict[str, int] = {}
        for s in samples:
            for gt in s.ground_truth_boxes:
                if gt.region_type:
                    key = gt.region_type.value
                    region_type_counts[key] = region_type_counts.get(key, 0) + 1

        return {
            "total_samples": len(samples),
            "complexity_distribution": complexity_counts,
            "domain_distribution": domain_counts,
            "region_type_distribution": region_type_counts,
            "single_page_count": sum(1 for s in samples if s.is_single_page),
            "multi_page_count": sum(1 for s in samples if not s.is_single_page),
            "avg_boxes_per_sample": np.mean([s.num_boxes for s in samples]),
            "unique_documents": len(set(s.document_id for s in samples)),
        }


def load_bbox_docvqa(
    dataset_path: str = "Yuwh07/BBox_DocVQA_Bench",
    cache_dir: Optional[str] = None,
    filter_type: str = "single_page",
    max_samples: Optional[int] = None,
) -> List[BBoxDocVQASample]:
    """
    Convenience function to load BBox_DocVQA dataset.

    Args:
        dataset_path: HuggingFace dataset path
        cache_dir: Optional cache directory
        filter_type: Filter type ('single_page', 'multi_page', 'all')
        max_samples: Maximum number of samples to return

    Returns:
        List of samples
    """
    loader = BBoxDocVQALoader(
        dataset_path=dataset_path,
        cache_dir=cache_dir,
        filter_type=filter_type,
    )
    loader.load()

    samples = loader.samples
    if max_samples is not None:
        samples = samples[:max_samples]

    return samples
