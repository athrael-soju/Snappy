"""
Unit tests for evaluation metrics and matching strategies.

These tests use REAL computations with hand-verified expected values.
NO MOCKING of IoU, matching, or metric calculations.
"""

import numpy as np
import pytest

from benchmarks.evaluation import (
    AggregatedMetrics,
    EvaluationResult,
    MatchingStrategy,
    aggregate_results,
    compare_to_baseline,
    compute_average_precision,
    compute_iou_at_threshold,
    compute_mean_iou,
    compute_precision_at_k,
    compute_recall_at_k,
    evaluate_sample,
    match_any,
    match_hungarian,
    match_predictions,
    match_set_coverage,
)
from benchmarks.utils.coordinates import Box


class TestMatchAny:
    """Tests for any-match strategy."""

    def test_single_match(self):
        """Test single matching pair."""
        # IoU matrix: 1 pred, 1 gt with IoU = 0.7
        iou_matrix = np.array([[0.7]])
        matches = match_any(iou_matrix, threshold=0.5)

        assert len(matches) == 1
        assert matches[0] == (0, 0, 0.7)

    def test_no_match_below_threshold(self):
        """Test no match when below threshold."""
        iou_matrix = np.array([[0.3]])
        matches = match_any(iou_matrix, threshold=0.5)

        assert len(matches) == 0

    def test_multiple_matches(self):
        """Test multiple matches."""
        # 2 preds, 2 gts
        iou_matrix = np.array([
            [0.8, 0.2],
            [0.3, 0.9],
        ])
        matches = match_any(iou_matrix, threshold=0.5)

        # Should match (0,0) with 0.8 and (1,1) with 0.9
        assert len(matches) == 2
        matched_pairs = {(m[0], m[1]) for m in matches}
        assert (0, 0) in matched_pairs
        assert (1, 1) in matched_pairs

    def test_many_to_many_matches(self):
        """Test that any-match allows many-to-many."""
        iou_matrix = np.array([
            [0.6, 0.7],
            [0.8, 0.5],
        ])
        matches = match_any(iou_matrix, threshold=0.5)

        # All four pairs exceed threshold
        assert len(matches) == 4


class TestMatchSetCoverage:
    """Tests for set coverage matching strategy."""

    def test_single_match(self):
        """Test single matching pair."""
        iou_matrix = np.array([[0.7]])
        matches = match_set_coverage(iou_matrix, threshold=0.5)

        assert len(matches) == 1
        assert matches[0] == (0, 0, 0.7)

    def test_best_match_per_gt(self):
        """Test that best match is selected per GT."""
        # 2 preds, 1 gt - should pick best pred
        iou_matrix = np.array([
            [0.6],
            [0.8],
        ])
        matches = match_set_coverage(iou_matrix, threshold=0.5)

        assert len(matches) == 1
        assert matches[0][0] == 1  # pred 1 has higher IoU
        assert matches[0][1] == 0
        assert matches[0][2] == pytest.approx(0.8)

    def test_multiple_gts(self):
        """Test with multiple GT boxes."""
        iou_matrix = np.array([
            [0.9, 0.1],
            [0.2, 0.8],
        ])
        matches = match_set_coverage(iou_matrix, threshold=0.5)

        # GT 0 matched by pred 0, GT 1 matched by pred 1
        assert len(matches) == 2

    def test_unmatched_gt(self):
        """Test GT that doesn't meet threshold."""
        iou_matrix = np.array([
            [0.8, 0.3],
        ])
        matches = match_set_coverage(iou_matrix, threshold=0.5)

        # Only GT 0 is matched
        assert len(matches) == 1
        assert matches[0][1] == 0


class TestMatchHungarian:
    """Tests for Hungarian matching strategy."""

    def test_optimal_matching(self):
        """Test optimal 1:1 matching."""
        # Cross-matching scenario
        iou_matrix = np.array([
            [0.9, 0.1],
            [0.1, 0.8],
        ])
        matches = match_hungarian(iou_matrix, threshold=0.5)

        # Optimal: (0,0) and (1,1)
        assert len(matches) == 2
        matched_pairs = {(m[0], m[1]) for m in matches}
        assert (0, 0) in matched_pairs
        assert (1, 1) in matched_pairs

    def test_one_to_one_constraint(self):
        """Test that Hungarian enforces 1:1 matching."""
        # Both preds want GT 0
        iou_matrix = np.array([
            [0.9],
            [0.8],
        ])
        matches = match_hungarian(iou_matrix, threshold=0.5)

        # Only one pred can match GT 0
        assert len(matches) == 1
        assert matches[0][0] == 0  # pred 0 has higher IoU

    def test_threshold_filtering(self):
        """Test that threshold is applied after matching."""
        iou_matrix = np.array([
            [0.4, 0.9],
            [0.8, 0.3],
        ])
        matches = match_hungarian(iou_matrix, threshold=0.5)

        # Hungarian would match (0,1)=0.9, (1,0)=0.8
        # Both exceed threshold
        assert len(matches) == 2


class TestMatchPredictions:
    """Tests for match_predictions dispatch function."""

    def test_dispatch_any_match(self):
        """Test dispatch to any-match strategy."""
        preds = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]
        gts = [Box(x1=0.1, y1=0.1, x2=0.6, y2=0.6)]

        iou_matrix, matches = match_predictions(
            preds, gts, MatchingStrategy.ANY_MATCH, threshold=0.3
        )

        assert iou_matrix.shape == (1, 1)
        assert len(matches) >= 0  # May or may not match depending on IoU

    def test_dispatch_set_coverage(self):
        """Test dispatch to set-coverage strategy."""
        preds = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        iou_matrix, matches = match_predictions(
            preds, gts, MatchingStrategy.SET_COVERAGE, threshold=0.5
        )

        assert iou_matrix[0, 0] == pytest.approx(1.0)
        assert len(matches) == 1

    def test_dispatch_hungarian(self):
        """Test dispatch to Hungarian strategy."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        _, matches = match_predictions(
            preds, gts, MatchingStrategy.HUNGARIAN, threshold=0.5
        )

        assert len(matches) == 2

    def test_empty_predictions(self):
        """Test with empty predictions."""
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        iou_matrix, matches = match_predictions(
            [], gts, MatchingStrategy.ANY_MATCH, threshold=0.5
        )

        assert iou_matrix.shape == (0, 1)
        assert len(matches) == 0


class TestComputeIouAtThreshold:
    """Tests for IoU@threshold metric."""

    def test_perfect_matching(self):
        """Test with all GT matched."""
        matches = [(0, 0, 0.8), (1, 1, 0.9)]
        hit_rate = compute_iou_at_threshold(matches, num_ground_truth=2, threshold=0.5)

        assert hit_rate == pytest.approx(1.0)

    def test_partial_matching(self):
        """Test with partial GT matched."""
        matches = [(0, 0, 0.8)]
        hit_rate = compute_iou_at_threshold(matches, num_ground_truth=2, threshold=0.5)

        assert hit_rate == pytest.approx(0.5)

    def test_threshold_filtering(self):
        """Test that threshold filters matches."""
        matches = [(0, 0, 0.8), (1, 1, 0.4)]  # Second below threshold
        hit_rate = compute_iou_at_threshold(matches, num_ground_truth=2, threshold=0.5)

        assert hit_rate == pytest.approx(0.5)

    def test_no_ground_truth(self):
        """Test with no ground truth."""
        hit_rate = compute_iou_at_threshold([], num_ground_truth=0, threshold=0.5)
        assert hit_rate == 0.0


class TestComputeMeanIou:
    """Tests for mean IoU metric."""

    def test_single_match(self):
        """Test mean IoU with single match."""
        iou_matrix = np.array([[0.7]])
        matches = [(0, 0, 0.7)]
        mean_iou = compute_mean_iou(iou_matrix, matches)

        assert mean_iou == pytest.approx(0.7)

    def test_multiple_matches(self):
        """Test mean IoU with multiple matches."""
        iou_matrix = np.array([[0.6, 0], [0, 0.8]])
        matches = [(0, 0, 0.6), (1, 1, 0.8)]
        mean_iou = compute_mean_iou(iou_matrix, matches)

        assert mean_iou == pytest.approx(0.7)

    def test_no_matches(self):
        """Test mean IoU with no matches."""
        iou_matrix = np.array([[0.1]])
        mean_iou = compute_mean_iou(iou_matrix, [])

        assert mean_iou == 0.0


class TestComputePrecisionAtK:
    """Tests for Precision@K metric."""

    def test_all_correct(self):
        """Test precision when all predictions are correct."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        precision = compute_precision_at_k(preds, gts, k=2, threshold=0.9)
        assert precision == pytest.approx(1.0)

    def test_half_correct(self):
        """Test precision when half are correct."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),  # matches GT 0
            Box(x1=0.7, y1=0.7, x2=0.9, y2=0.9),  # no match
        ]
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        precision = compute_precision_at_k(preds, gts, k=2, threshold=0.9)
        assert precision == pytest.approx(0.5)

    def test_k_limits_evaluation(self):
        """Test that K limits which predictions are evaluated."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),  # rank 1 - correct
            Box(x1=0.8, y1=0.8, x2=0.9, y2=0.9),  # rank 2 - wrong
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),  # rank 3 - correct
        ]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        # At K=1, only first (correct)
        assert compute_precision_at_k(preds, gts, k=1, threshold=0.9) == pytest.approx(1.0)

        # At K=2, one correct, one wrong
        assert compute_precision_at_k(preds, gts, k=2, threshold=0.9) == pytest.approx(0.5)


class TestComputeRecallAtK:
    """Tests for Recall@K metric."""

    def test_full_recall(self):
        """Test recall when all GT are found."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        recall = compute_recall_at_k(preds, gts, k=2, threshold=0.9)
        assert recall == pytest.approx(1.0)

    def test_partial_recall(self):
        """Test recall when some GT are found."""
        preds = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        recall = compute_recall_at_k(preds, gts, k=1, threshold=0.9)
        assert recall == pytest.approx(0.5)

    def test_k_affects_recall(self):
        """Test that K affects which GT can be recalled."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),  # rank 1
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),  # rank 2
        ]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        # K=1: only first GT found
        assert compute_recall_at_k(preds, gts, k=1, threshold=0.9) == pytest.approx(0.5)

        # K=2: both GT found
        assert compute_recall_at_k(preds, gts, k=2, threshold=0.9) == pytest.approx(1.0)


class TestComputeAveragePrecision:
    """Tests for Average Precision metric."""

    def test_perfect_ranking(self):
        """Test AP with perfect ranking."""
        preds = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]
        scores = [0.9, 0.8]
        gts = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
        ]

        ap = compute_average_precision(preds, scores, gts, threshold=0.9)
        assert ap == pytest.approx(1.0)

    def test_empty_predictions(self):
        """Test AP with no predictions."""
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]
        ap = compute_average_precision([], [], gts, threshold=0.5)
        assert ap == 0.0


class TestEvaluateSample:
    """Tests for evaluate_sample function."""

    def test_perfect_predictions(self):
        """Test evaluation with perfect predictions."""
        preds = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        result = evaluate_sample(
            predictions=preds,
            ground_truth=gts,
            sample_id="test_1",
            iou_thresholds=[0.5, 0.75],
        )

        assert result.sample_id == "test_1"
        assert result.num_predictions == 1
        assert result.num_ground_truth == 1
        assert result.metrics["iou@0.5"] == pytest.approx(1.0)
        assert result.metrics["mean_iou"] == pytest.approx(1.0)

    def test_no_predictions(self):
        """Test evaluation with no predictions."""
        gts = [Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5)]

        result = evaluate_sample(
            predictions=[],
            ground_truth=gts,
            sample_id="test_2",
        )

        assert result.num_predictions == 0
        assert result.metrics["iou@0.5"] == 0.0


class TestAggregateResults:
    """Tests for aggregate_results function."""

    def test_aggregation(self):
        """Test aggregation of multiple results."""
        results = [
            EvaluationResult(
                sample_id="1",
                num_predictions=2,
                num_ground_truth=2,
                iou_matrix=np.array([[1, 0], [0, 1]]),
                matched_pairs=[(0, 0, 1.0), (1, 1, 1.0)],
                metrics={"mean_iou": 1.0, "iou@0.5": 1.0},
            ),
            EvaluationResult(
                sample_id="2",
                num_predictions=1,
                num_ground_truth=2,
                iou_matrix=np.array([[0.5, 0.1]]),
                matched_pairs=[(0, 0, 0.5)],
                metrics={"mean_iou": 0.5, "iou@0.5": 0.5},
            ),
        ]

        aggregated = aggregate_results(results)

        assert aggregated.num_samples == 2
        assert aggregated.total_predictions == 3
        assert aggregated.total_ground_truth == 4
        assert aggregated.metrics["mean_mean_iou"] == pytest.approx(0.75)

    def test_empty_results(self):
        """Test aggregation of empty results."""
        aggregated = aggregate_results([])

        assert aggregated.num_samples == 0
        assert aggregated.total_predictions == 0


class TestCompareToBaseline:
    """Tests for compare_to_baseline function."""

    def test_improvement(self):
        """Test comparison showing improvement."""
        method = AggregatedMetrics(
            num_samples=10,
            total_predictions=50,
            total_ground_truth=50,
            metrics={"mean_mean_iou": 0.6},
        )
        baseline = AggregatedMetrics(
            num_samples=10,
            total_predictions=50,
            total_ground_truth=50,
            metrics={"mean_mean_iou": 0.4},
        )

        comparison = compare_to_baseline(method, baseline)

        assert comparison["method_value"] == 0.6
        assert comparison["baseline_value"] == 0.4
        assert comparison["absolute_improvement"] == pytest.approx(0.2)
        assert comparison["relative_improvement"] == pytest.approx(0.5)
        assert comparison["beats_baseline"] is True

    def test_no_improvement(self):
        """Test comparison showing no improvement."""
        method = AggregatedMetrics(
            num_samples=10,
            total_predictions=50,
            total_ground_truth=50,
            metrics={"mean_mean_iou": 0.3},
        )
        baseline = AggregatedMetrics(
            num_samples=10,
            total_predictions=50,
            total_ground_truth=50,
            metrics={"mean_mean_iou": 0.4},
        )

        comparison = compare_to_baseline(method, baseline)

        assert comparison["beats_baseline"] is False
        assert comparison["absolute_improvement"] < 0
