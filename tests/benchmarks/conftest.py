"""
Pytest configuration for benchmark tests.

This file contains fixtures and markers for the benchmark test suite.
"""

import pytest


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require external resources)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take significant time)"
    )
    config.addinivalue_line(
        "markers", "model_required: marks tests that require real model inference"
    )


@pytest.fixture
def sample_patch_scores():
    """Fixture providing sample patch scores for testing."""
    import numpy as np

    return np.array([
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 0.1, 0.2],
        [0.3, 0.4, 0.5, 0.6],
    ], dtype=np.float32)


@pytest.fixture
def sample_boxes():
    """Fixture providing sample bounding boxes for testing."""
    from benchmarks.utils.coordinates import Box

    return [
        Box(x1=0.0, y1=0.0, x2=0.5, y2=0.5),
        Box(x1=0.5, y1=0.0, x2=1.0, y2=0.5),
        Box(x1=0.0, y1=0.5, x2=0.5, y2=1.0),
        Box(x1=0.5, y1=0.5, x2=1.0, y2=1.0),
    ]


@pytest.fixture
def sample_scored_regions():
    """Fixture providing sample scored regions for testing."""
    return [
        (0, 0.9),
        (1, 0.7),
        (2, 0.5),
        (3, 0.3),
        (4, 0.1),
    ]


@pytest.fixture
def synthetic_bbox_sample():
    """Fixture providing a synthetic BBoxDocVQA sample for testing."""
    from benchmarks.loaders.bbox_docvqa import (
        BBoxDocVQASample,
        ComplexityType,
        GroundTruthBox,
    )
    from benchmarks.utils.coordinates import Box

    return BBoxDocVQASample(
        sample_id="test_sample_1",
        question="What is the title of the document?",
        answer="Test Document",
        document_id="doc_1",
        page_indices=[0],
        ground_truth_boxes=[
            GroundTruthBox(
                box=Box(x1=0.1, y1=0.05, x2=0.9, y2=0.15),
                page_idx=0,
            ),
        ],
        complexity=ComplexityType.SPSBB,
    )
