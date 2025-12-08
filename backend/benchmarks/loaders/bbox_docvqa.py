"""
Dataset loader for BBox_DocVQA_Bench.

This loader handles the BBox_DocVQA benchmark dataset from:
https://huggingface.co/datasets/Yuwh07/BBox_DocVQA_Bench

Dataset structure (JSONL):
- question: The question text
- answer: Ground truth answer
- evidence_bbox: List of bounding boxes [[x1, y1, x2, y2], ...]
- evidence_page: List of page numbers
- category: Complexity category (SPSBB, SPMBB, MPMBB)
- region_type: Type of region (Text, Image, Table)
- domain: Academic domain (cs, econ, math, etc.)
- image: Image filename or path
"""

import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Literal, Optional, Tuple, Union

from PIL import Image

logger = logging.getLogger(__name__)


def _find_hf_cache_zip(dataset_name: str = "Yuwh07/BBox_DocVQA_Bench") -> Optional[Path]:
    """
    Find the HuggingFace cached images zip file.

    Args:
        dataset_name: HuggingFace dataset identifier

    Returns:
        Path to the zip file if found, None otherwise
    """
    try:
        from huggingface_hub import hf_hub_download, try_to_load_from_cache
    except ImportError:
        return None

    # Try to find in cache first
    cached = try_to_load_from_cache(
        repo_id=dataset_name,
        filename="BBox_DocVQA_Bench_Images.zip",
        repo_type="dataset",
    )
    if cached and Path(cached).exists():
        return Path(cached)

    # If not cached, download it
    try:
        downloaded = hf_hub_download(
            repo_id=dataset_name,
            filename="BBox_DocVQA_Bench_Images.zip",
            repo_type="dataset",
        )
        return Path(downloaded)
    except Exception as e:
        logger.warning(f"Could not download images zip: {e}")
        return None


class ZipImageReader:
    """Helper class to read images from a zip file."""

    def __init__(self, zip_path: Path):
        self.zip_path = zip_path
        self._zip_file: Optional[zipfile.ZipFile] = None
        self._namelist: Optional[set] = None

    def _ensure_open(self):
        if self._zip_file is None:
            self._zip_file = zipfile.ZipFile(self.zip_path, "r")
            self._namelist = set(self._zip_file.namelist())

    def read_image(self, image_path: str) -> Image.Image:
        """Read an image from the zip file."""
        self._ensure_open()

        # Try different path variations
        paths_to_try = [
            image_path,
            image_path.lstrip("/"),
            f"BBox_DocVQA_Bench_Images/{image_path}",
        ]

        for path in paths_to_try:
            if path in self._namelist:
                with self._zip_file.open(path) as f:
                    return Image.open(io.BytesIO(f.read()))

        raise FileNotFoundError(f"Image not found in zip: {image_path}")

    def close(self):
        if self._zip_file:
            self._zip_file.close()
            self._zip_file = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# Complexity categories
CategoryType = Literal["SPSBB", "SPMBB", "MPMBB"]

# Region types
RegionType = Literal["Text", "Image", "Table"]

# Academic domains
DomainType = Literal[
    "cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat"
]


@dataclass
class BBoxDocVQASample:
    """A single sample from BBox_DocVQA_Bench."""

    # Core fields
    question: str
    answer: str
    evidence_bbox: List[List[float]]  # [[x1, y1, x2, y2], ...]
    evidence_page: List[int]
    image_path: str

    # Metadata
    category: Optional[CategoryType] = None
    region_type: Optional[RegionType] = None
    domain: Optional[DomainType] = None

    # Computed fields
    sample_id: str = ""
    is_single_page: bool = True

    # Image dimensions (populated when image is loaded)
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    # Raw data for extensibility
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Compute derived fields."""
        self.is_single_page = len(self.evidence_page) == 1

    def get_normalized_bboxes(self) -> List[Tuple[float, float, float, float]]:
        """
        Get evidence bounding boxes normalized to [0, 1] space.

        Requires image dimensions to be set.

        Returns:
            List of normalized bounding boxes (x1, y1, x2, y2)
        """
        if self.image_width is None or self.image_height is None:
            raise ValueError(
                "Image dimensions must be set before normalizing bounding boxes. "
                "Call load_image() first."
            )

        normalized = []
        for bbox in self.evidence_bbox:
            x1, y1, x2, y2 = bbox
            normalized.append((
                x1 / self.image_width,
                y1 / self.image_height,
                x2 / self.image_width,
                y2 / self.image_height,
            ))
        return normalized

    def load_image(
        self,
        images_dir: Optional[Path] = None,
        zip_reader: Optional[ZipImageReader] = None,
    ) -> Image.Image:
        """
        Load the sample image and set dimensions.

        Args:
            images_dir: Base directory for images (if paths are relative)
            zip_reader: Optional ZipImageReader for reading from HuggingFace cache

        Returns:
            PIL Image object
        """
        img = None

        # Try zip reader first if provided
        if zip_reader is not None:
            try:
                img = zip_reader.read_image(self.image_path)
            except FileNotFoundError:
                pass  # Fall through to file-based loading

        # Try file-based loading
        if img is None:
            image_path = Path(self.image_path)
            if images_dir and not image_path.is_absolute():
                image_path = images_dir / image_path
            img = Image.open(image_path)

        self.image_width = img.width
        self.image_height = img.height
        return img


class BBoxDocVQALoader:
    """
    Loader for BBox_DocVQA_Bench dataset.

    Supports loading from:
    - Local JSONL file
    - HuggingFace datasets (requires `datasets` library)
    """

    def __init__(
        self,
        jsonl_path: Optional[str] = None,
        images_dir: Optional[str] = None,
        hf_dataset: Optional[str] = "Yuwh07/BBox_DocVQA_Bench",
        images_zip_path: Optional[str] = None,
    ):
        """
        Initialize the loader.

        Args:
            jsonl_path: Path to local JSONL file (optional)
            images_dir: Directory containing images (optional)
            hf_dataset: HuggingFace dataset identifier (optional)
            images_zip_path: Path to images zip file (optional, auto-detected from HF cache)
        """
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        self.images_dir = Path(images_dir) if images_dir else None
        self.hf_dataset = hf_dataset
        self.images_zip_path = Path(images_zip_path) if images_zip_path else None

        self._samples: List[BBoxDocVQASample] = []
        self._loaded = False
        self._zip_reader: Optional[ZipImageReader] = None

    @property
    def zip_reader(self) -> Optional[ZipImageReader]:
        """Get the zip reader for accessing images from HuggingFace cache."""
        if self._zip_reader is None:
            zip_path = self._get_images_zip_path()
            if zip_path:
                self._zip_reader = ZipImageReader(zip_path)
                logger.info(f"Using images from zip: {zip_path}")
        return self._zip_reader

    def _get_images_zip_path(self) -> Optional[Path]:
        """Get the path to the images zip file."""
        # Use explicitly provided path first
        if self.images_zip_path and self.images_zip_path.exists():
            return self.images_zip_path

        # Try to find in HuggingFace cache
        if self.hf_dataset:
            return _find_hf_cache_zip(self.hf_dataset)

        return None

    def load(self, split: str = "train") -> "BBoxDocVQALoader":
        """
        Load the dataset.

        Args:
            split: Dataset split to load ('train', 'test', etc.)

        Returns:
            Self for chaining
        """
        if self.jsonl_path and self.jsonl_path.exists():
            self._load_from_jsonl()
        elif self.hf_dataset:
            self._load_from_huggingface(split)
        else:
            raise ValueError(
                "Either jsonl_path or hf_dataset must be specified"
            )

        self._loaded = True
        logger.info(f"Loaded {len(self._samples)} samples")
        return self

    def close(self):
        """Close any open resources."""
        if self._zip_reader:
            self._zip_reader.close()
            self._zip_reader = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _load_from_jsonl(self) -> None:
        """Load samples from local JSONL file."""
        logger.info(f"Loading from JSONL: {self.jsonl_path}")

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue

                data = json.loads(line)
                sample = self._parse_sample(data, idx)
                if sample:
                    self._samples.append(sample)

    def _load_from_huggingface(self, split: str) -> None:
        """Load samples from HuggingFace datasets."""
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "Please install datasets: pip install datasets"
            )

        logger.info(f"Loading from HuggingFace: {self.hf_dataset}")

        # Explicitly load only the JSONL file to avoid the dataset loader
        # trying to parse image files as JSON
        dataset = load_dataset(
            self.hf_dataset,
            data_files="BBox_DocVQA_Bench.jsonl",
            split=split,
        )

        for idx, item in enumerate(dataset):
            sample = self._parse_sample(dict(item), idx)
            if sample:
                self._samples.append(sample)

    def _parse_sample(
        self, data: Dict[str, Any], idx: int
    ) -> Optional[BBoxDocVQASample]:
        """
        Parse a raw data dict into a BBoxDocVQASample.

        Args:
            data: Raw sample data
            idx: Sample index for ID generation

        Returns:
            Parsed sample or None if invalid
        """
        try:
            # Extract required fields (handle both local and HuggingFace field names)
            question = data.get("question") or data.get("query", "")
            answer = data.get("answer", "")

            # HuggingFace uses "bbox", local uses "evidence_bbox"
            evidence_bbox = data.get("evidence_bbox") or data.get("bbox", [])
            # Flatten nested bbox structure from HF: [[[x1,y1,x2,y2]]] -> [[x1,y1,x2,y2]]
            if evidence_bbox and isinstance(evidence_bbox[0], list):
                if evidence_bbox[0] and isinstance(evidence_bbox[0][0], list):
                    evidence_bbox = [box for page_boxes in evidence_bbox for box in page_boxes]

            evidence_page = data.get("evidence_page", [])

            # HuggingFace uses "image_paths" or "images", local uses "image"
            image_path = (
                data.get("image")
                or data.get("image_path")
                or (data.get("image_paths") or [""])[0]
                or (data.get("images") or [""])[0]
            )

            if not question or not evidence_bbox:
                logger.debug(f"Skipping sample {idx}: missing required fields")
                return None

            # Extract optional metadata
            # HuggingFace "category" is actually the domain (cs, econ, math, etc.)
            # Our "category" is complexity (SPSBB, SPMBB, MPMBB)
            hf_category = data.get("category")
            category = None
            domain = data.get("domain")

            # If hf_category looks like a domain, use it as domain
            if hf_category and hf_category.lower() in (
                "cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat"
            ):
                domain = hf_category.lower()
            elif hf_category and hf_category.upper() in ("SPSBB", "SPMBB", "MPMBB"):
                category = hf_category.upper()

            # HuggingFace uses "subimg_tpye" (typo), local uses "region_type"
            region_type = data.get("region_type")
            if not region_type:
                subimg_type = data.get("subimg_tpye") or data.get("subimg_type")
                if subimg_type and isinstance(subimg_type, list):
                    # Flatten and get first type: [["text"]] -> "Text"
                    flat = [t for page in subimg_type for t in (page if isinstance(page, list) else [page])]
                    if flat:
                        region_type = flat[0].capitalize() if flat[0] else None

            # Generate sample ID
            sample_id = data.get("id", f"sample_{idx:05d}")

            return BBoxDocVQASample(
                question=question,
                answer=answer,
                evidence_bbox=evidence_bbox,
                evidence_page=evidence_page,
                image_path=image_path,
                category=category,
                region_type=region_type,
                domain=domain,
                sample_id=sample_id,
                raw_data=data,
            )
        except Exception as e:
            logger.warning(f"Failed to parse sample {idx}: {e}")
            return None

    def filter_single_page(self) -> "BBoxDocVQALoader":
        """
        Filter to only single-page samples.

        Returns:
            Self for chaining
        """
        original_count = len(self._samples)
        self._samples = [s for s in self._samples if s.is_single_page]
        logger.info(
            f"Filtered to single-page: {original_count} -> {len(self._samples)}"
        )
        return self

    def filter_by_category(
        self, categories: List[CategoryType]
    ) -> "BBoxDocVQALoader":
        """
        Filter by complexity category.

        Args:
            categories: List of categories to include

        Returns:
            Self for chaining
        """
        original_count = len(self._samples)
        self._samples = [
            s for s in self._samples if s.category in categories
        ]
        logger.info(
            f"Filtered by category {categories}: {original_count} -> {len(self._samples)}"
        )
        return self

    def filter_by_region_type(
        self, region_types: List[RegionType]
    ) -> "BBoxDocVQALoader":
        """
        Filter by region type.

        Args:
            region_types: List of region types to include

        Returns:
            Self for chaining
        """
        original_count = len(self._samples)
        self._samples = [
            s for s in self._samples if s.region_type in region_types
        ]
        logger.info(
            f"Filtered by region_type {region_types}: {original_count} -> {len(self._samples)}"
        )
        return self

    def filter_by_domain(self, domains: List[DomainType]) -> "BBoxDocVQALoader":
        """
        Filter by academic domain.

        Args:
            domains: List of domains to include

        Returns:
            Self for chaining
        """
        original_count = len(self._samples)
        self._samples = [s for s in self._samples if s.domain in domains]
        logger.info(
            f"Filtered by domain {domains}: {original_count} -> {len(self._samples)}"
        )
        return self

    def __iter__(self) -> Iterator[BBoxDocVQASample]:
        """Iterate over samples."""
        return iter(self._samples)

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self._samples)

    def __getitem__(self, idx: int) -> BBoxDocVQASample:
        """Get sample by index."""
        return self._samples[idx]

    @property
    def samples(self) -> List[BBoxDocVQASample]:
        """Get all samples."""
        return self._samples

    def get_statistics(self) -> Dict[str, Any]:
        """
        Compute dataset statistics.

        Returns:
            Dictionary with dataset statistics
        """
        if not self._samples:
            return {"total": 0}

        # Count by category
        category_counts: Dict[str, int] = {}
        for s in self._samples:
            cat = s.category or "unknown"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Count by region type
        region_counts: Dict[str, int] = {}
        for s in self._samples:
            rt = s.region_type or "unknown"
            region_counts[rt] = region_counts.get(rt, 0) + 1

        # Count by domain
        domain_counts: Dict[str, int] = {}
        for s in self._samples:
            dom = s.domain or "unknown"
            domain_counts[dom] = domain_counts.get(dom, 0) + 1

        # Single vs multi-page
        single_page = sum(1 for s in self._samples if s.is_single_page)
        multi_page = len(self._samples) - single_page

        # Bounding box statistics
        bbox_counts = [len(s.evidence_bbox) for s in self._samples]
        avg_bboxes = sum(bbox_counts) / len(bbox_counts) if bbox_counts else 0

        return {
            "total": len(self._samples),
            "single_page": single_page,
            "multi_page": multi_page,
            "single_page_pct": single_page / len(self._samples) * 100,
            "by_category": category_counts,
            "by_region_type": region_counts,
            "by_domain": domain_counts,
            "avg_bboxes_per_sample": avg_bboxes,
            "min_bboxes": min(bbox_counts) if bbox_counts else 0,
            "max_bboxes": max(bbox_counts) if bbox_counts else 0,
        }


def load_bbox_docvqa(
    jsonl_path: Optional[str] = None,
    images_dir: Optional[str] = None,
    filter_single_page: bool = True,
    categories: Optional[List[CategoryType]] = None,
    region_types: Optional[List[RegionType]] = None,
    domains: Optional[List[DomainType]] = None,
) -> BBoxDocVQALoader:
    """
    Convenience function to load and filter BBox_DocVQA_Bench.

    Args:
        jsonl_path: Path to local JSONL file
        images_dir: Directory containing images
        filter_single_page: Whether to filter to single-page samples
        categories: Filter to specific categories
        region_types: Filter to specific region types
        domains: Filter to specific domains

    Returns:
        Configured and loaded BBoxDocVQALoader
    """
    loader = BBoxDocVQALoader(
        jsonl_path=jsonl_path,
        images_dir=images_dir,
    )
    loader.load()

    if filter_single_page:
        loader.filter_single_page()

    if categories:
        loader.filter_by_category(categories)

    if region_types:
        loader.filter_by_region_type(region_types)

    if domains:
        loader.filter_by_domain(domains)

    return loader
