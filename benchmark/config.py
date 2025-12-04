"""
Configuration for benchmark module.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""

    # Dataset settings
    dataset_name: str = "Yuwh07/BBox_DocVQA_Bench"
    dataset_cache_dir: str = field(
        default_factory=lambda: str(Path.home() / ".cache" / "snappy_benchmark")
    )

    # Service URLs (inherit from environment or use defaults)
    colpali_url: str = field(
        default_factory=lambda: os.getenv("COLPALI_URL", "http://localhost:7000")
    )
    ocr_url: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_OCR_URL", "http://localhost:8200")
    )
    llm_url: str = field(
        default_factory=lambda: os.getenv("LLM_URL", "http://localhost:8000")
    )

    # OCR settings
    ocr_mode: str = "Base"
    ocr_task: str = "markdown"
    ocr_include_grounding: bool = True

    # Region relevance settings
    relevance_threshold: float = 0.3
    relevance_aggregation: str = "max"
    region_top_k: int = 0  # 0 = no limit

    # LLM settings for downstream RAG
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024

    # Output settings
    output_dir: str = field(
        default_factory=lambda: str(Path.cwd() / "benchmark_results")
    )

    # Execution settings
    max_samples: Optional[int] = None  # None = all samples
    batch_size: int = 1  # Process one at a time for accurate timing
    verbose: bool = True


def load_config(**overrides) -> BenchmarkConfig:
    """Load benchmark configuration with optional overrides."""
    return BenchmarkConfig(**overrides)
