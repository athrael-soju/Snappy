"""
Snappy Benchmarking Suite

A comprehensive benchmarking framework for comparing document retrieval strategies:
- Snappy Full: ColPali + OCR + Spatially-Grounded Region Relevance Propagation
- ColPali Only: Pure vision-language model retrieval
- OCR Only: Traditional text-based retrieval

Uses the BBox_DocVQA_Bench dataset from Hugging Face for evaluation.
"""

from benchmarks.config import BenchmarkConfig
from benchmarks.runner import BenchmarkRunner

__all__ = ["BenchmarkConfig", "BenchmarkRunner"]
