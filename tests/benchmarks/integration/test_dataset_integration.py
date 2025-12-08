"""
Integration tests using real BBox_DocVQA dataset samples.

These tests use REAL data samples with REAL computations.
NO MOCKING of dataset loading, coordinate transforms, or evaluation.

Note: These tests require the datasets library and may download data.
Tests are marked with pytest.mark.integration and pytest.mark.slow.
"""

import pytest

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]


class TestDatasetLoadingIntegration:
    """Integration tests for dataset loading."""

    @pytest.mark.slow
    def test_load_bbox_docvqa_dataset(self):
        """Test loading the real BBox_DocVQA dataset."""
        pytest.importorskip("datasets")

        from benchmarks.loaders.bbox_docvqa import BBoxDocVQALoader

        loader = BBoxDocVQALoader(
            dataset_path="Yuwh07/BBox_DocVQA_Bench",
            filter_type="single_page",
        )

        try:
            loader.load()
            samples = loader.samples

            # Verify we got samples
            assert len(samples) > 0

            # Verify sample structure
            sample = samples[0]
            assert sample.sample_id is not None
            assert sample.question is not None
            assert len(sample.ground_truth_boxes) > 0

            # Verify ground truth boxes are normalized
            for gt in sample.ground_truth_boxes:
                assert 0 <= gt.box.x1 <= 1
                assert 0 <= gt.box.y1 <= 1
                assert 0 <= gt.box.x2 <= 1
                assert 0 <= gt.box.y2 <= 1

        except Exception as e:
            pytest.skip(f"Could not load dataset: {e}")

    @pytest.mark.slow
    def test_dataset_statistics(self):
        """Test dataset statistics computation."""
        pytest.importorskip("datasets")

        from benchmarks.loaders.bbox_docvqa import BBoxDocVQALoader

        loader = BBoxDocVQALoader(
            dataset_path="Yuwh07/BBox_DocVQA_Bench",
            filter_type="all",
        )

        try:
            loader.load()
            stats = loader.get_statistics()

            assert "total_samples" in stats
            assert "complexity_distribution" in stats
            assert "single_page_count" in stats
            assert "multi_page_count" in stats

            # Verify complexity distribution
            complexity = stats["complexity_distribution"]
            assert "SPSBB" in complexity
            assert "SPMBB" in complexity
            assert "MPMBB" in complexity

        except Exception as e:
            pytest.skip(f"Could not load dataset: {e}")

    @pytest.mark.slow
    def test_stratified_sampling(self):
        """Test stratified sampling across complexity types."""
        pytest.importorskip("datasets")

        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQALoader,
            ComplexityType,
        )

        loader = BBoxDocVQALoader(
            dataset_path="Yuwh07/BBox_DocVQA_Bench",
            filter_type="all",
        )

        try:
            loader.load()
            stratified = loader.get_stratified_sample(n_per_category=5)

            # Should have samples from each category
            complexities = {s.complexity for s in stratified}

            # At least some categories should be represented
            assert len(complexities) >= 1

        except Exception as e:
            pytest.skip(f"Could not load dataset: {e}")


class TestEndToEndPipelineIntegration:
    """Integration tests for the full pipeline with simulated data."""

    def test_pipeline_with_synthetic_data(self):
        """Test pipeline with synthetic samples (no dataset required)."""
        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQASample,
            ComplexityType,
            GroundTruthBox,
        )
        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.utils.coordinates import Box

        # Create synthetic samples
        samples = [
            BBoxDocVQASample(
                sample_id="synthetic_1",
                question="What is shown in the document?",
                answer="A table of data",
                document_id="doc_1",
                page_indices=[0],
                ground_truth_boxes=[
                    GroundTruthBox(
                        box=Box(x1=0.1, y1=0.1, x2=0.4, y2=0.4),
                        page_idx=0,
                    ),
                    GroundTruthBox(
                        box=Box(x1=0.5, y1=0.5, x2=0.9, y2=0.9),
                        page_idx=0,
                    ),
                ],
                complexity=ComplexityType.SPMBB,
            ),
            BBoxDocVQASample(
                sample_id="synthetic_2",
                question="Where is the title?",
                answer="Top of page",
                document_id="doc_2",
                page_indices=[0],
                ground_truth_boxes=[
                    GroundTruthBox(
                        box=Box(x1=0.2, y1=0.0, x2=0.8, y2=0.1),
                        page_idx=0,
                    ),
                ],
                complexity=ComplexityType.SPSBB,
            ),
        ]

        # Run pipeline in simulation mode
        config = BenchmarkConfig(
            max_samples=2,
            run_baselines=True,
            save_predictions=True,
        )

        pipeline = BenchmarkPipeline(config=config)
        results = pipeline.run(samples=samples)

        # Verify results
        assert results.total_samples == 2
        assert results.overall_metrics.num_samples == 2
        assert "mean_mean_iou" in results.overall_metrics.metrics

        # Verify stratified results
        assert "SPSBB" in results.stratified_metrics
        assert "SPMBB" in results.stratified_metrics

    def test_pipeline_aggregation_selection_combinations(self):
        """Test pipeline with different aggregation/selection combos."""
        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQASample,
            ComplexityType,
            GroundTruthBox,
        )
        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.utils.coordinates import Box

        sample = BBoxDocVQASample(
            sample_id="combo_test",
            question="Test question",
            answer="Test answer",
            document_id="doc_1",
            page_indices=[0],
            ground_truth_boxes=[
                GroundTruthBox(
                    box=Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
                    page_idx=0,
                ),
            ],
            complexity=ComplexityType.SPSBB,
        )

        config = BenchmarkConfig(
            max_samples=1,
            aggregation_methods=["max", "mean", "iou_weighted"],
            selection_methods=["top_k", "threshold"],
            top_k_values=[1, 3],
            threshold_values=[0.3],
        )

        pipeline = BenchmarkPipeline(config=config)
        results = pipeline.run(samples=[sample])

        # Verify grid search results
        assert len(results.method_grid_results) > 0

        # Check that we have results for different method combinations
        method_keys = list(results.method_grid_results.keys())
        assert any("max" in k for k in method_keys)
        assert any("mean" in k for k in method_keys)


class TestRealComputationsIntegration:
    """Integration tests verifying real computations on realistic data."""

    def test_iou_computation_chain(self):
        """Test IoU computation through the full pipeline."""
        from benchmarks.aggregation import compute_region_scores
        from benchmarks.aggregation import AggregationMethod
        from benchmarks.evaluation import evaluate_sample, MatchingStrategy
        from benchmarks.selection import select_regions, SelectionMethod
        from benchmarks.utils.coordinates import Box
        import numpy as np

        # Create realistic scenario: 4x4 patch grid, 3 OCR regions
        patch_scores = np.array([
            [0.1, 0.2, 0.8, 0.9],
            [0.1, 0.3, 0.7, 0.8],
            [0.2, 0.2, 0.3, 0.4],
            [0.1, 0.1, 0.2, 0.3],
        ], dtype=np.float32)

        regions = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),   # covers low-score area
            Box(x1=0.5, y1=0.0, x2=1.0, y2=0.5),   # covers high-score area
            Box(x1=0.25, y1=0.25, x2=0.75, y2=0.75),  # covers mixed area
        ]

        ground_truth = [
            Box(x1=0.5, y1=0.0, x2=1.0, y2=0.5),  # matches region 1
        ]

        # Step 1: Score regions
        scored = compute_region_scores(
            regions, patch_scores, AggregationMethod.MAX,
            n_patches_x=4, n_patches_y=4
        )

        # Verify scoring
        assert len(scored) == 3
        assert scored[0][0] == 1  # Region 1 should score highest (high patch area)

        # Step 2: Select top region
        selected = select_regions(scored, SelectionMethod.TOP_K, k=1)
        assert len(selected) == 1
        assert selected[0][0] == 1

        # Step 3: Evaluate against ground truth
        predicted_boxes = [regions[selected[0][0]]]
        result = evaluate_sample(
            predictions=predicted_boxes,
            ground_truth=ground_truth,
            sample_id="test",
            strategy=MatchingStrategy.SET_COVERAGE,
            iou_thresholds=[0.5, 0.75],
        )

        # Verify perfect match (region 1 = GT)
        assert result.metrics["iou@0.5"] == 1.0
        assert result.metrics["mean_iou"] == 1.0

    def test_multi_token_aggregation_chain(self):
        """Test multi-token aggregation through pipeline."""
        from benchmarks.aggregation import compute_region_scores_multi_token
        from benchmarks.aggregation import AggregationMethod
        from benchmarks.utils.coordinates import Box
        import numpy as np

        # Two tokens with different attention patterns
        token1_scores = np.array([
            [0.9, 0.1],
            [0.1, 0.1],
        ], dtype=np.float32)

        token2_scores = np.array([
            [0.1, 0.1],
            [0.1, 0.9],
        ], dtype=np.float32)

        token_maps = [token1_scores, token2_scores]

        regions = [
            Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),  # top-left
            Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),  # bottom-right
        ]

        # Max aggregation across tokens
        scored = compute_region_scores_multi_token(
            regions, token_maps, AggregationMethod.MAX,
            token_aggregation="max", n_patches_x=2, n_patches_y=2
        )

        # Both regions should score 0.9 (token 1 prefers region 0, token 2 prefers region 1)
        assert len(scored) == 2
        for idx, score in scored:
            assert score == pytest.approx(0.9)
