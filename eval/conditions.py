"""
Context builders for different evaluation conditions.

Implements context construction for:
- Hybrid: Top-k regions by patch-to-region relevance
- Page-only: Full page OCR text
- OCR-only (BM25): Top-k regions by BM25 similarity
- OCR-only (Dense): Top-k regions by dense embedding similarity
"""

import logging
import math
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from eval.dataset import OCRRegion, Sample

logger = logging.getLogger(__name__)


class ContextBuilder(ABC):
    """Abstract base class for context builders."""

    @abstractmethod
    def build_context(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """
        Build context string for LLM input.

        Args:
            sample: Evaluation sample
            query: Query string
            scored_regions: Pre-scored regions (for hybrid condition)
            **kwargs: Additional condition-specific parameters

        Returns:
            Context string to be passed to the LLM
        """
        pass

    @abstractmethod
    def get_retrieved_regions(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Get the regions used to build context (for metrics calculation).

        Returns:
            List of region dictionaries with bbox information
        """
        pass


class HybridContextBuilder(ContextBuilder):
    """
    Builds context using top-k regions by patch-to-region relevance.

    This is the primary condition testing the spatial grounding approach.
    """

    def __init__(
        self,
        top_k: int = 5,
        include_bbox: bool = True,
        include_score: bool = False,
    ):
        """
        Initialize hybrid context builder.

        Args:
            top_k: Maximum number of regions to include
            include_bbox: Whether to include bbox coordinates in context
            include_score: Whether to include relevance scores in context
        """
        self.top_k = top_k
        self.include_bbox = include_bbox
        self.include_score = include_score

    def build_context(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Build context from top-k scored regions."""
        if scored_regions is None:
            logger.warning("HybridContextBuilder requires scored_regions")
            return ""

        # Take top-k
        regions = scored_regions[: self.top_k]

        if not regions:
            return ""

        # Build context string
        context_parts = []
        for i, region in enumerate(regions):
            content = region.get("content", "")
            if not content:
                continue

            if self.include_bbox:
                bbox = region.get("bbox", [])
                bbox_str = f"[{bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f}]" if bbox else ""
                prefix = f"[Region {i + 1}, bbox={bbox_str}]"
            else:
                prefix = f"[Region {i + 1}]"

            if self.include_score:
                score = region.get("relevance_score", 0.0)
                prefix += f" (score={score:.3f})"

            context_parts.append(f"{prefix}: {content}")

        return "\n".join(context_parts)

    def get_retrieved_regions(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return top-k scored regions."""
        if scored_regions is None:
            return []
        return scored_regions[: self.top_k]


class PageOnlyContextBuilder(ContextBuilder):
    """
    Builds context using full page OCR text.

    Baseline condition with no spatial filtering.
    """

    def __init__(self, max_chars: Optional[int] = None):
        """
        Initialize page-only context builder.

        Args:
            max_chars: Maximum characters to include (None = no limit)
        """
        self.max_chars = max_chars

    def build_context(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Build context from full page text."""
        text = sample.full_page_text

        if not text and sample.ocr_regions:
            # Reconstruct from regions
            text = "\n".join(
                region.content if isinstance(region, OCRRegion) else region.get("content", "")
                for region in sample.ocr_regions
            )

        if self.max_chars and len(text) > self.max_chars:
            text = text[: self.max_chars] + "..."

        return text

    def get_retrieved_regions(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return all regions (full page)."""
        regions = []
        for region in sample.ocr_regions:
            if isinstance(region, OCRRegion):
                regions.append(region.to_dict())
            else:
                regions.append(region)
        return regions


class OCROnlyBM25ContextBuilder(ContextBuilder):
    """
    Builds context using top-k regions by BM25 similarity.

    Sparse retrieval baseline without spatial information.
    """

    def __init__(
        self,
        top_k: int = 5,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        """
        Initialize BM25 context builder.

        Args:
            top_k: Maximum number of regions to include
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
        """
        self.top_k = top_k
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing."""
        import re

        # Remove punctuation and split
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return text.split()

    def _compute_bm25_scores(
        self,
        query: str,
        regions: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Compute BM25 scores for each region."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(r, 0.0) for r in regions]

        # Tokenize all regions
        region_tokens = []
        for region in regions:
            content = region.get("content", "")
            tokens = self._tokenize(content)
            region_tokens.append(tokens)

        # Compute IDF for query terms
        n_docs = len(regions)
        doc_freqs = Counter()
        for tokens in region_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freqs[token] += 1

        # Average document length
        avg_dl = sum(len(tokens) for tokens in region_tokens) / max(n_docs, 1)

        # Compute BM25 score for each region
        scores = []
        for i, (region, tokens) in enumerate(zip(regions, region_tokens)):
            score = 0.0
            dl = len(tokens)
            token_freqs = Counter(tokens)

            for q_token in query_tokens:
                if q_token not in doc_freqs:
                    continue

                # IDF
                df = doc_freqs[q_token]
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

                # TF with saturation
                tf = token_freqs.get(q_token, 0)
                tf_component = (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / max(avg_dl, 1))
                )

                score += idf * tf_component

            scores.append((region, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def build_context(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Build context from top-k BM25-scored regions."""
        # Convert sample regions to dicts
        regions = []
        for region in sample.ocr_regions:
            if isinstance(region, OCRRegion):
                regions.append(region.to_dict())
            else:
                regions.append(region)

        if not regions:
            return ""

        # Score and rank
        scored = self._compute_bm25_scores(query, regions)
        top_k = scored[: self.top_k]

        # Build context
        context_parts = []
        for i, (region, score) in enumerate(top_k):
            content = region.get("content", "")
            if content:
                context_parts.append(f"[Region {i + 1}]: {content}")

        return "\n".join(context_parts)

    def get_retrieved_regions(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return top-k BM25-scored regions."""
        regions = []
        for region in sample.ocr_regions:
            if isinstance(region, OCRRegion):
                regions.append(region.to_dict())
            else:
                regions.append(region)

        if not regions:
            return []

        scored = self._compute_bm25_scores(query, regions)
        return [region for region, _ in scored[: self.top_k]]


class OCROnlyDenseContextBuilder(ContextBuilder):
    """
    Builds context using top-k regions by dense embedding similarity.

    Dense retrieval baseline for comparison.
    """

    def __init__(
        self,
        top_k: int = 5,
        embedding_model: str = "text-embedding-3-small",
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize dense context builder.

        Args:
            top_k: Maximum number of regions to include
            embedding_model: OpenAI embedding model to use
            openai_api_key: OpenAI API key (uses env var if not provided)
        """
        self.top_k = top_k
        self.embedding_model = embedding_model
        self.openai_api_key = openai_api_key
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            import os

            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai package required for dense retrieval")

            api_key = self.openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required for dense retrieval")

            self._client = OpenAI(api_key=api_key)

        return self._client

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts."""
        client = self._get_client()

        response = client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )

        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    def _compute_dense_scores(
        self,
        query: str,
        regions: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Compute cosine similarity scores for each region."""
        if not regions:
            return []

        # Get region contents
        contents = [region.get("content", "") for region in regions]
        valid_indices = [i for i, c in enumerate(contents) if c.strip()]

        if not valid_indices:
            return [(r, 0.0) for r in regions]

        valid_contents = [contents[i] for i in valid_indices]

        # Get embeddings
        all_texts = [query] + valid_contents
        embeddings = self._get_embeddings(all_texts)

        query_emb = embeddings[0]
        content_embs = embeddings[1:]

        # Compute cosine similarities
        query_norm = query_emb / np.linalg.norm(query_emb)
        content_norms = content_embs / np.linalg.norm(content_embs, axis=1, keepdims=True)
        similarities = content_norms @ query_norm

        # Map back to all regions
        scores = []
        valid_idx = 0
        for i, region in enumerate(regions):
            if i in valid_indices:
                scores.append((region, float(similarities[valid_idx])))
                valid_idx += 1
            else:
                scores.append((region, 0.0))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def build_context(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Build context from top-k dense-scored regions."""
        regions = []
        for region in sample.ocr_regions:
            if isinstance(region, OCRRegion):
                regions.append(region.to_dict())
            else:
                regions.append(region)

        if not regions:
            return ""

        # Score and rank
        scored = self._compute_dense_scores(query, regions)
        top_k = scored[: self.top_k]

        # Build context
        context_parts = []
        for i, (region, score) in enumerate(top_k):
            content = region.get("content", "")
            if content:
                context_parts.append(f"[Region {i + 1}]: {content}")

        return "\n".join(context_parts)

    def get_retrieved_regions(
        self,
        sample: Sample,
        query: str,
        scored_regions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return top-k dense-scored regions."""
        regions = []
        for region in sample.ocr_regions:
            if isinstance(region, OCRRegion):
                regions.append(region.to_dict())
            else:
                regions.append(region)

        if not regions:
            return []

        scored = self._compute_dense_scores(query, regions)
        return [region for region, _ in scored[: self.top_k]]


# Convenience aliases
CONDITION_BUILDERS = {
    "hybrid": HybridContextBuilder,
    "page_only": PageOnlyContextBuilder,
    "ocr_bm25": OCROnlyBM25ContextBuilder,
    "ocr_dense": OCROnlyDenseContextBuilder,
}


def get_context_builder(
    condition: str,
    **kwargs,
) -> ContextBuilder:
    """
    Factory function to get a context builder by name.

    Args:
        condition: Condition name ('hybrid', 'page_only', 'ocr_bm25', 'ocr_dense')
        **kwargs: Arguments to pass to the builder constructor

    Returns:
        ContextBuilder instance
    """
    if condition not in CONDITION_BUILDERS:
        raise ValueError(f"Unknown condition: {condition}. Available: {list(CONDITION_BUILDERS.keys())}")

    return CONDITION_BUILDERS[condition](**kwargs)
