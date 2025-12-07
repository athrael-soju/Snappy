"""
Baseline methods for comparison against patch-to-region relevance propagation.

Baselines:
- Random OCR: Pick K random OCR regions (lower bound)
- Text similarity: BM25 or cosine similarity between query and region text
- Uniform patches: All patches score = 1.0 (measures value of learned relevance)
"""

import logging
import math
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .aggregation import RegionScore
from .utils.coordinates import NormalizedBox

logger = logging.getLogger(__name__)


@dataclass
class BaselineResult:
    """Result from a baseline method."""

    method: str
    region_scores: List[RegionScore]
    params: Dict[str, Any]


class BaselineGenerator:
    """
    Generates baseline predictions for comparison.

    Provides several baseline methods to establish lower bounds
    and measure the value of vision-based relevance.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the baseline generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def random_selection(
        self,
        regions: List[Dict[str, Any]],
        k: int = 5,
    ) -> BaselineResult:
        """
        Select K random OCR regions.

        Args:
            regions: List of OCR region dictionaries
            k: Number of regions to select

        Returns:
            BaselineResult with randomly selected regions
        """
        if not regions:
            return BaselineResult(
                method="random",
                region_scores=[],
                params={"k": k},
            )

        # Sample k regions (or all if fewer than k)
        sample_size = min(k, len(regions))
        selected = random.sample(regions, sample_size)

        # Assign random scores
        scores = np.random.random(sample_size)
        scores = scores / scores.sum()  # Normalize

        region_scores = []
        for region, score in zip(selected, scores):
            bbox = region.get("bbox", [0, 0, 0, 0])
            # Normalize bbox if needed
            normalized_bbox = self._normalize_bbox(bbox)

            region_scores.append(
                RegionScore(
                    region_id=region.get("id", ""),
                    score=float(score),
                    bbox=normalized_bbox,
                    content=region.get("content", ""),
                    label=region.get("label", ""),
                    patch_count=0,
                    raw_region=region,
                )
            )

        # Sort by score descending
        region_scores.sort(key=lambda x: x.score, reverse=True)

        return BaselineResult(
            method="random",
            region_scores=region_scores,
            params={"k": k, "seed": self.seed},
        )

    def text_similarity_bm25(
        self,
        regions: List[Dict[str, Any]],
        query: str,
        k: int = 5,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> BaselineResult:
        """
        Rank regions by BM25 text similarity with query.

        Args:
            regions: List of OCR region dictionaries with 'content' field
            query: Query text
            k: Number of top regions to return
            k1: BM25 term frequency saturation parameter
            b: BM25 length normalization parameter

        Returns:
            BaselineResult with text-similarity ranked regions
        """
        if not regions or not query:
            return BaselineResult(
                method="bm25",
                region_scores=[],
                params={"k": k, "k1": k1, "b": b},
            )

        # Tokenize query
        query_terms = self._tokenize(query)

        # Compute document frequencies and average length
        doc_lengths = []
        term_doc_freq: Dict[str, int] = {}

        for region in regions:
            content = region.get("content", "")
            tokens = self._tokenize(content)
            doc_lengths.append(len(tokens))

            unique_terms = set(tokens)
            for term in unique_terms:
                term_doc_freq[term] = term_doc_freq.get(term, 0) + 1

        avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1
        n_docs = len(regions)

        # Compute BM25 scores
        region_scores = []
        for region, doc_len in zip(regions, doc_lengths):
            content = region.get("content", "")
            tokens = self._tokenize(content)
            term_freq = self._term_frequency(tokens)

            score = 0.0
            for term in query_terms:
                if term not in term_freq:
                    continue

                tf = term_freq[term]
                df = term_doc_freq.get(term, 0)

                # IDF component
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

                # TF component with saturation
                tf_component = (tf * (k1 + 1)) / (
                    tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                )

                score += idf * tf_component

            bbox = region.get("bbox", [0, 0, 0, 0])
            normalized_bbox = self._normalize_bbox(bbox)

            region_scores.append(
                RegionScore(
                    region_id=region.get("id", ""),
                    score=float(score),
                    bbox=normalized_bbox,
                    content=region.get("content", ""),
                    label=region.get("label", ""),
                    patch_count=0,
                    raw_region=region,
                )
            )

        # Sort by score descending and take top k
        region_scores.sort(key=lambda x: x.score, reverse=True)
        region_scores = region_scores[:k]

        return BaselineResult(
            method="bm25",
            region_scores=region_scores,
            params={"k": k, "k1": k1, "b": b, "query": query},
        )

    def text_similarity_cosine(
        self,
        regions: List[Dict[str, Any]],
        query: str,
        k: int = 5,
    ) -> BaselineResult:
        """
        Rank regions by cosine similarity with query (TF-IDF vectors).

        Args:
            regions: List of OCR region dictionaries
            query: Query text
            k: Number of top regions to return

        Returns:
            BaselineResult with cosine-similarity ranked regions
        """
        if not regions or not query:
            return BaselineResult(
                method="cosine",
                region_scores=[],
                params={"k": k},
            )

        # Build vocabulary and compute IDF
        vocab: Dict[str, int] = {}
        doc_freq: Dict[str, int] = {}
        n_docs = len(regions) + 1  # Include query as a document

        # Process regions
        region_tokens = []
        for region in regions:
            tokens = self._tokenize(region.get("content", ""))
            region_tokens.append(tokens)

            unique = set(tokens)
            for term in unique:
                if term not in vocab:
                    vocab[term] = len(vocab)
                doc_freq[term] = doc_freq.get(term, 0) + 1

        # Process query
        query_tokens = self._tokenize(query)
        for term in set(query_tokens):
            if term not in vocab:
                vocab[term] = len(vocab)
            doc_freq[term] = doc_freq.get(term, 0) + 1

        # Compute IDF values
        idf = {}
        for term, df in doc_freq.items():
            idf[term] = math.log(n_docs / (df + 1)) + 1

        # Build query TF-IDF vector
        query_vec = self._tfidf_vector(query_tokens, vocab, idf)

        # Compute similarity for each region
        region_scores = []
        for region, tokens in zip(regions, region_tokens):
            region_vec = self._tfidf_vector(tokens, vocab, idf)
            similarity = self._cosine_similarity(query_vec, region_vec)

            bbox = region.get("bbox", [0, 0, 0, 0])
            normalized_bbox = self._normalize_bbox(bbox)

            region_scores.append(
                RegionScore(
                    region_id=region.get("id", ""),
                    score=float(similarity),
                    bbox=normalized_bbox,
                    content=region.get("content", ""),
                    label=region.get("label", ""),
                    patch_count=0,
                    raw_region=region,
                )
            )

        # Sort and take top k
        region_scores.sort(key=lambda x: x.score, reverse=True)
        region_scores = region_scores[:k]

        return BaselineResult(
            method="cosine",
            region_scores=region_scores,
            params={"k": k, "query": query, "vocab_size": len(vocab)},
        )

    def uniform_patches(
        self,
        regions: List[Dict[str, Any]],
        grid_x: int = 32,
        grid_y: int = 32,
    ) -> BaselineResult:
        """
        Score regions assuming all patches have equal relevance.

        This baseline measures the value of learned patch-level relevance
        by comparing against uniform scoring.

        Args:
            regions: List of OCR region dictionaries
            grid_x: Number of patches in x dimension
            grid_y: Number of patches in y dimension

        Returns:
            BaselineResult with uniformly-scored regions
        """
        if not regions:
            return BaselineResult(
                method="uniform_patches",
                region_scores=[],
                params={"grid_x": grid_x, "grid_y": grid_y},
            )

        # Create uniform heatmap
        uniform_heatmap = np.ones((grid_y, grid_x))

        # Import aggregator to reuse logic
        from .aggregation import PatchToRegionAggregator

        aggregator = PatchToRegionAggregator(
            grid_x=grid_x,
            grid_y=grid_y,
            default_method="iou_weighted",
        )

        region_scores = aggregator.aggregate(
            heatmap=uniform_heatmap,
            regions=regions,
            method="iou_weighted",
        )

        return BaselineResult(
            method="uniform_patches",
            region_scores=region_scores,
            params={"grid_x": grid_x, "grid_y": grid_y},
        )

    def center_bias(
        self,
        regions: List[Dict[str, Any]],
        grid_x: int = 32,
        grid_y: int = 32,
    ) -> BaselineResult:
        """
        Score regions using a center-biased prior.

        Important information often appears near the center of documents.

        Args:
            regions: List of OCR region dictionaries
            grid_x: Number of patches in x dimension
            grid_y: Number of patches in y dimension

        Returns:
            BaselineResult with center-biased scores
        """
        if not regions:
            return BaselineResult(
                method="center_bias",
                region_scores=[],
                params={"grid_x": grid_x, "grid_y": grid_y},
            )

        # Create center-biased heatmap (Gaussian-like)
        x = np.linspace(-1, 1, grid_x)
        y = np.linspace(-1, 1, grid_y)
        xx, yy = np.meshgrid(x, y)
        center_heatmap = np.exp(-(xx**2 + yy**2))

        from .aggregation import PatchToRegionAggregator

        aggregator = PatchToRegionAggregator(
            grid_x=grid_x,
            grid_y=grid_y,
            default_method="iou_weighted",
        )

        region_scores = aggregator.aggregate(
            heatmap=center_heatmap,
            regions=regions,
            method="iou_weighted",
        )

        return BaselineResult(
            method="center_bias",
            region_scores=region_scores,
            params={"grid_x": grid_x, "grid_y": grid_y},
        )

    def top_left_bias(
        self,
        regions: List[Dict[str, Any]],
    ) -> BaselineResult:
        """
        Score regions based on reading order (top-left first).

        Assumes important content appears earlier in the document.

        Args:
            regions: List of OCR region dictionaries

        Returns:
            BaselineResult with position-based scores
        """
        if not regions:
            return BaselineResult(
                method="top_left_bias",
                region_scores=[],
                params={},
            )

        region_scores = []
        for region in regions:
            bbox = region.get("bbox", [0, 0, 0, 0])
            normalized_bbox = self._normalize_bbox(bbox)

            # Score inversely proportional to position
            x1, y1, x2, y2 = normalized_bbox
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # Higher score for top-left regions
            score = 1.0 - (0.5 * center_x + 0.5 * center_y)

            region_scores.append(
                RegionScore(
                    region_id=region.get("id", ""),
                    score=float(score),
                    bbox=normalized_bbox,
                    content=region.get("content", ""),
                    label=region.get("label", ""),
                    patch_count=0,
                    raw_region=region,
                )
            )

        region_scores.sort(key=lambda x: x.score, reverse=True)

        return BaselineResult(
            method="top_left_bias",
            region_scores=region_scores,
            params={},
        )

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        if not text:
            return []
        text = text.lower()
        tokens = re.split(r"[^a-z0-9]+", text)
        return [t for t in tokens if t]

    def _term_frequency(self, tokens: List[str]) -> Dict[str, int]:
        """Compute term frequency from token list."""
        freq: Dict[str, int] = {}
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1
        return freq

    def _tfidf_vector(
        self,
        tokens: List[str],
        vocab: Dict[str, int],
        idf: Dict[str, float],
    ) -> np.ndarray:
        """Build TF-IDF vector for a document."""
        vec = np.zeros(len(vocab))
        tf = self._term_frequency(tokens)

        for term, freq in tf.items():
            if term in vocab:
                idx = vocab[term]
                vec[idx] = freq * idf.get(term, 1.0)

        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))

    def _normalize_bbox(
        self,
        bbox: List[float],
    ) -> Tuple[float, float, float, float]:
        """Normalize bbox to [0, 1] space (assumes 0-999 DeepSeek format)."""
        if len(bbox) < 4:
            return (0.0, 0.0, 0.0, 0.0)

        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
        max_coord = max(x1, y1, x2, y2)

        if max_coord <= 1.0:
            return (x1, y1, x2, y2)
        elif max_coord <= 999:
            return (x1 / 999.0, y1 / 999.0, x2 / 999.0, y2 / 999.0)
        else:
            # Assume large pixel values - normalize by max
            return (x1 / max_coord, y1 / max_coord, x2 / max_coord, y2 / max_coord)

    def run_all_baselines(
        self,
        regions: List[Dict[str, Any]],
        query: str,
        k: int = 5,
    ) -> Dict[str, BaselineResult]:
        """
        Run all baseline methods.

        Args:
            regions: List of OCR region dictionaries
            query: Query text
            k: Number of regions to select

        Returns:
            Dictionary mapping method name to BaselineResult
        """
        return {
            "random": self.random_selection(regions, k),
            "bm25": self.text_similarity_bm25(regions, query, k),
            "cosine": self.text_similarity_cosine(regions, query, k),
            "uniform_patches": self.uniform_patches(regions),
            "center_bias": self.center_bias(regions),
            "top_left_bias": self.top_left_bias(regions),
        }
