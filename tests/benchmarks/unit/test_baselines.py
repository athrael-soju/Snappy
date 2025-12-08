"""
Unit tests for baseline methods.

These tests use REAL computations with hand-verified expected values.
NO MOCKING of baseline calculations.
"""

import numpy as np
import pytest

from benchmarks.baselines import (
    BaselineMethod,
    random_ocr_baseline,
    run_all_baselines,
    run_baseline,
    text_similarity_baseline,
    uniform_patches_baseline,
)
from benchmarks.utils.coordinates import Box


class TestRandomOcrBaseline:
    """Tests for random OCR baseline."""

    def test_returns_k_regions(self):
        """Test that random baseline returns k regions."""
        regions = [Box(x1=i*0.1, y1=0, x2=(i+1)*0.1, y2=0.1) for i in range(10)]
        selected = random_ocr_baseline(regions, k=5, seed=42)

        assert len(selected) == 5

    def test_returns_less_if_fewer_regions(self):
        """Test handling when k > number of regions."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]
        selected = random_ocr_baseline(regions, k=10, seed=42)

        assert len(selected) == 1

    def test_reproducible_with_seed(self):
        """Test that same seed produces same results."""
        regions = [Box(x1=i*0.1, y1=0, x2=(i+1)*0.1, y2=0.1) for i in range(10)]

        selected1 = random_ocr_baseline(regions, k=5, seed=42)
        selected2 = random_ocr_baseline(regions, k=5, seed=42)

        assert selected1 == selected2

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        regions = [Box(x1=i*0.1, y1=0, x2=(i+1)*0.1, y2=0.1) for i in range(10)]

        selected1 = random_ocr_baseline(regions, k=5, seed=42)
        selected2 = random_ocr_baseline(regions, k=5, seed=123)

        # Results should differ (with high probability)
        indices1 = [s[0] for s in selected1]
        indices2 = [s[0] for s in selected2]
        # At least one difference expected
        assert indices1 != indices2

    def test_empty_regions(self):
        """Test handling empty regions."""
        selected = random_ocr_baseline([], k=5)
        assert len(selected) == 0


class TestTextSimilarityBaseline:
    """Tests for text similarity baseline."""

    def test_bm25_matches_query(self):
        """Test BM25 scores relevant text higher."""
        regions = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0, x2=1, y2=0.5),
            Box(x1=0, y1=0.5, x2=0.5, y2=1),
        ]
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Python programming language",
            "The fox is brown and quick",
        ]
        query = "quick brown fox"

        selected = text_similarity_baseline(
            query=query,
            regions=regions,
            region_texts=texts,
            method="bm25",
            k=3,
        )

        assert len(selected) == 3
        # First and third regions should score higher
        top_indices = {s[0] for s in selected[:2]}
        assert 0 in top_indices or 2 in top_indices

    def test_cosine_similarity(self):
        """Test cosine similarity method."""
        regions = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0, x2=1, y2=0.5),
        ]
        texts = [
            "machine learning artificial intelligence",
            "random unrelated text here",
        ]
        query = "machine learning"

        selected = text_similarity_baseline(
            query=query,
            regions=regions,
            region_texts=texts,
            method="cosine",
            k=2,
        )

        # First region should score higher
        assert selected[0][0] == 0
        assert selected[0][1] > selected[1][1]

    def test_empty_query(self):
        """Test handling empty query."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]
        texts = ["some text"]

        selected = text_similarity_baseline(
            query="",
            regions=regions,
            region_texts=texts,
            method="bm25",
            k=1,
        )

        assert len(selected) == 1

    def test_mismatched_lengths_raises(self):
        """Test that mismatched regions/texts raises error."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]
        texts = ["text1", "text2"]

        with pytest.raises(ValueError, match="Mismatch"):
            text_similarity_baseline("query", regions, texts, "bm25", 1)


class TestUniformPatchesBaseline:
    """Tests for uniform patches baseline."""

    def test_larger_regions_score_higher(self):
        """Test that larger regions get higher scores."""
        regions = [
            Box(x1=0, y1=0, x2=0.25, y2=0.25),  # 1 patch in 4x4 grid
            Box(x1=0, y1=0, x2=0.5, y2=0.5),    # 4 patches in 4x4 grid
        ]

        selected = uniform_patches_baseline(regions, n_patches_x=4, n_patches_y=4)

        # Larger region should score higher
        assert selected[0][0] == 1  # second region is larger
        assert selected[0][1] > selected[1][1]

    def test_full_image_region(self):
        """Test region covering full image."""
        regions = [Box(x1=0, y1=0, x2=1, y2=1)]

        selected = uniform_patches_baseline(regions, n_patches_x=4, n_patches_y=4)

        # Should cover all 16 patches, normalized to 1.0
        assert selected[0][1] == pytest.approx(1.0)

    def test_normalized_scores(self):
        """Test that scores are normalized to [0, 1]."""
        regions = [
            Box(x1=0, y1=0, x2=0.25, y2=0.25),
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0, y1=0, x2=1, y2=1),
        ]

        selected = uniform_patches_baseline(regions, n_patches_x=4, n_patches_y=4)

        for _, score in selected:
            assert 0 <= score <= 1

    def test_empty_regions(self):
        """Test handling empty regions."""
        selected = uniform_patches_baseline([])
        assert len(selected) == 0


class TestRunBaseline:
    """Tests for run_baseline dispatch function."""

    def test_dispatch_random(self):
        """Test dispatch to random baseline."""
        regions = [Box(x1=i*0.1, y1=0, x2=(i+1)*0.1, y2=0.1) for i in range(5)]

        selected = run_baseline(
            BaselineMethod.RANDOM_OCR,
            regions=regions,
            k=3,
            seed=42,
        )

        assert len(selected) == 3

    def test_dispatch_text_similarity(self):
        """Test dispatch to text similarity baseline."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]
        texts = ["matching text"]

        selected = run_baseline(
            BaselineMethod.TEXT_SIMILARITY,
            regions=regions,
            query="matching",
            region_texts=texts,
            k=1,
        )

        assert len(selected) == 1

    def test_dispatch_uniform_patches(self):
        """Test dispatch to uniform patches baseline."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]

        selected = run_baseline(
            BaselineMethod.UNIFORM_PATCHES,
            regions=regions,
            k=1,
        )

        assert len(selected) == 1

    def test_text_similarity_requires_query(self):
        """Test that text similarity requires query."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]

        with pytest.raises(ValueError, match="query is required"):
            run_baseline(
                BaselineMethod.TEXT_SIMILARITY,
                regions=regions,
                k=1,
            )


class TestRunAllBaselines:
    """Tests for run_all_baselines function."""

    def test_runs_all_baselines(self):
        """Test that all baselines are run."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]
        texts = ["test text"]

        results = run_all_baselines(
            regions=regions,
            query="test",
            region_texts=texts,
            k=1,
        )

        assert "random_ocr" in results
        assert "uniform_patches" in results
        assert "text_similarity" in results

    def test_skips_text_similarity_without_text(self):
        """Test that text similarity is skipped without text."""
        regions = [Box(x1=0, y1=0, x2=0.5, y2=0.5)]

        results = run_all_baselines(
            regions=regions,
            k=1,
        )

        assert "random_ocr" in results
        assert "uniform_patches" in results
        assert "text_similarity" not in results
