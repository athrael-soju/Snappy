"""
Text processing utilities for benchmarks.
"""

import re
import string


def normalize_answer(text: str) -> str:
    """
    Normalize answer text for comparison.

    Applies standard text normalization:
    - Lowercase conversion
    - Punctuation removal
    - Article removal (a, an, the)
    - Whitespace normalization

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text string
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove articles
    text = re.sub(r"\b(a|an|the)\b", " ", text)

    # Remove extra whitespace
    text = " ".join(text.split())

    return text.strip()


def compute_f1_score(prediction: str, ground_truth: str) -> float:
    """
    Compute token-level F1 score between prediction and ground truth.

    Args:
        prediction: Model-generated answer
        ground_truth: Ground truth answer

    Returns:
        F1 score between 0.0 and 1.0
    """
    pred_tokens = set(normalize_answer(prediction).split())
    gt_tokens = set(normalize_answer(ground_truth).split())

    if not pred_tokens or not gt_tokens:
        return 0.0

    common = pred_tokens & gt_tokens
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)

    return 2 * precision * recall / (precision + recall)
