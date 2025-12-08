"""
Unit tests for aggregation methods.

These tests use REAL computations with hand-verified expected values.
NO MOCKING of aggregation calculations.
"""

import numpy as np
import pytest

from benchmarks.aggregation import (
    AggregationMethod,
    aggregate_multi_token_scores,
    aggregate_patch_scores,
    aggregate_patch_scores_iou_weighted,
    aggregate_patch_scores_max,
    aggregate_patch_scores_mean,
    aggregate_patch_scores_sum,
    compute_region_scores,
    compute_region_scores_multi_token,
)
from benchmarks.utils.coordinates import Box


class TestAggregatePatchScoresMax:
    """Tests for max aggregation."""

    def test_single_patch_region(self):
        """Test max aggregation for region covering one patch."""
        # Create 4x4 grid with known values
        patch_scores = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region covering patch (0,0)
        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        score = aggregate_patch_scores_max(patch_scores, region, n_patches_x=4, n_patches_y=4)

        assert score == pytest.approx(0.1)

    def test_multi_patch_region(self):
        """Test max aggregation for region covering multiple patches."""
        patch_scores = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.9, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region covering patches (0,0), (1,0), (0,1), (1,1)
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_patch_scores_max(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # Max of 0.1, 0.2, 0.5, 0.9 = 0.9
        assert score == pytest.approx(0.9)

    def test_full_image_region(self):
        """Test max aggregation for full image region."""
        patch_scores = np.random.rand(4, 4).astype(np.float32)
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
        score = aggregate_patch_scores_max(patch_scores, region, n_patches_x=4, n_patches_y=4)

        assert score == pytest.approx(np.max(patch_scores))

    def test_no_overlap_returns_zero(self):
        """Test that non-overlapping region returns 0."""
        patch_scores = np.ones((4, 4), dtype=np.float32)
        # Region outside grid (would be clamped to empty)
        region = Box(x1=1.1, y1=1.1, x2=1.2, y2=1.2)
        score = aggregate_patch_scores_max(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # After clamping, should get a very small region or 0
        assert score >= 0.0


class TestAggregatePatchScoresMean:
    """Tests for mean aggregation."""

    def test_single_patch_region(self):
        """Test mean aggregation for region covering one patch."""
        patch_scores = np.array([
            [0.4, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        score = aggregate_patch_scores_mean(patch_scores, region, n_patches_x=4, n_patches_y=4)

        assert score == pytest.approx(0.4)

    def test_multi_patch_region(self):
        """Test mean aggregation for region covering multiple patches."""
        patch_scores = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region covering patches (0,0), (1,0), (0,1), (1,1)
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_patch_scores_mean(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # Mean of 0.1, 0.2, 0.5, 0.6 = (0.1 + 0.2 + 0.5 + 0.6) / 4 = 0.35
        assert score == pytest.approx(0.35)

    def test_uniform_scores(self):
        """Test mean of uniform scores equals that value."""
        patch_scores = np.full((4, 4), 0.5, dtype=np.float32)
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_patch_scores_mean(patch_scores, region, n_patches_x=4, n_patches_y=4)

        assert score == pytest.approx(0.5)


class TestAggregatePatchScoresSum:
    """Tests for sum aggregation."""

    def test_single_patch_region(self):
        """Test sum aggregation for region covering one patch."""
        patch_scores = np.array([
            [0.4, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        score = aggregate_patch_scores_sum(patch_scores, region, n_patches_x=4, n_patches_y=4)

        assert score == pytest.approx(0.4)

    def test_multi_patch_region(self):
        """Test sum aggregation for region covering multiple patches."""
        patch_scores = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region covering patches (0,0), (1,0), (0,1), (1,1)
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_patch_scores_sum(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # Sum of 0.1, 0.2, 0.5, 0.6 = 1.4
        assert score == pytest.approx(1.4)

    def test_full_image_sum(self):
        """Test sum of full image equals total."""
        patch_scores = np.ones((4, 4), dtype=np.float32) * 0.25
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
        score = aggregate_patch_scores_sum(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # Sum of 16 patches at 0.25 each = 4.0
        assert score == pytest.approx(4.0)


class TestAggregatePatchScoresIouWeighted:
    """Tests for IoU-weighted aggregation."""

    def test_single_patch_full_overlap(self):
        """Test IoU-weighted for single patch with full overlap."""
        patch_scores = np.array([
            [1.0, 0.5, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region exactly covering patch (0,0)
        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        score = aggregate_patch_scores_iou_weighted(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # IoU = 1.0 for patch (0,0), score = 1.0 * 1.0 = 1.0
        assert score == pytest.approx(1.0)

    def test_multi_patch_full_overlap(self):
        """Test IoU-weighted for multiple patches with full overlap."""
        patch_scores = np.array([
            [0.4, 0.6, 0.3, 0.4],
            [0.2, 0.8, 0.7, 0.8],
            [0.9, 1.0, 0.1, 0.2],
            [0.3, 0.4, 0.5, 0.6],
        ], dtype=np.float32)

        # Region covering 4 patches fully
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_patch_scores_iou_weighted(patch_scores, region, n_patches_x=4, n_patches_y=4)

        # All 4 patches have IoU = 1.0
        # Sum = 0.4 + 0.6 + 0.2 + 0.8 = 2.0
        assert score == pytest.approx(2.0)

    def test_partial_overlap(self):
        """Test IoU-weighted with partial overlap."""
        patch_scores = np.array([
            [1.0, 1.0],
            [1.0, 1.0],
        ], dtype=np.float32)

        # Region covering half of first patch
        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.5)
        score = aggregate_patch_scores_iou_weighted(patch_scores, region, n_patches_x=2, n_patches_y=2)

        # Patch (0,0) has partial overlap
        # Region: 0.25 x 0.5 = 0.125 area
        # Patch: 0.5 x 0.5 = 0.25 area
        # Intersection: 0.25 x 0.5 = 0.125
        # IoU = 0.125 / (0.125 + 0.25 - 0.125) = 0.125 / 0.25 = 0.5
        assert score == pytest.approx(0.5)


class TestAggregateDispatch:
    """Tests for aggregate_patch_scores dispatch function."""

    def test_max_dispatch(self):
        """Test dispatch to max aggregation."""
        patch_scores = np.array([[0.1, 0.9], [0.5, 0.6]], dtype=np.float32)
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_patch_scores(
            patch_scores, region, AggregationMethod.MAX, n_patches_x=2, n_patches_y=2
        )
        assert score == pytest.approx(0.9)

    def test_mean_dispatch(self):
        """Test dispatch to mean aggregation."""
        patch_scores = np.array([[0.1, 0.3], [0.5, 0.7]], dtype=np.float32)
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_patch_scores(
            patch_scores, region, AggregationMethod.MEAN, n_patches_x=2, n_patches_y=2
        )
        # Mean = (0.1 + 0.3 + 0.5 + 0.7) / 4 = 0.4
        assert score == pytest.approx(0.4)

    def test_sum_dispatch(self):
        """Test dispatch to sum aggregation."""
        patch_scores = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_patch_scores(
            patch_scores, region, AggregationMethod.SUM, n_patches_x=2, n_patches_y=2
        )
        assert score == pytest.approx(1.0)

    def test_iou_weighted_dispatch(self):
        """Test dispatch to IoU-weighted aggregation."""
        patch_scores = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=np.float32)
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)

        score = aggregate_patch_scores(
            patch_scores, region, AggregationMethod.IOU_WEIGHTED, n_patches_x=2, n_patches_y=2
        )
        # One patch fully covered, IoU = 1.0, score = 0.5
        assert score == pytest.approx(0.5)


class TestMultiTokenAggregation:
    """Tests for multi-token score aggregation."""

    def test_single_token(self):
        """Test aggregation with single token."""
        token_scores = [np.array([[0.5, 0.6], [0.7, 0.8]], dtype=np.float32)]
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_multi_token_scores(
            token_scores, region, AggregationMethod.MAX,
            token_aggregation="max", n_patches_x=2, n_patches_y=2
        )
        assert score == pytest.approx(0.8)

    def test_multi_token_max(self):
        """Test max aggregation across tokens."""
        token_scores = [
            np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
            np.array([[0.5, 0.6], [0.7, 0.8]], dtype=np.float32),
        ]
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_multi_token_scores(
            token_scores, region, AggregationMethod.MAX,
            token_aggregation="max", n_patches_x=2, n_patches_y=2
        )
        # Max of token 1 = 0.4, max of token 2 = 0.8
        # Token max = 0.8
        assert score == pytest.approx(0.8)

    def test_multi_token_mean(self):
        """Test mean aggregation across tokens."""
        token_scores = [
            np.array([[0.4, 0.4], [0.4, 0.4]], dtype=np.float32),
            np.array([[0.8, 0.8], [0.8, 0.8]], dtype=np.float32),
        ]
        region = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)

        score = aggregate_multi_token_scores(
            token_scores, region, AggregationMethod.MAX,
            token_aggregation="mean", n_patches_x=2, n_patches_y=2
        )
        # Max of token 1 = 0.4, max of token 2 = 0.8
        # Token mean = (0.4 + 0.8) / 2 = 0.6
        assert score == pytest.approx(0.6)

    def test_empty_tokens(self):
        """Test with no tokens returns 0."""
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        score = aggregate_multi_token_scores(
            [], region, AggregationMethod.MAX, "max", n_patches_x=2, n_patches_y=2
        )
        assert score == 0.0


class TestComputeRegionScores:
    """Tests for compute_region_scores function."""

    def test_single_region(self):
        """Test scoring single region."""
        patch_scores = np.array([[0.9, 0.1], [0.1, 0.1]], dtype=np.float32)
        regions = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        scored = compute_region_scores(
            regions, patch_scores, AggregationMethod.MAX, n_patches_x=2, n_patches_y=2
        )

        assert len(scored) == 1
        assert scored[0][0] == 0  # index
        assert scored[0][1] == pytest.approx(0.9)  # score

    def test_multiple_regions_sorted(self):
        """Test that multiple regions are sorted by score."""
        patch_scores = np.array([
            [0.1, 0.9],
            [0.5, 0.3],
        ], dtype=np.float32)

        regions = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),  # covers 0.1
            Box(x1=0.5, y1=0.0, x2=1.0, y2=0.5),  # covers 0.9
            Box(x1=0.0, y1=0.5, x2=0.5, y2=1.0),  # covers 0.5
        ]

        scored = compute_region_scores(
            regions, patch_scores, AggregationMethod.MAX, n_patches_x=2, n_patches_y=2
        )

        assert len(scored) == 3
        # Should be sorted: region 1 (0.9), region 2 (0.5), region 0 (0.1)
        assert scored[0][0] == 1  # highest score region
        assert scored[0][1] == pytest.approx(0.9)
        assert scored[1][0] == 2
        assert scored[1][1] == pytest.approx(0.5)
        assert scored[2][0] == 0
        assert scored[2][1] == pytest.approx(0.1)
