"""
Baseline Methods for Benchmark Comparison.

This module implements baseline methods to compare against
the patch-to-region relevance propagation approach.

Baselines:
- random_ocr: Random OCR region selection
- text_similarity: BM25/cosine on OCR text
- uniform_patches: All patch scores = 1 (tests if learned scores matter)
"""

import math
import re
from collections import Counter
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from .utils.coordinates import Box


class BaselineMethod(str, Enum):
    """Available baseline methods."""

    RANDOM_OCR = "random_ocr"
    TEXT_SIMILARITY = "text_similarity"
    UNIFORM_PATCHES = "uniform_patches"


def random_ocr_baseline(
    regions: List[Box],
    k: int,
    seed: Optional[int] = None,
) -> List[Tuple[int, float]]:
    """
    Random OCR region selection baseline.

    This baseline provides a lower bound - if the method doesn't
    significantly beat random selection, the task may be trivial
    or the method is not learning meaningful relevance.

    Args:
        regions: List of OCR region boxes
        k: Number of regions to select
        seed: Optional random seed for reproducibility

    Returns:
        List of (region_index, score) tuples with random scores
    """
    if not regions:
        return []

    rng = np.random.default_rng(seed)

    # Assign random scores
    scores = rng.random(len(regions))

    # Sort by score descending
    scored_regions = [(i, float(scores[i])) for i in range(len(regions))]
    scored_regions.sort(key=lambda x: x[1], reverse=True)

    return scored_regions[:k]


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer for text similarity."""
    # Lowercase and split on non-alphanumeric
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens


def _compute_bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    doc_freq: Dict[str, int],
    avg_doc_len: float,
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """
    Compute BM25 score between query and document.

    Args:
        query_tokens: Tokenized query
        doc_tokens: Tokenized document
        doc_freq: Document frequency for each term
        avg_doc_len: Average document length
        n_docs: Total number of documents
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        BM25 score
    """
    score = 0.0
    doc_len = len(doc_tokens)
    term_freq = Counter(doc_tokens)

    for term in query_tokens:
        if term not in term_freq:
            continue

        tf = term_freq[term]
        df = doc_freq.get(term, 0)

        if df == 0:
            continue

        # IDF component
        idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

        # TF component with length normalization
        tf_norm = (tf * (k1 + 1)) / (
            tf + k1 * (1 - b + b * doc_len / avg_doc_len)
        )

        score += idf * tf_norm

    return score


def _compute_cosine_similarity(
    query_tokens: List[str],
    doc_tokens: List[str],
) -> float:
    """
    Compute cosine similarity between query and document.

    Args:
        query_tokens: Tokenized query
        doc_tokens: Tokenized document

    Returns:
        Cosine similarity score
    """
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)

    # Get all terms
    all_terms = set(query_counts.keys()) | set(doc_counts.keys())

    if not all_terms:
        return 0.0

    # Build vectors
    query_vec = np.array([query_counts.get(t, 0) for t in all_terms])
    doc_vec = np.array([doc_counts.get(t, 0) for t in all_terms])

    # Compute cosine similarity
    dot = np.dot(query_vec, doc_vec)
    norm_q = np.linalg.norm(query_vec)
    norm_d = np.linalg.norm(doc_vec)

    if norm_q == 0 or norm_d == 0:
        return 0.0

    return float(dot / (norm_q * norm_d))


def text_similarity_baseline(
    query: str,
    regions: List[Box],
    region_texts: List[str],
    method: str = "bm25",
    k: int = 5,
) -> List[Tuple[int, float]]:
    """
    Text similarity baseline using BM25 or cosine similarity.

    This baseline tests whether vision-based relevance adds value
    over simple text matching.

    Args:
        query: Query text
        regions: List of OCR region boxes
        region_texts: List of text content for each region
        method: Similarity method ('bm25' or 'cosine')
        k: Number of regions to return

    Returns:
        List of (region_index, score) tuples sorted by score
    """
    if not regions or not region_texts:
        return []

    if len(regions) != len(region_texts):
        raise ValueError(
            f"Mismatch between regions ({len(regions)}) "
            f"and texts ({len(region_texts)})"
        )

    query_tokens = _tokenize(query)

    if not query_tokens:
        # No query tokens - return uniform scores
        scored = [(i, 1.0 / len(regions)) for i in range(len(regions))]
        return scored[:k]

    # Tokenize all regions
    region_token_lists = [_tokenize(text) for text in region_texts]

    if method == "bm25":
        # Compute document frequencies
        doc_freq: Dict[str, int] = {}
        for tokens in region_token_lists:
            for term in set(tokens):
                doc_freq[term] = doc_freq.get(term, 0) + 1

        # Compute average document length
        avg_doc_len = np.mean([len(t) for t in region_token_lists]) if region_token_lists else 1.0

        # Score each region
        scores = []
        for tokens in region_token_lists:
            score = _compute_bm25_score(
                query_tokens,
                tokens,
                doc_freq,
                avg_doc_len,
                len(regions),
            )
            scores.append(score)

    elif method == "cosine":
        scores = [
            _compute_cosine_similarity(query_tokens, tokens)
            for tokens in region_token_lists
        ]
    else:
        raise ValueError(f"Unknown similarity method: {method}")

    # Create scored regions
    scored_regions = [(i, float(scores[i])) for i in range(len(regions))]
    scored_regions.sort(key=lambda x: x[1], reverse=True)

    return scored_regions[:k]


def uniform_patches_baseline(
    regions: List[Box],
    n_patches_x: int = 32,
    n_patches_y: int = 32,
) -> List[Tuple[int, float]]:
    """
    Uniform patches baseline - all patch scores = 1.

    This baseline tests whether learned patch similarity scores
    matter, or if simple spatial overlap is sufficient.

    Score = number of patches overlapping with region (normalized).

    Args:
        regions: List of OCR region boxes
        n_patches_x: Number of patches in x dimension
        n_patches_y: Number of patches in y dimension

    Returns:
        List of (region_index, score) tuples sorted by score
    """
    if not regions:
        return []

    patch_width = 1.0 / n_patches_x
    patch_height = 1.0 / n_patches_y

    scores = []
    for region in regions:
        # Count overlapping patches
        start_x = max(0, int(region.x1 / patch_width))
        end_x = min(n_patches_x, int(np.ceil(region.x2 / patch_width)))
        start_y = max(0, int(region.y1 / patch_height))
        end_y = min(n_patches_y, int(np.ceil(region.y2 / patch_height)))

        n_overlapping = (end_x - start_x) * (end_y - start_y)
        scores.append(n_overlapping)

    # Normalize scores
    max_score = max(scores) if scores else 1
    if max_score > 0:
        scores = [s / max_score for s in scores]

    # Create scored regions
    scored_regions = [(i, float(scores[i])) for i in range(len(regions))]
    scored_regions.sort(key=lambda x: x[1], reverse=True)

    return scored_regions


def run_baseline(
    method: BaselineMethod,
    regions: List[Box],
    query: Optional[str] = None,
    region_texts: Optional[List[str]] = None,
    k: int = 5,
    **kwargs,
) -> List[Tuple[int, float]]:
    """
    Run a baseline method.

    Args:
        method: Baseline method to run
        regions: List of OCR region boxes
        query: Query text (required for text_similarity)
        region_texts: Text content for regions (required for text_similarity)
        k: Number of regions to return
        **kwargs: Additional method-specific parameters

    Returns:
        List of (region_index, score) tuples
    """
    if method == BaselineMethod.RANDOM_OCR:
        return random_ocr_baseline(
            regions,
            k=k,
            seed=kwargs.get("seed"),
        )

    elif method == BaselineMethod.TEXT_SIMILARITY:
        if query is None:
            raise ValueError("query is required for text_similarity baseline")
        if region_texts is None:
            raise ValueError("region_texts is required for text_similarity baseline")

        return text_similarity_baseline(
            query=query,
            regions=regions,
            region_texts=region_texts,
            method=kwargs.get("similarity_method", "bm25"),
            k=k,
        )

    elif method == BaselineMethod.UNIFORM_PATCHES:
        result = uniform_patches_baseline(
            regions,
            n_patches_x=kwargs.get("n_patches_x", 32),
            n_patches_y=kwargs.get("n_patches_y", 32),
        )
        return result[:k]

    else:
        raise ValueError(f"Unknown baseline method: {method}")


def run_all_baselines(
    regions: List[Box],
    query: Optional[str] = None,
    region_texts: Optional[List[str]] = None,
    k: int = 5,
    **kwargs,
) -> Dict[str, List[Tuple[int, float]]]:
    """
    Run all baseline methods.

    Args:
        regions: List of OCR region boxes
        query: Query text
        region_texts: Text content for regions
        k: Number of regions to return per method
        **kwargs: Additional parameters

    Returns:
        Dict mapping baseline name to results
    """
    results = {}

    # Random baseline
    results[BaselineMethod.RANDOM_OCR.value] = run_baseline(
        BaselineMethod.RANDOM_OCR,
        regions,
        k=k,
        **kwargs,
    )

    # Uniform patches baseline
    results[BaselineMethod.UNIFORM_PATCHES.value] = run_baseline(
        BaselineMethod.UNIFORM_PATCHES,
        regions,
        k=k,
        **kwargs,
    )

    # Text similarity baseline (if text available)
    if query and region_texts:
        results[BaselineMethod.TEXT_SIMILARITY.value] = run_baseline(
            BaselineMethod.TEXT_SIMILARITY,
            regions,
            query=query,
            region_texts=region_texts,
            k=k,
            **kwargs,
        )

    return results
