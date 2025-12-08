"""
Regression tests with known-value validation.

These tests verify that computations produce EXACT expected values
for carefully constructed test cases. NO MOCKING allowed.

Each test case documents:
- Input data
- Expected output (hand-calculated)
- Mathematical derivation
"""

import numpy as np
import pytest

from benchmarks.aggregation import (
    aggregate_patch_scores_iou_weighted,
    aggregate_patch_scores_max,
    aggregate_patch_scores_mean,
    aggregate_patch_scores_sum,
)
from benchmarks.evaluation import (
    compute_average_precision,
    compute_iou_at_threshold,
    compute_mean_iou,
    compute_precision_at_k,
    compute_recall_at_k,
    match_hungarian,
    match_set_coverage,
)
from benchmarks.selection import select_by_otsu, select_top_k
from benchmarks.utils.coordinates import (
    Box,
    compute_iou,
    compute_iou_matrix,
    normalize_bbox_deepseek,
    normalize_bbox_pixels,
    patch_index_to_normalized_box,
    patches_to_region_iou_weights,
)


class TestKnownIoUValues:
    """Regression tests for IoU computation with known values."""

    def test_iou_identical_unit_square(self):
        """
        Test: Two identical unit squares

        Box A: (0, 0, 1, 1)
        Box B: (0, 0, 1, 1)

        Intersection = 1 * 1 = 1
        Union = 1 + 1 - 1 = 1
        IoU = 1 / 1 = 1.0
        """
        box_a = Box(x1=0, y1=0, x2=1, y2=1)
        box_b = Box(x1=0, y1=0, x2=1, y2=1)

        iou = compute_iou(box_a, box_b)

        assert iou == pytest.approx(1.0, abs=1e-10)

    def test_iou_half_overlap_horizontal(self):
        """
        Test: Two boxes with 50% horizontal overlap

        Box A: (0, 0, 0.5, 1) - left half
        Box B: (0.25, 0, 0.75, 1) - center half

        Area A = 0.5 * 1 = 0.5
        Area B = 0.5 * 1 = 0.5

        Intersection: (0.25, 0) to (0.5, 1)
        Intersection area = 0.25 * 1 = 0.25

        Union = 0.5 + 0.5 - 0.25 = 0.75
        IoU = 0.25 / 0.75 = 1/3 = 0.333...
        """
        box_a = Box(x1=0, y1=0, x2=0.5, y2=1)
        box_b = Box(x1=0.25, y1=0, x2=0.75, y2=1)

        iou = compute_iou(box_a, box_b)

        expected = 1 / 3
        assert iou == pytest.approx(expected, abs=1e-10)

    def test_iou_quarter_overlap(self):
        """
        Test: Two unit squares overlapping at corner

        Box A: (0, 0, 0.5, 0.5)
        Box B: (0.25, 0.25, 0.75, 0.75)

        Area A = 0.5 * 0.5 = 0.25
        Area B = 0.5 * 0.5 = 0.25

        Intersection: (0.25, 0.25) to (0.5, 0.5)
        Intersection area = 0.25 * 0.25 = 0.0625

        Union = 0.25 + 0.25 - 0.0625 = 0.4375
        IoU = 0.0625 / 0.4375 = 1/7 = 0.142857...
        """
        box_a = Box(x1=0, y1=0, x2=0.5, y2=0.5)
        box_b = Box(x1=0.25, y1=0.25, x2=0.75, y2=0.75)

        iou = compute_iou(box_a, box_b)

        expected = 0.0625 / 0.4375  # = 1/7
        assert iou == pytest.approx(expected, abs=1e-10)

    def test_iou_matrix_2x2(self):
        """
        Test: 2x2 IoU matrix with known values

        Predictions:
        P0: (0, 0, 0.5, 0.5) - top-left quadrant
        P1: (0.5, 0.5, 1, 1) - bottom-right quadrant

        Ground Truth:
        G0: (0, 0, 0.5, 0.5) - identical to P0
        G1: (0.5, 0.5, 1, 1) - identical to P1

        Expected IoU matrix:
        [[1.0, 0.0],
         [0.0, 1.0]]
        """
        preds = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1, y2=1),
        ]
        gts = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1, y2=1),
        ]

        matrix = compute_iou_matrix(preds, gts)

        expected = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])
        np.testing.assert_array_almost_equal(matrix, expected, decimal=10)


class TestKnownCoordinateNormalization:
    """Regression tests for coordinate normalization."""

    def test_deepseek_coords_center(self):
        """
        Test: DeepSeek coordinates for center region

        Input: (250, 250, 750, 750) on 0-999 scale
        Expected: (250/999, 250/999, 750/999, 750/999)
                = (0.2502..., 0.2502..., 0.7507..., 0.7507...)
        """
        box = normalize_bbox_deepseek((250, 250, 750, 750))

        assert box.x1 == pytest.approx(250 / 999, abs=1e-10)
        assert box.y1 == pytest.approx(250 / 999, abs=1e-10)
        assert box.x2 == pytest.approx(750 / 999, abs=1e-10)
        assert box.y2 == pytest.approx(750 / 999, abs=1e-10)

    def test_pixel_coords_half_image(self):
        """
        Test: Pixel coordinates for half-image region

        Input: (0, 0, 500, 400) on 1000x800 image
        Expected: (0, 0, 0.5, 0.5)
        """
        box = normalize_bbox_pixels((0, 0, 500, 400), 1000, 800)

        assert box.x1 == pytest.approx(0.0, abs=1e-10)
        assert box.y1 == pytest.approx(0.0, abs=1e-10)
        assert box.x2 == pytest.approx(0.5, abs=1e-10)
        assert box.y2 == pytest.approx(0.5, abs=1e-10)

    def test_patch_index_known_positions(self):
        """
        Test: Patch indices to boxes for 4x4 grid

        Patch 0 (0,0): (0, 0, 0.25, 0.25)
        Patch 5 (1,1): (0.25, 0.25, 0.5, 0.5)
        Patch 15 (3,3): (0.75, 0.75, 1.0, 1.0)
        """
        # Patch 0
        box0 = patch_index_to_normalized_box(0, 4, 4)
        assert box0.x1 == pytest.approx(0.0, abs=1e-10)
        assert box0.y1 == pytest.approx(0.0, abs=1e-10)
        assert box0.x2 == pytest.approx(0.25, abs=1e-10)
        assert box0.y2 == pytest.approx(0.25, abs=1e-10)

        # Patch 5 (idx = 5, x = 5 % 4 = 1, y = 5 // 4 = 1)
        box5 = patch_index_to_normalized_box(5, 4, 4)
        assert box5.x1 == pytest.approx(0.25, abs=1e-10)
        assert box5.y1 == pytest.approx(0.25, abs=1e-10)
        assert box5.x2 == pytest.approx(0.5, abs=1e-10)
        assert box5.y2 == pytest.approx(0.5, abs=1e-10)

        # Patch 15 (idx = 15, x = 15 % 4 = 3, y = 15 // 4 = 3)
        box15 = patch_index_to_normalized_box(15, 4, 4)
        assert box15.x1 == pytest.approx(0.75, abs=1e-10)
        assert box15.y1 == pytest.approx(0.75, abs=1e-10)
        assert box15.x2 == pytest.approx(1.0, abs=1e-10)
        assert box15.y2 == pytest.approx(1.0, abs=1e-10)


class TestKnownAggregationValues:
    """Regression tests for aggregation with known values."""

    def test_aggregation_2x2_uniform(self):
        """
        Test: All aggregation methods on 2x2 uniform grid

        Patch scores:
        [[0.4, 0.6],
         [0.2, 0.8]]

        Region: Full image (0, 0, 1, 1)

        Max = 0.8
        Mean = (0.4 + 0.6 + 0.2 + 0.8) / 4 = 0.5
        Sum = 0.4 + 0.6 + 0.2 + 0.8 = 2.0
        IoU-weighted = 0.4*1 + 0.6*1 + 0.2*1 + 0.8*1 = 2.0 (all IoU=1)
        """
        scores = np.array([[0.4, 0.6], [0.2, 0.8]], dtype=np.float32)
        region = Box(x1=0, y1=0, x2=1, y2=1)

        max_score = aggregate_patch_scores_max(scores, region, 2, 2)
        mean_score = aggregate_patch_scores_mean(scores, region, 2, 2)
        sum_score = aggregate_patch_scores_sum(scores, region, 2, 2)
        iou_score = aggregate_patch_scores_iou_weighted(scores, region, 2, 2)

        assert max_score == pytest.approx(0.8, abs=1e-6)
        assert mean_score == pytest.approx(0.5, abs=1e-6)
        assert sum_score == pytest.approx(2.0, abs=1e-6)
        assert iou_score == pytest.approx(2.0, abs=1e-6)

    def test_iou_weighted_partial_overlap(self):
        """
        Test: IoU-weighted with partial patch overlap

        Patch scores (2x2 grid):
        [[1.0, 0.0],
         [0.0, 0.0]]

        Region: (0, 0, 0.25, 0.5) - covers left half of patch (0,0)

        Patch (0,0) box: (0, 0, 0.5, 0.5)
        Region: (0, 0, 0.25, 0.5)
        Intersection: (0, 0, 0.25, 0.5), area = 0.125
        Patch area: 0.25
        Region area: 0.125
        Union = 0.25 + 0.125 - 0.125 = 0.25
        IoU = 0.125 / 0.25 = 0.5

        IoU-weighted sum = 1.0 * 0.5 = 0.5
        """
        scores = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.float32)
        region = Box(x1=0, y1=0, x2=0.25, y2=0.5)

        iou_score = aggregate_patch_scores_iou_weighted(scores, region, 2, 2)

        assert iou_score == pytest.approx(0.5, abs=1e-6)


class TestKnownEvaluationMetrics:
    """Regression tests for evaluation metrics."""

    def test_precision_recall_known(self):
        """
        Test: P@K and R@K with known values

        Predictions (ranked by score):
        P0: (0, 0, 0.5, 0.5) - matches G0
        P1: (0.8, 0.8, 0.9, 0.9) - no match
        P2: (0.5, 0.5, 1, 1) - matches G1

        Ground Truth:
        G0: (0, 0, 0.5, 0.5)
        G1: (0.5, 0.5, 1, 1)

        At K=1: P=1/1=1.0, R=1/2=0.5 (P0 matches G0)
        At K=2: P=1/2=0.5, R=1/2=0.5 (P1 misses)
        At K=3: P=2/3=0.667, R=2/2=1.0 (P2 matches G1)
        """
        preds = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),      # matches G0
            Box(x1=0.8, y1=0.8, x2=0.9, y2=0.9),  # no match
            Box(x1=0.5, y1=0.5, x2=1, y2=1),      # matches G1
        ]
        gts = [
            Box(x1=0, y1=0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1, y2=1),
        ]

        # K=1
        p1 = compute_precision_at_k(preds, gts, k=1, threshold=0.9)
        r1 = compute_recall_at_k(preds, gts, k=1, threshold=0.9)
        assert p1 == pytest.approx(1.0, abs=1e-10)
        assert r1 == pytest.approx(0.5, abs=1e-10)

        # K=2
        p2 = compute_precision_at_k(preds, gts, k=2, threshold=0.9)
        r2 = compute_recall_at_k(preds, gts, k=2, threshold=0.9)
        assert p2 == pytest.approx(0.5, abs=1e-10)
        assert r2 == pytest.approx(0.5, abs=1e-10)

        # K=3
        p3 = compute_precision_at_k(preds, gts, k=3, threshold=0.9)
        r3 = compute_recall_at_k(preds, gts, k=3, threshold=0.9)
        assert p3 == pytest.approx(2/3, abs=1e-10)
        assert r3 == pytest.approx(1.0, abs=1e-10)

    def test_hit_rate_known(self):
        """
        Test: IoU@threshold hit rate with known values

        Matches at IoU >= 0.5:
        - (pred0, gt0, 0.8) - above threshold
        - (pred1, gt1, 0.4) - below threshold

        Num GT = 2
        Hit rate = 1/2 = 0.5
        """
        matches = [(0, 0, 0.8), (1, 1, 0.4)]

        hit_rate = compute_iou_at_threshold(matches, num_ground_truth=2, threshold=0.5)

        assert hit_rate == pytest.approx(0.5, abs=1e-10)

    def test_hungarian_matching_known(self):
        """
        Test: Hungarian matching with known optimal assignment

        IoU matrix:
        [[0.9, 0.1],
         [0.1, 0.8]]

        Optimal assignment: (0,0) with 0.9, (1,1) with 0.8
        Total IoU = 1.7 (maximum possible)
        """
        iou_matrix = np.array([
            [0.9, 0.1],
            [0.1, 0.8],
        ])

        matches = match_hungarian(iou_matrix, threshold=0.5)

        assert len(matches) == 2
        pairs = {(m[0], m[1]) for m in matches}
        assert pairs == {(0, 0), (1, 1)}


class TestKnownSelectionBehavior:
    """Regression tests for selection methods."""

    def test_top_k_ordering(self):
        """
        Test: Top-K preserves score ordering

        Input (unsorted): [(0, 0.3), (1, 0.9), (2, 0.5)]
        Top-2: [(1, 0.9), (2, 0.5)]
        """
        scored = [(0, 0.3), (1, 0.9), (2, 0.5)]

        selected = select_top_k(scored, k=2)

        assert len(selected) == 2
        assert selected[0] == (1, 0.9)
        assert selected[1] == (2, 0.5)

    def test_otsu_bimodal_known(self):
        """
        Test: Otsu threshold on bimodal distribution

        Low group: 0.1, 0.15, 0.2
        High group: 0.8, 0.85, 0.9

        Otsu should find threshold separating these groups,
        selecting only high group.
        """
        scored = [
            (0, 0.1), (1, 0.15), (2, 0.2),
            (3, 0.8), (4, 0.85), (5, 0.9),
        ]

        selected = select_by_otsu(scored)

        # Should select high-scoring regions
        selected_indices = {s[0] for s in selected}
        assert 3 in selected_indices or 4 in selected_indices or 5 in selected_indices


class TestRegressionFixtures:
    """Tests using fixed known configurations to detect regressions."""

    def test_standard_32x32_patch_grid(self):
        """
        Test: Standard 32x32 patch grid properties

        Patch dimensions: 1/32 x 1/32
        Total patches: 1024
        Patch 0: (0, 0, 0.03125, 0.03125)
        Patch 1023: (0.96875, 0.96875, 1.0, 1.0)
        """
        patch_0 = patch_index_to_normalized_box(0, 32, 32)
        patch_1023 = patch_index_to_normalized_box(1023, 32, 32)

        # Patch 0
        assert patch_0.x1 == pytest.approx(0.0, abs=1e-10)
        assert patch_0.y1 == pytest.approx(0.0, abs=1e-10)
        assert patch_0.width == pytest.approx(1/32, abs=1e-10)
        assert patch_0.height == pytest.approx(1/32, abs=1e-10)

        # Patch 1023
        assert patch_1023.x2 == pytest.approx(1.0, abs=1e-10)
        assert patch_1023.y2 == pytest.approx(1.0, abs=1e-10)
        assert patch_1023.width == pytest.approx(1/32, abs=1e-10)

    def test_iou_weight_consistency(self):
        """
        Test: IoU weights sum to expected value for full coverage

        A region covering exactly 4 patches in 4x4 grid
        should have total IoU weight = 4.0
        """
        region = Box(x1=0, y1=0, x2=0.5, y2=0.5)
        weights = patches_to_region_iou_weights(region, 4, 4)

        # Should cover exactly 4 patches with IoU = 1.0 each
        total_weight = np.sum(weights)
        assert total_weight == pytest.approx(4.0, abs=1e-10)

        # Exactly 4 non-zero weights
        assert np.count_nonzero(weights) == 4
