"""
Snappy Benchmarking Suite

A benchmarking framework for evaluating document retrieval with region relevance filtering.
Uses the BBox_DocVQA_Bench dataset from Hugging Face for evaluation.

Modules:
- config: Benchmark configuration and settings
- dataset: BBox_DocVQA_Bench dataset loader
- metrics: Metrics collection and aggregation
- runner: Main benchmark orchestration
- evaluation: RAG answer generation and correctness evaluation
- strategies: Retrieval strategy implementations
- reports: Report generation in multiple formats
- llm: Shared LLM client abstraction
- utils: Shared utilities (text, images)
"""

from benchmarks.config import BenchmarkConfig
from benchmarks.runner import BenchmarkRunner, run_benchmark

__all__ = ["BenchmarkConfig", "BenchmarkRunner", "run_benchmark"]
