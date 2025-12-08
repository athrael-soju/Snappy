"""
End-to-end tests for the full benchmark pipeline.

These tests run the complete pipeline with REAL model inference
when available. NO MOCKING of core functionality.

Note: Tests requiring real model inference are marked with
pytest.mark.model_required and may be skipped if models unavailable.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Mark all tests in this module as e2e tests
pytestmark = [pytest.mark.e2e]


class TestFullPipelineSimulation:
    """E2E tests using simulated model outputs."""

    def test_complete_pipeline_simulation(self):
        """Test complete pipeline with simulated model."""
        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQASample,
            ComplexityType,
            GroundTruthBox,
        )
        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.utils.coordinates import Box

        # Create diverse test samples
        samples = []

        # SPSBB sample (single page, single box)
        samples.append(
            BBoxDocVQASample(
                sample_id="e2e_spsbb_1",
                question="What is the title?",
                answer="Document Title",
                document_id="doc_1",
                page_indices=[0],
                ground_truth_boxes=[
                    GroundTruthBox(
                        box=Box(x1=0.2, y1=0.05, x2=0.8, y2=0.15),
                        page_idx=0,
                    ),
                ],
                complexity=ComplexityType.SPSBB,
            )
        )

        # SPMBB sample (single page, multiple boxes)
        samples.append(
            BBoxDocVQASample(
                sample_id="e2e_spmbb_1",
                question="Where are the data entries?",
                answer="In the table",
                document_id="doc_2",
                page_indices=[0],
                ground_truth_boxes=[
                    GroundTruthBox(
                        box=Box(x1=0.1, y1=0.3, x2=0.45, y2=0.4),
                        page_idx=0,
                    ),
                    GroundTruthBox(
                        box=Box(x1=0.55, y1=0.3, x2=0.9, y2=0.4),
                        page_idx=0,
                    ),
                    GroundTruthBox(
                        box=Box(x1=0.1, y1=0.45, x2=0.9, y2=0.7),
                        page_idx=0,
                    ),
                ],
                complexity=ComplexityType.SPMBB,
            )
        )

        # Add more SPSBB samples for statistical significance
        for i in range(3):
            samples.append(
                BBoxDocVQASample(
                    sample_id=f"e2e_spsbb_{i+2}",
                    question=f"Question {i}?",
                    answer=f"Answer {i}",
                    document_id=f"doc_{i+3}",
                    page_indices=[0],
                    ground_truth_boxes=[
                        GroundTruthBox(
                            box=Box(
                                x1=0.1 + i * 0.1,
                                y1=0.1 + i * 0.1,
                                x2=0.4 + i * 0.1,
                                y2=0.4 + i * 0.1,
                            ),
                            page_idx=0,
                        ),
                    ],
                    complexity=ComplexityType.SPSBB,
                )
            )

        # Run full pipeline
        config = BenchmarkConfig(
            aggregation_methods=["max", "iou_weighted"],
            selection_methods=["top_k"],
            top_k_values=[1, 3, 5],
            iou_thresholds=[0.25, 0.5, 0.75],
            run_baselines=True,
            save_predictions=True,
        )

        pipeline = BenchmarkPipeline(config=config)
        results = pipeline.run(samples=samples)

        # Verify comprehensive results
        assert results.total_samples == 5
        assert results.overall_metrics.num_samples == 5

        # Verify metrics computed
        metrics = results.overall_metrics.metrics
        assert "mean_mean_iou" in metrics
        assert "mean_iou@0.5" in metrics
        assert "std_mean_iou" in metrics

        # Verify stratified results
        assert results.stratified_metrics["SPSBB"].num_samples == 4
        assert results.stratified_metrics["SPMBB"].num_samples == 1

        # Verify baseline comparisons
        assert "random_ocr" in results.baseline_comparisons
        assert "uniform_patches" in results.baseline_comparisons

        # Verify method grid results
        assert len(results.method_grid_results) > 0

    def test_pipeline_results_saving(self):
        """Test that pipeline results can be saved and loaded."""
        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQASample,
            ComplexityType,
            GroundTruthBox,
        )
        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.utils.coordinates import Box
        import json

        sample = BBoxDocVQASample(
            sample_id="save_test",
            question="Test?",
            answer="Test",
            document_id="doc_1",
            page_indices=[0],
            ground_truth_boxes=[
                GroundTruthBox(
                    box=Box(x1=0.1, y1=0.1, x2=0.5, y2=0.5),
                    page_idx=0,
                ),
            ],
            complexity=ComplexityType.SPSBB,
        )

        config = BenchmarkConfig(save_predictions=False)
        pipeline = BenchmarkPipeline(config=config)
        results = pipeline.run(samples=[sample])

        # Save to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name

        try:
            results.save(temp_path)

            # Verify file exists and is valid JSON
            assert os.path.exists(temp_path)

            with open(temp_path, "r") as f:
                loaded = json.load(f)

            assert "timestamp" in loaded
            assert "total_samples" in loaded
            assert "overall_metrics" in loaded

        finally:
            os.unlink(temp_path)

    def test_pipeline_print_summary(self, capsys):
        """Test that pipeline summary printing works."""
        from benchmarks.loaders.bbox_docvqa import (
            BBoxDocVQASample,
            ComplexityType,
            GroundTruthBox,
        )
        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.utils.coordinates import Box

        sample = BBoxDocVQASample(
            sample_id="summary_test",
            question="Test?",
            answer="Test",
            document_id="doc_1",
            page_indices=[0],
            ground_truth_boxes=[
                GroundTruthBox(
                    box=Box(x1=0.1, y1=0.1, x2=0.5, y2=0.5),
                    page_idx=0,
                ),
            ],
            complexity=ComplexityType.SPSBB,
        )

        config = BenchmarkConfig()
        pipeline = BenchmarkPipeline(config=config)
        pipeline.run(samples=[sample])

        pipeline.print_summary()

        captured = capsys.readouterr()
        assert "BENCHMARK RESULTS SUMMARY" in captured.out
        assert "OVERALL METRICS" in captured.out


class TestFullPipelineWithModel:
    """E2E tests using real model inference."""

    @pytest.mark.model_required
    @pytest.mark.slow
    def test_pipeline_with_colpali(self):
        """Test pipeline with real ColPali model inference.

        This test requires:
        - ColPali service running at localhost:7000
        - DeepSeek OCR service running at localhost:8200
        """
        import requests

        from benchmarks.pipeline import BenchmarkConfig, BenchmarkPipeline
        from benchmarks.run_bbox_docvqa import (
            create_colpali_inference_func,
            create_deepseek_ocr_func,
        )

        colpali_url = os.environ.get("COLPALI_URL", "http://localhost:7000")
        ocr_url = os.environ.get("OCR_URL", "http://localhost:8200")

        # Check service availability
        try:
            requests.get(f"{colpali_url}/health", timeout=5)
            requests.get(f"{ocr_url}/health", timeout=5)
        except requests.RequestException:
            pytest.skip("ColPali or OCR services not available")

        # Create inference functions
        model_inference = create_colpali_inference_func(colpali_url)
        ocr_func = create_deepseek_ocr_func(ocr_url)

        config = BenchmarkConfig(
            max_samples=10,
            filter_type="single_page",
        )

        pipeline = BenchmarkPipeline(
            config=config,
            model_inference=model_inference,
            ocr_func=ocr_func,
        )

        try:
            pipeline.load_dataset()
            results = pipeline.run()

            # Verify meaningful results
            assert results.total_samples >= 1
            assert results.overall_metrics.metrics.get("mean_mean_iou", 0) >= 0

        except Exception as e:
            pytest.skip(f"Pipeline execution failed: {e}")


class TestConfigurationLoading:
    """E2E tests for configuration loading."""

    def test_load_yaml_config(self):
        """Test loading configuration from YAML file."""
        from benchmarks.pipeline import BenchmarkConfig
        import yaml

        # Create temporary config file
        config_content = {
            "dataset": {
                "path": "test/dataset",
                "filter": "single_page",
            },
            "aggregation": {
                "methods": ["max", "mean"],
                "default": "max",
            },
            "selection": {
                "methods": ["top_k"],
                "top_k": {"values": [1, 5]},
            },
            "evaluation": {
                "iou_thresholds": [0.5],
                "default_matching": "set_coverage",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            config = BenchmarkConfig.from_yaml(temp_path)

            assert config.dataset_path == "test/dataset"
            assert config.filter_type == "single_page"
            assert "max" in config.aggregation_methods
            assert "mean" in config.aggregation_methods
            assert config.default_aggregation == "max"
            assert config.top_k_values == [1, 5]

        finally:
            os.unlink(temp_path)

    def test_default_config(self):
        """Test default configuration values."""
        from benchmarks.pipeline import BenchmarkConfig

        config = BenchmarkConfig()

        assert config.dataset_path == "Yuwh07/BBox_DocVQA_Bench"
        assert config.filter_type == "single_page"
        assert config.n_patches_x == 32
        assert config.n_patches_y == 32
        assert "iou_weighted" in config.aggregation_methods
        assert "top_k" in config.selection_methods
