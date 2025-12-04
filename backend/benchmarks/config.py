"""
Benchmark configuration and settings.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RetrievalStrategy(str, Enum):
    """Available retrieval strategies for benchmarking."""

    SNAPPY_FULL = "snappy_full"  # ColPali + OCR + Region Relevance
    COLPALI_ONLY = "colpali_only"  # Pure ColPali retrieval
    OCR_ONLY = "ocr_only"  # Traditional OCR-based retrieval


class LLMProvider(str, Enum):
    """LLM providers for RAG answer generation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # For local models via Ollama/vLLM


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
        default_factory=lambda: [
            RetrievalStrategy.SNAPPY_FULL,
            RetrievalStrategy.COLPALI_ONLY,
            RetrievalStrategy.OCR_ONLY,
        ]
    )
    top_k: int = 5  # Number of documents to retrieve
    include_ocr: bool = True  # Include OCR data in retrieval

    # Region relevance settings (for Snappy Full)
    region_relevance_threshold: float = 0.3
    region_top_k: int = 10
    region_score_aggregation: str = "max"

    # LLM settings for RAG evaluation
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str = "gpt-5-nano"  # Default to cost-effective model
    llm_temperature: float = 0.0  # Deterministic for reproducibility
    llm_max_tokens: int = 512
    llm_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )

    # Metrics settings
    measure_latency: bool = True
    measure_tokens: bool = True
    measure_correctness: bool = True

    # Output settings
    output_dir: str = field(
        default_factory=lambda: os.environ.get(
            "BENCHMARK_OUTPUT_DIR", "./benchmark_results"
        )
    )
    save_raw_results: bool = True
    generate_report: bool = True

    # Service URLs (use environment or defaults)
    colpali_url: str = field(
        default_factory=lambda: os.environ.get("COLPALI_URL", "http://localhost:7000")
    )
    qdrant_url: str = field(
        default_factory=lambda: os.environ.get("QDRANT_URL", "http://localhost:6333")
    )
    duckdb_url: str = field(
        default_factory=lambda: os.environ.get("DUCKDB_URL", "http://localhost:8300")
    )
    minio_url: str = field(
        default_factory=lambda: os.environ.get("MINIO_URL", "http://localhost:9000")
    )
    deepseek_ocr_url: str = field(
        default_factory=lambda: os.environ.get(
            "DEEPSEEK_OCR_URL", "http://localhost:8200"
        )
    )

    # Execution settings
    batch_size: int = 10  # Process samples in batches
    num_workers: int = 4  # Parallel workers for data loading
    timeout: int = 120  # Timeout per sample in seconds
    retry_count: int = 3  # Retries on failure

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")

        if self.region_relevance_threshold < 0 or self.region_relevance_threshold > 1:
            raise ValueError("region_relevance_threshold must be between 0 and 1")

        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("llm_temperature must be between 0 and 2")

        if self.llm_provider == LLMProvider.OPENAI and not self.llm_api_key:
            raise ValueError("OpenAI API key required for OPENAI provider")

        if self.llm_provider == LLMProvider.ANTHROPIC and not self.anthropic_api_key:
            raise ValueError("Anthropic API key required for ANTHROPIC provider")

    @classmethod
    def from_env(cls) -> "BenchmarkConfig":
        """Create configuration from environment variables."""
        return cls(
            max_samples=int(os.environ.get("BENCHMARK_MAX_SAMPLES", 0)) or None,
            top_k=int(os.environ.get("BENCHMARK_TOP_K", 5)),
            llm_model=os.environ.get("BENCHMARK_LLM_MODEL", "gpt-5-nano"),
            batch_size=int(os.environ.get("BENCHMARK_BATCH_SIZE", 10)),
        )
