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
import zipfile
from dataclasses import dataclass
from io import BytesIO
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
        """Load dataset from HuggingFace cache."""
        from huggingface_hub import hf_hub_download

        logger.info(f"Loading dataset {self.dataset_name} from HuggingFace (split={split})...")

        # Download the JSONL file and images zip to cache
        jsonl_path = hf_hub_download(
            repo_id=self.dataset_name,
            filename="BBox_DocVQA_Bench.jsonl",
            repo_type="dataset",
            cache_dir=str(self.cache_dir)
        )

        # Also ensure images are downloaded
        hf_hub_download(
            repo_id=self.dataset_name,
            filename="BBox_DocVQA_Bench_Images.zip",
            repo_type="dataset",
            cache_dir=str(self.cache_dir)
        )

        # Load directly from JSONL file
        logger.info(f"Reading JSONL from {jsonl_path}")
        self._samples = []

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if max_samples and idx >= max_samples:
                    break

                item = json.loads(line.strip())
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
        # Convert list to comma-separated string if needed
        if isinstance(subimg_type, list):
            subimg_type = ",".join(str(t) for t in subimg_type) if subimg_type else "text"

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

            # Handle subimg_type which might be a list or string
            subimg_key = sample.subimg_type
            if isinstance(subimg_key, list):
                subimg_key = ",".join(str(t) for t in subimg_key) if subimg_key else "unknown"
            types[subimg_key] = types.get(subimg_key, 0) + 1

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

        Tries multiple sources in order:
        1. Direct file path
        2. HuggingFace cache zip file
        3. Local cache directories

        Args:
            image_path: Relative path to image within dataset

        Returns:
            PIL Image or None if not found
        """
        # Try direct file paths first
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

        # Try loading from HuggingFace cache zip
        image = self._load_from_zip(image_path)
        if image:
            return image

        logger.warning(f"Image not found: {image_path}")
        return None

    def _load_from_zip(self, image_path: str) -> Optional[Image.Image]:
        """
        Load an image from the HuggingFace cache zip file.

        Args:
            image_path: Relative path to image within the zip

        Returns:
            PIL Image or None if not found
        """
        zip_path = self._find_images_zip()
        if not zip_path:
            return None

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                with zf.open(image_path) as img_file:
                    return Image.open(BytesIO(img_file.read())).convert("RGB")
        except KeyError:
            logger.debug(f"Image {image_path} not found in zip")
            return None
        except Exception as e:
            logger.warning(f"Failed to load image from zip: {e}")
            return None

    def _find_images_zip(self) -> Optional[Path]:
        """
        Find the images zip file in the HuggingFace cache.

        Returns:
            Path to the zip file or None if not found
        """
        # Look for the zip in HuggingFace cache structure
        hf_cache_pattern = "datasets--Yuwh07--BBox_DocVQA_Bench"
        for snapshot_dir in (self.cache_dir / hf_cache_pattern / "snapshots").glob("*"):
            zip_path = snapshot_dir / "BBox_DocVQA_Bench_Images.zip"
            if zip_path.exists():
                return zip_path

        return None

    def load_sample_image(self, sample: BenchmarkSample) -> Optional[Image.Image]:
        """
        Load the first image for a benchmark sample.

        This is a convenience method for loading sample images during benchmarking.

        Args:
            sample: Benchmark sample with image_paths

        Returns:
            PIL Image or None if not available
        """
        if not sample.image_paths:
            logger.warning(f"Sample {sample.sample_id} has no image_paths")
            return None

        return self.load_image(sample.image_paths[0])

    def get_image_local_path(self, sample: BenchmarkSample) -> Optional[str]:
        """
        Get the local file path to a sample's image.

        Returns a path string in the format "zip_path!/internal_path" for zip files.

        Args:
            sample: Benchmark sample with image_paths

        Returns:
            Local file path string, or None if not available
        """
        if not sample.image_paths:
            return None

        # Check if it's in a zip file
        zip_path = self._find_images_zip()
        if zip_path:
            return f"{zip_path}!/{sample.image_paths[0]}"

        # Check direct paths
        image_path = sample.image_paths[0]
        potential_paths = [
            self.cache_dir / image_path,
            Path(image_path),
            self.cache_dir / "images" / image_path,
        ]

        for path in potential_paths:
            if path.exists():
                return str(path)

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
