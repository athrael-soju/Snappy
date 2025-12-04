"""
Benchmark configuration and settings.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RetrievalStrategy(str, Enum):
    """Available retrieval strategies for benchmarking."""

    ON_THE_FLY = "on_the_fly"  # On-the-fly OCR + filtering (no storage)


class LLMProvider(str, Enum):
    """LLM providers for RAG answer generation."""

    OPENAI = "openai"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""

    # Dataset settings
    dataset_name: str = "Yuwh07/BBox_DocVQA_Bench"
    dataset_split: str = "train"  # BBox_DocVQA_Bench uses train split
    cache_dir: str = field(
        default_factory=lambda: os.environ.get(
            "BENCHMARK_CACHE_DIR", "./benchmark_cache"
        )
    )
    max_samples: Optional[int] = None  # Limit samples for quick testing
    categories: Optional[List[str]] = None  # Filter by arxiv categories

    # Retrieval settings
    strategies: List[RetrievalStrategy] = field(
        default_factory=lambda: [RetrievalStrategy.ON_THE_FLY]
    )

    # Region relevance settings
    region_relevance_threshold: float = 0.3
    region_top_k: int = 10
    region_score_aggregation: str = "max"

    # LLM settings for RAG evaluation
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str = field(
        default_factory=lambda: os.environ.get("BENCHMARK_LLM_MODEL", "gpt-5-mini")
    )
    llm_temperature: float = 0  # Deterministic for reproducibility
    llm_max_tokens: int = 1024  # Increased for multimodal responses
    llm_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )

    # Evaluation mode
    skip_llm_evaluation: bool = False  # If True, only compute retrieval metrics (no LLM calls)

    # Output settings
    output_dir: str = field(
        default_factory=lambda: os.environ.get(
            "BENCHMARK_OUTPUT_DIR", "./benchmark_results"
        )
    )
    generate_report: bool = True

    # Service URLs (use environment or defaults)
    colpali_url: str = field(
        default_factory=lambda: os.environ.get("COLPALI_URL", "http://localhost:7000")
    )
    deepseek_ocr_url: str = field(
        default_factory=lambda: os.environ.get(
            "DEEPSEEK_OCR_URL", "http://localhost:8200"
        )
    )

    # Execution settings
    batch_size: int = 5  # Process samples in batches (reduced to prevent OCR overload)
    timeout: int = 120  # Timeout per sample in seconds

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.region_relevance_threshold < 0 or self.region_relevance_threshold > 1:
            raise ValueError("region_relevance_threshold must be between 0 and 1")

        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("llm_temperature must be between 0 and 2")

        if not self.skip_llm_evaluation and not self.llm_api_key:
            raise ValueError("OpenAI API key required (or set skip_llm_evaluation=True)")

    @classmethod
    def from_env(cls) -> "BenchmarkConfig":
        """Create configuration from environment variables."""
        return cls(
            max_samples=int(os.environ.get("BENCHMARK_MAX_SAMPLES", 0)) or None,
            batch_size=int(os.environ.get("BENCHMARK_BATCH_SIZE", 5)),
        )
