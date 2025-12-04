"""
Benchmark module for evaluating Spatially-Grounded Document Retrieval.

This module compares three approaches:
1. OCR-only: Returns all OCR regions without filtering
2. ColPali-only: Uses ColPali embeddings without region-level filtering
3. Snappy Spatial Grounding: Uses interpretability maps to filter relevant regions

Based on the research paper: https://arxiv.org/pdf/2512.02660
Dataset: BBox_DocVQA_Bench from HuggingFace
"""

__version__ = "0.1.0"
