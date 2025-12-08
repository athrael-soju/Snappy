"""
Unit tests for coordinate utilities.

These tests use REAL computations with hand-verified expected values.
NO MOCKING of coordinate transformations or IoU calculations.
"""

import math

import numpy as np
import pytest

from benchmarks.utils.coordinates import (
    Box,
    compute_iou,
    compute_iou_matrix,
    get_overlapping_patches,
    normalize_bbox_deepseek,
    normalize_bbox_pixels,
    patch_index_to_normalized_box,
    patches_to_region_iou_weights,
)


class TestBox:
    """Tests for Box dataclass."""

    def test_box_creation(self):
        """Test basic box creation."""
        box = Box(x1=0.1, y1=0.2, x2=0.5, y2=0.6)
        assert box.x1 == 0.1
        assert box.y1 == 0.2
        assert box.x2 == 0.5
        assert box.y2 == 0.6

    def test_box_invalid_coordinates_x(self):
        """Test that x2 < x1 raises error."""
        with pytest.raises(ValueError, match="x2.*must be >= x1"):
            Box(x1=0.5, y1=0.2, x2=0.1, y2=0.6)

    def test_box_invalid_coordinates_y(self):
        """Test that y2 < y1 raises error."""
        with pytest.raises(ValueError, match="y2.*must be >= y1"):
            Box(x1=0.1, y1=0.6, x2=0.5, y2=0.2)

    def test_box_width_height(self):
        """Test width and height properties."""
        box = Box(x1=0.1, y1=0.2, x2=0.5, y2=0.8)
        assert box.width == pytest.approx(0.4)
        assert box.height == pytest.approx(0.6)

    def test_box_area(self):
        """Test area calculation."""
        box = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.4)
        # Area = 0.5 * 0.4 = 0.2
        assert box.area == pytest.approx(0.2)

    def test_box_to_tuple(self):
        """Test conversion to tuple."""
        box = Box(x1=0.1, y1=0.2, x2=0.3, y2=0.4)
        assert box.to_tuple() == (0.1, 0.2, 0.3, 0.4)

    def test_box_to_array(self):
        """Test conversion to numpy array."""
        box = Box(x1=0.1, y1=0.2, x2=0.3, y2=0.4)
        arr = box.to_array()
        np.testing.assert_array_almost_equal(arr, [0.1, 0.2, 0.3, 0.4])

    def test_box_from_tuple(self):
        """Test creation from tuple."""
        box = Box.from_tuple((0.1, 0.2, 0.3, 0.4))
        assert box.x1 == 0.1
        assert box.y1 == 0.2
        assert box.x2 == 0.3
        assert box.y2 == 0.4

    def test_box_from_array(self):
        """Test creation from numpy array."""
        arr = np.array([0.1, 0.2, 0.3, 0.4])
        box = Box.from_array(arr)
        assert box.x1 == pytest.approx(0.1)
        assert box.y1 == pytest.approx(0.2)
        assert box.x2 == pytest.approx(0.3)
        assert box.y2 == pytest.approx(0.4)


class TestPatchIndexToNormalizedBox:
    """Tests for patch_index_to_normalized_box function."""

    def test_first_patch(self):
        """Test patch at index 0 (top-left corner)."""
        # For 32x32 grid, patch 0 is at (0,0) to (1/32, 1/32)
        box = patch_index_to_normalized_box(0, n_patches_x=32, n_patches_y=32)
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(1/32)
        assert box.y2 == pytest.approx(1/32)

    def test_second_patch(self):
        """Test patch at index 1 (second in first row)."""
        # Patch 1 is at (1/32, 0) to (2/32, 1/32)
        box = patch_index_to_normalized_box(1, n_patches_x=32, n_patches_y=32)
        assert box.x1 == pytest.approx(1/32)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(2/32)
        assert box.y2 == pytest.approx(1/32)

    def test_first_of_second_row(self):
        """Test first patch of second row."""
        # Patch 32 is at (0, 1/32) to (1/32, 2/32)
        box = patch_index_to_normalized_box(32, n_patches_x=32, n_patches_y=32)
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(1/32)
        assert box.x2 == pytest.approx(1/32)
        assert box.y2 == pytest.approx(2/32)

    def test_last_patch(self):
        """Test last patch (bottom-right corner)."""
        # For 32x32 grid, last patch (1023) is at (31/32, 31/32) to (1, 1)
        box = patch_index_to_normalized_box(1023, n_patches_x=32, n_patches_y=32)
        assert box.x1 == pytest.approx(31/32)
        assert box.y1 == pytest.approx(31/32)
        assert box.x2 == pytest.approx(1.0)
        assert box.y2 == pytest.approx(1.0)

    def test_center_patch(self):
        """Test a center patch."""
        # For 4x4 grid, patch 5 is at (1/4, 1/4) to (2/4, 2/4)
        # idx=5: x=5%4=1, y=5//4=1
        box = patch_index_to_normalized_box(5, n_patches_x=4, n_patches_y=4)
        assert box.x1 == pytest.approx(0.25)
        assert box.y1 == pytest.approx(0.25)
        assert box.x2 == pytest.approx(0.5)
        assert box.y2 == pytest.approx(0.5)

    def test_invalid_negative_index(self):
        """Test that negative index raises error."""
        with pytest.raises(ValueError, match="out of range"):
            patch_index_to_normalized_box(-1)

    def test_invalid_too_large_index(self):
        """Test that index >= total patches raises error."""
        with pytest.raises(ValueError, match="out of range"):
            patch_index_to_normalized_box(1024, n_patches_x=32, n_patches_y=32)


class TestNormalizeBboxDeepseek:
    """Tests for normalize_bbox_deepseek function."""

    def test_full_image(self):
        """Test coordinates spanning full image."""
        # (0, 0, 999, 999) should map to (0, 0, 1, 1)
        box = normalize_bbox_deepseek((0, 0, 999, 999))
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(1.0)
        assert box.y2 == pytest.approx(1.0)

    def test_quarter_image(self):
        """Test coordinates spanning quarter of image."""
        # (0, 0, 499, 499) should map to approximately (0, 0, 0.5, 0.5)
        box = normalize_bbox_deepseek((0, 0, 499, 499))
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(499/999, rel=0.01)
        assert box.y2 == pytest.approx(499/999, rel=0.01)

    def test_center_region(self):
        """Test center region."""
        # (250, 250, 750, 750) should map to approximately (0.25, 0.25, 0.75, 0.75)
        box = normalize_bbox_deepseek((250, 250, 750, 750))
        assert box.x1 == pytest.approx(250/999, rel=0.01)
        assert box.y1 == pytest.approx(250/999, rel=0.01)
        assert box.x2 == pytest.approx(750/999, rel=0.01)
        assert box.y2 == pytest.approx(750/999, rel=0.01)

    def test_swapped_coordinates_corrected(self):
        """Test that swapped x coordinates are corrected."""
        # (500, 0, 100, 999) should be corrected to (100, 0, 500, 999)
        box = normalize_bbox_deepseek((500, 0, 100, 999))
        assert box.x1 < box.x2
        assert box.y1 < box.y2


class TestNormalizeBboxPixels:
    """Tests for normalize_bbox_pixels function."""

    def test_full_image(self):
        """Test coordinates spanning full image."""
        box = normalize_bbox_pixels((0, 0, 1000, 800), image_width=1000, image_height=800)
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(1.0)
        assert box.y2 == pytest.approx(1.0)

    def test_half_image(self):
        """Test coordinates spanning half image."""
        box = normalize_bbox_pixels((0, 0, 500, 400), image_width=1000, image_height=800)
        assert box.x1 == pytest.approx(0.0)
        assert box.y1 == pytest.approx(0.0)
        assert box.x2 == pytest.approx(0.5)
        assert box.y2 == pytest.approx(0.5)

    def test_offset_region(self):
        """Test region with offset."""
        box = normalize_bbox_pixels((100, 200, 300, 600), image_width=1000, image_height=1000)
        assert box.x1 == pytest.approx(0.1)
        assert box.y1 == pytest.approx(0.2)
        assert box.x2 == pytest.approx(0.3)
        assert box.y2 == pytest.approx(0.6)

    def test_invalid_dimensions(self):
        """Test that invalid dimensions raise error."""
        with pytest.raises(ValueError, match="Invalid image dimensions"):
            normalize_bbox_pixels((0, 0, 100, 100), image_width=0, image_height=100)


class TestComputeIou:
    """Tests for compute_iou function."""

    def test_identical_boxes(self):
        """Test IoU of identical boxes is 1."""
        box = Box(x1=0.1, y1=0.2, x2=0.5, y2=0.6)
        iou = compute_iou(box, box)
        assert iou == pytest.approx(1.0)

    def test_no_overlap(self):
        """Test IoU of non-overlapping boxes is 0."""
        box1 = Box(x1=0.0, y1=0.0, x2=0.3, y2=0.3)
        box2 = Box(x1=0.5, y1=0.5, x2=0.8, y2=0.8)
        iou = compute_iou(box1, box2)
        assert iou == pytest.approx(0.0)

    def test_touching_boxes(self):
        """Test IoU of touching (but not overlapping) boxes."""
        box1 = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        box2 = Box(x1=0.5, y1=0.0, x2=1.0, y2=0.5)
        iou = compute_iou(box1, box2)
        assert iou == pytest.approx(0.0)

    def test_partial_overlap(self):
        """Test IoU of partially overlapping boxes."""
        # Box1: (0,0) to (0.5, 0.5), area = 0.25
        # Box2: (0.25, 0.25) to (0.75, 0.75), area = 0.25
        # Intersection: (0.25, 0.25) to (0.5, 0.5), area = 0.0625
        # Union: 0.25 + 0.25 - 0.0625 = 0.4375
        # IoU: 0.0625 / 0.4375 = 0.142857...
        box1 = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        box2 = Box(x1=0.25, y1=0.25, x2=0.75, y2=0.75)
        iou = compute_iou(box1, box2)
        expected = 0.0625 / 0.4375
        assert iou == pytest.approx(expected, rel=0.001)

    def test_one_contains_other(self):
        """Test IoU when one box contains the other."""
        # Outer: (0,0) to (1,1), area = 1
        # Inner: (0.25, 0.25) to (0.75, 0.75), area = 0.25
        # Intersection = 0.25, Union = 1
        # IoU = 0.25
        outer = Box(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
        inner = Box(x1=0.25, y1=0.25, x2=0.75, y2=0.75)
        iou = compute_iou(outer, inner)
        assert iou == pytest.approx(0.25)

    def test_50_percent_overlap(self):
        """Test IoU with 50% overlap of one box."""
        # Box1: (0, 0) to (0.5, 1), area = 0.5
        # Box2: (0.25, 0) to (0.75, 1), area = 0.5
        # Intersection: (0.25, 0) to (0.5, 1), area = 0.25
        # Union: 0.5 + 0.5 - 0.25 = 0.75
        # IoU: 0.25 / 0.75 = 1/3
        box1 = Box(x1=0.0, y1=0.0, x2=0.5, y2=1.0)
        box2 = Box(x1=0.25, y1=0.0, x2=0.75, y2=1.0)
        iou = compute_iou(box1, box2)
        assert iou == pytest.approx(1/3, rel=0.001)


class TestComputeIouMatrix:
    """Tests for compute_iou_matrix function."""

    def test_empty_lists(self):
        """Test with empty box lists."""
        matrix = compute_iou_matrix([], [])
        assert matrix.shape == (0, 0)

    def test_single_box_each(self):
        """Test with single box in each list."""
        box1 = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        box2 = Box(x1=0.25, y1=0.25, x2=0.75, y2=0.75)
        matrix = compute_iou_matrix([box1], [box2])
        assert matrix.shape == (1, 1)
        expected = compute_iou(box1, box2)
        assert matrix[0, 0] == pytest.approx(expected)

    def test_multiple_boxes(self):
        """Test with multiple boxes."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.3, y2=0.3),
            Box(x1=0.5, y1=0.5, x2=0.8, y2=0.8),
        ]
        gts = [
            Box(x1=0.1, y1=0.1, x2=0.4, y2=0.4),
            Box(x1=0.6, y1=0.6, x2=0.9, y2=0.9),
        ]
        matrix = compute_iou_matrix(preds, gts)
        assert matrix.shape == (2, 2)

        # Verify each entry
        for i, pred in enumerate(preds):
            for j, gt in enumerate(gts):
                expected = compute_iou(pred, gt)
                assert matrix[i, j] == pytest.approx(expected)

    def test_vectorized_matches_loop(self):
        """Test that vectorized implementation matches loop computation."""
        np.random.seed(42)
        n_preds, n_gts = 10, 8

        preds = []
        gts = []
        for _ in range(n_preds):
            x1, y1 = np.random.rand(2) * 0.5
            w, h = np.random.rand(2) * 0.3 + 0.1
            preds.append(Box(x1=x1, y1=y1, x2=x1+w, y2=y1+h))

        for _ in range(n_gts):
            x1, y1 = np.random.rand(2) * 0.5
            w, h = np.random.rand(2) * 0.3 + 0.1
            gts.append(Box(x1=x1, y1=y1, x2=x1+w, y2=y1+h))

        matrix = compute_iou_matrix(preds, gts)

        # Verify against loop computation
        for i, pred in enumerate(preds):
            for j, gt in enumerate(gts):
                expected = compute_iou(pred, gt)
                assert matrix[i, j] == pytest.approx(expected, abs=1e-10)


class TestGetOverlappingPatches:
    """Tests for get_overlapping_patches function."""

    def test_single_patch_region(self):
        """Test region covering exactly one patch."""
        # Region exactly covering patch (0,0) in 4x4 grid
        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        overlapping = get_overlapping_patches(region, n_patches_x=4, n_patches_y=4)

        assert len(overlapping) == 1
        px, py, iou = overlapping[0]
        assert px == 0
        assert py == 0
        assert iou == pytest.approx(1.0)

    def test_multi_patch_region(self):
        """Test region covering multiple patches."""
        # Region covering patches (0,0), (1,0), (0,1), (1,1) in 4x4 grid
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        overlapping = get_overlapping_patches(region, n_patches_x=4, n_patches_y=4)

        assert len(overlapping) == 4
        # Each patch should have IoU = 1.0 (full overlap)
        for px, py, iou in overlapping:
            assert 0 <= px <= 1
            assert 0 <= py <= 1
            assert iou == pytest.approx(1.0)

    def test_partial_overlap(self):
        """Test region partially overlapping patches."""
        # Region covering half of patch (0,0) in 4x4 grid
        region = Box(x1=0.0, y1=0.0, x2=0.125, y2=0.25)
        overlapping = get_overlapping_patches(region, n_patches_x=4, n_patches_y=4)

        assert len(overlapping) == 1
        px, py, iou = overlapping[0]
        assert px == 0
        assert py == 0
        # Region area = 0.125 * 0.25 = 0.03125
        # Patch area = 0.25 * 0.25 = 0.0625
        # Intersection = 0.03125
        # Union = 0.03125 + 0.0625 - 0.03125 = 0.0625
        # IoU = 0.03125 / 0.0625 = 0.5
        assert iou == pytest.approx(0.5)


class TestPatchesToRegionIouWeights:
    """Tests for patches_to_region_iou_weights function."""

    def test_single_patch_full_coverage(self):
        """Test weights for region exactly covering one patch."""
        region = Box(x1=0.0, y1=0.0, x2=0.25, y2=0.25)
        weights = patches_to_region_iou_weights(region, n_patches_x=4, n_patches_y=4)

        assert weights.shape == (4, 4)
        assert weights[0, 0] == pytest.approx(1.0)
        # All other weights should be 0
        assert np.sum(weights) == pytest.approx(1.0)

    def test_four_patches_full_coverage(self):
        """Test weights for region covering four patches."""
        region = Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)
        weights = patches_to_region_iou_weights(region, n_patches_x=4, n_patches_y=4)

        assert weights.shape == (4, 4)
        # First 4 patches should have weight 1.0
        assert weights[0, 0] == pytest.approx(1.0)
        assert weights[0, 1] == pytest.approx(1.0)
        assert weights[1, 0] == pytest.approx(1.0)
        assert weights[1, 1] == pytest.approx(1.0)
        # Total weight should be 4
        assert np.sum(weights) == pytest.approx(4.0)

    def test_partial_coverage(self):
        """Test weights for partial patch coverage."""
        # Region covering half of two patches horizontally
        region = Box(x1=0.0, y1=0.0, x2=0.375, y2=0.25)
        weights = patches_to_region_iou_weights(region, n_patches_x=4, n_patches_y=4)

        assert weights.shape == (4, 4)
        # Patch (0,0) fully covered: weight 1.0
        assert weights[0, 0] == pytest.approx(1.0)
        # Patch (1,0) half covered
        assert weights[0, 1] > 0
        assert weights[0, 1] < 1.0
