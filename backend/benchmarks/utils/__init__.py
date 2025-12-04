"""
Shared utilities for the benchmarks module.
"""

from benchmarks.utils.images import decode_base64_image, encode_image_base64
from benchmarks.utils.text import compute_f1_score, normalize_answer

__all__ = [
    "normalize_answer",
    "compute_f1_score",
    "encode_image_base64",
    "decode_base64_image",
]
