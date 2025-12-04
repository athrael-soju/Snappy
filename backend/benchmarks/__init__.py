"""
Snappy Benchmarking Suite

A benchmarking framework for evaluating document retrieval with region relevance filtering.
Uses the BBox_DocVQA_Bench dataset from Hugging Face for evaluation.
"""

from benchmarks.config import BenchmarkConfig
from benchmarks.runner import BenchmarkRunner

__all__ = ["BenchmarkConfig", "BenchmarkRunner"]
