"""
BBox_DocVQA_Bench dataset loader and utilities.

Dataset structure:
- query: Natural language question
- answer: Ground truth answer
- category: ArXiv subject category (cs, econ, eess, math, physics, q-bio, q-fin, stat)
- doc_name: ArXiv document identifier
- evidence_page: 1-based page numbers containing evidence
- image_paths/images: Paths to rendered PNG pages
- bbox: Pixel coordinates for evidence regions [[x1, y1, x2, y2], ...]
- subimg_type: Classification as "text", "table", or "image"
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    """A single benchmark sample from BBox_DocVQA_Bench."""

    sample_id: str
    query: str
    answer: str
    category: str
    doc_name: str
    evidence_pages: List[int]  # 1-based page numbers
    image_paths: List[str]
    bboxes: List[List[int]]  # [[x1, y1, x2, y2], ...]
    subimg_type: str  # "text", "table", or "image"
    raw_data: Dict[str, Any]  # Original JSON data

    @property
    def is_multi_page(self) -> bool:
        """Check if sample references multiple pages."""
        return len(self.evidence_pages) > 1

    @property
    def has_multiple_bboxes(self) -> bool:
        """Check if sample has multiple bounding boxes."""
        return len(self.bboxes) > 1

    def get_evidence_type(self) -> str:
        """Get human-readable evidence type."""
        return self.subimg_type.capitalize()


class BBoxDocVQADataset:
    """
    Loader for BBox_DocVQA_Bench dataset from Hugging Face.

    Supports both:
    1. Direct Hugging Face datasets loading
    2. Local JSONL file loading
    """

    def __init__(
        self,
        dataset_name: str = "Yuwh07/BBox_DocVQA_Bench",
        cache_dir: str = "./benchmark_cache",
        use_huggingface: bool = True,
    ):
        """
        Initialize dataset loader.

        Args:
            dataset_name: HuggingFace dataset name or path to local JSONL
            cache_dir: Directory for caching downloaded data
            use_huggingface: Whether to use HuggingFace datasets library
        """
        self.dataset_name = dataset_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_huggingface = use_huggingface

        self._dataset = None
        self._samples: List[BenchmarkSample] = []
        self._loaded = False

    def load(
        self,
        split: str = "train",
        max_samples: Optional[int] = None,
        categories: Optional[List[str]] = None,
    ) -> "BBoxDocVQADataset":
        """
        Load dataset from HuggingFace or local file.

        Args:
            split: Dataset split to load
            max_samples: Maximum number of samples to load
            categories: Filter by specific arXiv categories

        Returns:
            Self for method chaining
        """
        if self.use_huggingface:
            self._load_from_huggingface(split, max_samples, categories)
        else:
            self._load_from_local(max_samples, categories)

        self._loaded = True
        logger.info(f"Loaded {len(self._samples)} samples from {self.dataset_name}")
        return self

    def _load_from_huggingface(
        self,
        split: str,
        max_samples: Optional[int],
        categories: Optional[List[str]],
    ) -> None:
        """Load dataset using HuggingFace datasets library."""
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "HuggingFace datasets library required. "
                "Install with: pip install datasets"
            )

        logger.info(f"Loading dataset {self.dataset_name} from HuggingFace...")
        self._dataset = load_dataset(
            self.dataset_name, split=split, cache_dir=str(self.cache_dir)
        )

        self._samples = []
        for idx, item in enumerate(self._dataset):
            if max_samples and idx >= max_samples:
                break

            sample = self._parse_sample(item, idx)

            # Filter by category if specified
            if categories and sample.category not in categories:
                continue

            self._samples.append(sample)

    def _load_from_local(
        self,
        max_samples: Optional[int],
        categories: Optional[List[str]],
    ) -> None:
        """Load dataset from local JSONL file."""
        jsonl_path = Path(self.dataset_name)
        if not jsonl_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {jsonl_path}")

        logger.info(f"Loading dataset from local file: {jsonl_path}")
        self._samples = []

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if max_samples and idx >= max_samples:
                    break

                item = json.loads(line.strip())
                sample = self._parse_sample(item, idx)

                if categories and sample.category not in categories:
                    continue

                self._samples.append(sample)

    def _parse_sample(self, item: Dict[str, Any], idx: int) -> BenchmarkSample:
        """Parse raw dataset item into BenchmarkSample."""
        # Handle different field naming conventions
        query = item.get("query") or item.get("question", "")
        answer = item.get("answer", "")
        category = item.get("category", "unknown")
        doc_name = item.get("doc_name", "")

        # Evidence pages (1-based)
        evidence_pages = item.get("evidence_page", [])
        if isinstance(evidence_pages, int):
            evidence_pages = [evidence_pages]

        # Image paths
        image_paths = item.get("image_paths") or item.get("images", [])
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        # Bounding boxes
        bboxes = item.get("bbox", [])
        if bboxes and not isinstance(bboxes[0], list):
            # Single bbox as flat list
            bboxes = [bboxes]

        # Sub-image type
        subimg_type = item.get("subimg_tpye") or item.get("subimg_type", "text")

        return BenchmarkSample(
            sample_id=f"{category}_{doc_name}_{idx}",
            query=query,
            answer=answer,
            category=category,
            doc_name=doc_name,
            evidence_pages=evidence_pages,
            image_paths=image_paths,
            bboxes=bboxes,
            subimg_type=subimg_type,
            raw_data=item,
        )

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self._samples)

    def __iter__(self) -> Iterator[BenchmarkSample]:
        """Iterate over samples."""
        return iter(self._samples)

    def __getitem__(self, idx: int) -> BenchmarkSample:
        """Get sample by index."""
        return self._samples[idx]

    def get_samples_by_category(
        self, category: str
    ) -> List[BenchmarkSample]:
        """Get all samples for a specific category."""
        return [s for s in self._samples if s.category == category]

    def get_samples_by_type(self, subimg_type: str) -> List[BenchmarkSample]:
        """Get all samples by sub-image type (text, table, image)."""
        return [s for s in self._samples if s.subimg_type == subimg_type]

    def get_multi_page_samples(self) -> List[BenchmarkSample]:
        """Get samples that reference multiple pages."""
        return [s for s in self._samples if s.is_multi_page]

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self._samples:
            return {}

        categories = {}
        types = {}
        multi_page_count = 0
        multi_bbox_count = 0

        for sample in self._samples:
            categories[sample.category] = categories.get(sample.category, 0) + 1
            types[sample.subimg_type] = types.get(sample.subimg_type, 0) + 1
            if sample.is_multi_page:
                multi_page_count += 1
            if sample.has_multiple_bboxes:
                multi_bbox_count += 1

        return {
            "total_samples": len(self._samples),
            "categories": categories,
            "evidence_types": types,
            "multi_page_samples": multi_page_count,
            "multi_bbox_samples": multi_bbox_count,
        }

    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load an image from the dataset.

        Args:
            image_path: Relative path to image within dataset

        Returns:
            PIL Image or None if not found
        """
        # Try multiple potential locations
        potential_paths = [
            self.cache_dir / image_path,
            Path(image_path),
            self.cache_dir / "images" / image_path,
        ]

        for path in potential_paths:
            if path.exists():
                try:
                    return Image.open(path).convert("RGB")
                except Exception as e:
                    logger.warning(f"Failed to load image {path}: {e}")

        logger.warning(f"Image not found: {image_path}")
        return None

    def prepare_for_indexing(
        self,
    ) -> Iterator[Tuple[str, str, List[Tuple[Image.Image, int]]]]:
        """
        Prepare dataset for indexing into Snappy.

        Yields:
            Tuples of (doc_name, category, [(image, page_num), ...])
        """
        # Group samples by document
        docs: Dict[str, Dict[str, Any]] = {}

        for sample in self._samples:
            doc_key = f"{sample.category}/{sample.doc_name}"
            if doc_key not in docs:
                docs[doc_key] = {
                    "doc_name": sample.doc_name,
                    "category": sample.category,
                    "pages": {},
                }

            # Collect unique pages
            for i, page_num in enumerate(sample.evidence_pages):
                if page_num not in docs[doc_key]["pages"]:
                    if i < len(sample.image_paths):
                        docs[doc_key]["pages"][page_num] = sample.image_paths[i]

        # Yield documents with loaded images
        for doc_key, doc_info in docs.items():
            images = []
            for page_num, image_path in sorted(doc_info["pages"].items()):
                img = self.load_image(image_path)
                if img:
                    images.append((img, page_num))

            if images:
                yield doc_info["doc_name"], doc_info["category"], images
