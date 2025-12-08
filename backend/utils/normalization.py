"""
Normalization strategies for heatmap visualization.

Ports the frontend normalization strategies from TypeScript to Python.
"""

from enum import Enum
from typing import List, Tuple, Union

import numpy as np


class NormalizationStrategy(str, Enum):
    """Available normalization strategies for heatmap values."""

    PERCENTILE = "percentile"  # 2nd-98th percentile (robust to outliers, good default)
    MINMAX = "minmax"  # Full range (preserves all info but may be noisy)
    ROBUST = "robust"  # IQR-based (25th-75th percentile, very resistant to outliers)
    ZSCORE = "zscore"  # Mean-centered with standard deviation scaling
    MAD = "mad"  # Median Absolute Deviation (most robust to outliers)


def normalize_bounds(
    values: Union[np.ndarray, List[float]],
    strategy: NormalizationStrategy = NormalizationStrategy.PERCENTILE,
) -> Tuple[float, float]:
    """
    Calculate normalization bounds based on the specified strategy.

    Args:
        values: Array of numeric values to analyze
        strategy: Normalization strategy to use

    Returns:
        Tuple of (min_bound, max_bound) for normalization

    Strategies:
    - percentile: 2nd-98th percentile (robust to outliers, good default)
    - minmax: Full range (preserves all information but may be noisy)
    - robust: IQR-based (25th-75th percentile, very resistant to outliers)
    - zscore: Z-score normalization (mean-centered, +/-3 sigma scaled)
    - mad: Median Absolute Deviation (most robust to outliers)
    """
    arr = np.asarray(values).flatten()

    if len(arr) == 0:
        return 0.0, 1.0

    if strategy == NormalizationStrategy.PERCENTILE:
        min_val = float(np.percentile(arr, 2))
        max_val = float(np.percentile(arr, 98))
        return min_val, max_val

    elif strategy == NormalizationStrategy.MINMAX:
        return float(np.min(arr)), float(np.max(arr))

    elif strategy == NormalizationStrategy.ROBUST:
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        return q1, q3

    elif strategy == NormalizationStrategy.ZSCORE:
        mean_val = float(np.mean(arr))
        std_dev = float(np.std(arr))
        if std_dev == 0:
            return mean_val - 1, mean_val + 1
        return mean_val - 3 * std_dev, mean_val + 3 * std_dev

    elif strategy == NormalizationStrategy.MAD:
        median_val = float(np.median(arr))
        # MAD = median(|x - median(x)|)
        mad = float(np.median(np.abs(arr - median_val)))
        if mad == 0:
            return median_val - 1, median_val + 1
        # Scale factor k=3 for +/-3 MAD (similar to +/-3 sigma for z-score)
        # 1.4826 is the consistency constant for normal distribution
        k = 3
        scaled_mad = k * 1.4826 * mad
        return median_val - scaled_mad, median_val + scaled_mad

    else:
        # Fallback to percentile
        min_val = float(np.percentile(arr, 2))
        max_val = float(np.percentile(arr, 98))
        return min_val, max_val


def normalize_array(
    values: np.ndarray,
    strategy: NormalizationStrategy = NormalizationStrategy.PERCENTILE,
    clip: bool = True,
) -> np.ndarray:
    """
    Normalize an array to [0, 1] range using the specified strategy.

    Args:
        values: Array of values to normalize
        strategy: Normalization strategy to use
        clip: Whether to clip values outside [0, 1] after normalization

    Returns:
        Normalized array with values in [0, 1] range
    """
    min_bound, max_bound = normalize_bounds(values, strategy)

    if max_bound <= min_bound:
        return np.zeros_like(values, dtype=np.float32)

    normalized = (values - min_bound) / (max_bound - min_bound)

    if clip:
        normalized = np.clip(normalized, 0.0, 1.0)

    return normalized.astype(np.float32)


def get_strategy_label(strategy: NormalizationStrategy) -> str:
    """Get display name for normalization strategy."""
    labels = {
        NormalizationStrategy.PERCENTILE: "Percentile (2-98%)",
        NormalizationStrategy.MINMAX: "Min-Max",
        NormalizationStrategy.ROBUST: "Robust (IQR)",
        NormalizationStrategy.ZSCORE: "Z-Score",
        NormalizationStrategy.MAD: "MAD (Median)",
    }
    return labels.get(strategy, str(strategy))


def get_strategy_description(strategy: NormalizationStrategy) -> str:
    """Get description for normalization strategy."""
    descriptions = {
        NormalizationStrategy.PERCENTILE: "Robust to outliers, good general purpose default",
        NormalizationStrategy.MINMAX: "Full range, preserves all information but may be noisy",
        NormalizationStrategy.ROBUST: "IQR-based, very resistant to outliers",
        NormalizationStrategy.ZSCORE: "Mean-centered with standard deviation scaling",
        NormalizationStrategy.MAD: "Most robust to outliers, excellent for similarity maps",
    }
    return descriptions.get(strategy, "")
