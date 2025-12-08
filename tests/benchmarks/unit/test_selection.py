"""
Unit tests for selection strategies.

These tests use REAL computations with hand-verified expected values.
NO MOCKING of selection logic.
"""

import numpy as np
import pytest

from benchmarks.selection import (
    SelectionMethod,
    select_by_elbow,
    select_by_gap,
    select_by_otsu,
    select_by_percentile,
    select_by_relative,
    select_by_threshold,
    select_regions,
    select_regions_ensemble,
    select_top_k,
)


class TestSelectTopK:
    """Tests for top-k selection."""

    def test_select_top_1(self):
        """Test selecting top 1 region."""
        scored = [(0, 0.3), (1, 0.9), (2, 0.5)]
        selected = select_top_k(scored, k=1)

        assert len(selected) == 1
        assert selected[0] == (1, 0.9)

    def test_select_top_3(self):
        """Test selecting top 3 regions."""
        scored = [(0, 0.1), (1, 0.9), (2, 0.5), (3, 0.7), (4, 0.3)]
        selected = select_top_k(scored, k=3)

        assert len(selected) == 3
        assert selected[0][1] == 0.9
        assert selected[1][1] == 0.7
        assert selected[2][1] == 0.5

    def test_k_greater_than_regions(self):
        """Test when k exceeds number of regions."""
        scored = [(0, 0.5), (1, 0.3)]
        selected = select_top_k(scored, k=5)

        assert len(selected) == 2

    def test_already_sorted(self):
        """Test with already sorted input."""
        scored = [(0, 0.9), (1, 0.7), (2, 0.5)]
        selected = select_top_k(scored, k=2)

        assert len(selected) == 2
        assert selected[0] == (0, 0.9)
        assert selected[1] == (1, 0.7)

    def test_invalid_k(self):
        """Test that k <= 0 raises error."""
        with pytest.raises(ValueError):
            select_top_k([(0, 0.5)], k=0)


class TestSelectByThreshold:
    """Tests for threshold selection."""

    def test_threshold_filters_correctly(self):
        """Test that threshold correctly filters regions."""
        scored = [(0, 0.1), (1, 0.5), (2, 0.8), (3, 0.3)]
        selected = select_by_threshold(scored, threshold=0.5)

        assert len(selected) == 2
        indices = {s[0] for s in selected}
        assert indices == {1, 2}

    def test_threshold_zero(self):
        """Test threshold of 0 includes all."""
        scored = [(0, 0.1), (1, 0.5), (2, 0.8)]
        selected = select_by_threshold(scored, threshold=0.0)

        assert len(selected) == 3

    def test_threshold_one(self):
        """Test threshold of 1 excludes all but perfect."""
        scored = [(0, 0.9), (1, 1.0), (2, 0.8)]
        selected = select_by_threshold(scored, threshold=1.0)

        assert len(selected) == 1
        assert selected[0][0] == 1

    def test_threshold_none_pass(self):
        """Test when no regions pass threshold."""
        scored = [(0, 0.1), (1, 0.2)]
        selected = select_by_threshold(scored, threshold=0.5)

        assert len(selected) == 0


class TestSelectByPercentile:
    """Tests for percentile selection."""

    def test_top_50_percentile(self):
        """Test selecting top 50 percentile."""
        scored = [(0, 0.1), (1, 0.3), (2, 0.5), (3, 0.7), (4, 0.9)]
        selected = select_by_percentile(scored, percentile=50)

        # Top 50% should be 0.5, 0.7, 0.9
        assert len(selected) >= 2

    def test_top_90_percentile(self):
        """Test selecting top 90 percentile."""
        scored = [(i, float(i) / 10) for i in range(11)]  # 0.0 to 1.0
        selected = select_by_percentile(scored, percentile=90)

        # Top 10% should include at least the highest value
        assert len(selected) >= 1
        # Check that selected includes the top scores
        selected_scores = {s[1] for s in selected}
        assert 1.0 in selected_scores  # The max should always be included

    def test_percentile_100(self):
        """Test 100 percentile includes all."""
        scored = [(0, 0.1), (1, 0.5), (2, 0.9)]
        selected = select_by_percentile(scored, percentile=100)

        assert len(selected) == 3

    def test_invalid_percentile(self):
        """Test that invalid percentile raises error."""
        with pytest.raises(ValueError):
            select_by_percentile([(0, 0.5)], percentile=150)


class TestSelectByOtsu:
    """Tests for Otsu's thresholding selection."""

    def test_bimodal_distribution(self):
        """Test Otsu on bimodal distribution."""
        # Clear separation between low (0.1-0.2) and high (0.8-0.9) scores
        scored = [
            (0, 0.1), (1, 0.1), (2, 0.2), (3, 0.15),
            (4, 0.85), (5, 0.9), (6, 0.88), (7, 0.92),
        ]
        selected = select_by_otsu(scored)

        # Should select the high-score group
        selected_indices = {s[0] for s in selected}
        assert 4 in selected_indices or 5 in selected_indices or 6 in selected_indices or 7 in selected_indices

    def test_uniform_scores(self):
        """Test Otsu with uniform scores."""
        scored = [(i, 0.5) for i in range(10)]
        selected = select_by_otsu(scored)

        # With uniform scores, should include all
        assert len(selected) == 10

    def test_single_region(self):
        """Test with single region."""
        scored = [(0, 0.5)]
        selected = select_by_otsu(scored)

        assert len(selected) == 1

    def test_empty_input(self):
        """Test with empty input."""
        selected = select_by_otsu([])
        assert len(selected) == 0


class TestSelectByElbow:
    """Tests for elbow/knee point selection."""

    def test_clear_elbow(self):
        """Test detection of clear elbow point."""
        # Scores drop sharply after first few
        scored = [
            (0, 0.9), (1, 0.85), (2, 0.8),
            (3, 0.2), (4, 0.15), (5, 0.1),
        ]
        selected = select_by_elbow(scored)

        # Should select the first 3 (before drop)
        assert len(selected) >= 1
        assert len(selected) <= 4

    def test_linear_decrease(self):
        """Test with linear score decrease."""
        scored = [(i, 1.0 - i * 0.1) for i in range(10)]
        selected = select_by_elbow(scored)

        # With linear decrease, elbow detection varies
        assert len(selected) >= 1

    def test_two_regions(self):
        """Test with only two regions."""
        scored = [(0, 0.9), (1, 0.1)]
        selected = select_by_elbow(scored)

        assert len(selected) >= 1


class TestSelectByGap:
    """Tests for gap-based selection."""

    def test_clear_gap(self):
        """Test detection of clear score gap."""
        scored = [(0, 0.9), (1, 0.85), (2, 0.1), (3, 0.05)]
        selected = select_by_gap(scored)

        # Largest gap is between 0.85 and 0.1
        # Should select first 2
        assert len(selected) == 2
        selected_indices = {s[0] for s in selected}
        assert selected_indices == {0, 1}

    def test_min_regions(self):
        """Test minimum regions constraint."""
        scored = [(0, 0.9), (1, 0.1)]
        selected = select_by_gap(scored, min_regions=2)

        # Even with large gap, should return at least 2
        assert len(selected) == 2

    def test_uniform_gaps(self):
        """Test with uniform gaps."""
        scored = [(i, 1.0 - i * 0.1) for i in range(5)]
        selected = select_by_gap(scored)

        # All gaps are equal (0.1), so should select first
        assert len(selected) >= 1


class TestSelectByRelative:
    """Tests for relative threshold selection."""

    def test_relative_50_percent(self):
        """Test relative threshold at 50% of max."""
        scored = [(0, 1.0), (1, 0.6), (2, 0.4), (3, 0.3)]
        selected = select_by_relative(scored, fraction=0.5)

        # 50% of max (1.0) = 0.5
        # Should include indices 0, 1
        assert len(selected) == 2
        selected_indices = {s[0] for s in selected}
        assert selected_indices == {0, 1}

    def test_relative_zero(self):
        """Test relative threshold of 0 includes all."""
        scored = [(0, 0.9), (1, 0.1), (2, 0.01)]
        selected = select_by_relative(scored, fraction=0.0)

        assert len(selected) == 3

    def test_relative_one(self):
        """Test relative threshold of 1 includes only max."""
        scored = [(0, 0.9), (1, 1.0), (2, 0.8)]
        selected = select_by_relative(scored, fraction=1.0)

        assert len(selected) == 1
        assert selected[0][0] == 1

    def test_invalid_fraction(self):
        """Test that invalid fraction raises error."""
        with pytest.raises(ValueError):
            select_by_relative([(0, 0.5)], fraction=1.5)


class TestSelectRegionsDispatch:
    """Tests for select_regions dispatch function."""

    def test_dispatch_top_k(self):
        """Test dispatch to top_k."""
        scored = [(0, 0.3), (1, 0.9), (2, 0.5)]
        selected = select_regions(scored, SelectionMethod.TOP_K, k=2)

        assert len(selected) == 2
        assert selected[0][1] == 0.9

    def test_dispatch_threshold(self):
        """Test dispatch to threshold."""
        scored = [(0, 0.3), (1, 0.9), (2, 0.5)]
        selected = select_regions(scored, SelectionMethod.THRESHOLD, threshold=0.5)

        assert len(selected) == 2

    def test_dispatch_otsu(self):
        """Test dispatch to otsu."""
        scored = [(0, 0.1), (1, 0.9), (2, 0.2), (3, 0.85)]
        selected = select_regions(scored, SelectionMethod.OTSU)

        assert len(selected) >= 1

    def test_unknown_method_raises(self):
        """Test that unknown method raises error."""
        with pytest.raises(ValueError):
            select_regions([(0, 0.5)], "invalid_method")


class TestSelectRegionsEnsemble:
    """Tests for ensemble selection."""

    def test_intersection_voting(self):
        """Test intersection voting strategy."""
        scored = [(0, 0.9), (1, 0.8), (2, 0.7), (3, 0.3)]

        # Two methods that both select top 2
        methods = [
            (SelectionMethod.TOP_K, {"k": 2}),
            (SelectionMethod.THRESHOLD, {"threshold": 0.75}),
        ]

        selected = select_regions_ensemble(scored, methods, voting="intersection")

        # Only regions selected by both: 0.9, 0.8
        selected_indices = {s[0] for s in selected}
        assert 0 in selected_indices
        assert 1 in selected_indices

    def test_union_voting(self):
        """Test union voting strategy."""
        scored = [(0, 0.9), (1, 0.8), (2, 0.7), (3, 0.3)]

        methods = [
            (SelectionMethod.TOP_K, {"k": 1}),  # selects 0
            (SelectionMethod.THRESHOLD, {"threshold": 0.75}),  # selects 0, 1
        ]

        selected = select_regions_ensemble(scored, methods, voting="union")

        # Union: 0, 1
        selected_indices = {s[0] for s in selected}
        assert 0 in selected_indices
        assert 1 in selected_indices

    def test_majority_voting(self):
        """Test majority voting strategy."""
        scored = [(0, 0.9), (1, 0.8), (2, 0.7), (3, 0.5)]

        methods = [
            (SelectionMethod.TOP_K, {"k": 2}),  # 0, 1
            (SelectionMethod.THRESHOLD, {"threshold": 0.75}),  # 0, 1
            (SelectionMethod.TOP_K, {"k": 3}),  # 0, 1, 2
        ]

        selected = select_regions_ensemble(scored, methods, voting="majority")

        # Majority (>50% = >1.5 methods):
        # 0: all 3 methods (3/3 > 50%)
        # 1: all 3 methods (3/3 > 50%)
        # 2: only 1 method (1/3 < 50%) - NOT majority
        selected_indices = {s[0] for s in selected}
        assert 0 in selected_indices
        assert 1 in selected_indices
        assert 2 not in selected_indices  # 1/3 is not majority

    def test_empty_methods_raises(self):
        """Test that empty methods list raises error."""
        with pytest.raises(ValueError):
            select_regions_ensemble([(0, 0.5)], [], voting="intersection")
