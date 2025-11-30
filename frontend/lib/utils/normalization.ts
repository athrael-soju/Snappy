import {
  quantile,
  min,
  max,
  mean,
  standardDeviation,
  medianAbsoluteDeviation,
  median,
  interquartileRange,
} from "simple-statistics";

export type NormalizationStrategy =
  | "percentile"
  | "minmax"
  | "robust"
  | "zscore"
  | "mad";

/**
 * Normalize values based on the specified strategy
 *
 * @param values - Array of numeric values to normalize
 * @param strategy - Normalization strategy to use
 * @returns Object with min and max bounds for normalization
 *
 * Strategies:
 * - percentile: 2nd-98th percentile (robust to outliers, good default)
 * - minmax: Full range (preserves all information but may be noisy)
 * - robust: IQR-based (25th-75th percentile, very resistant to outliers)
 * - zscore: Z-score normalization (mean-centered, ±3σ scaled)
 * - mad: Median Absolute Deviation (most robust to outliers, excellent for similarity maps)
 */
export function normalizeValues(
  values: number[],
  strategy: NormalizationStrategy
): { min: number; max: number } {
  switch (strategy) {
    case "percentile": {
      // Use 2nd and 98th percentile for better outlier handling
      const minVal = quantile(values, 0.02);
      const maxVal = quantile(values, 0.98);
      return { min: minVal, max: maxVal };
    }

    case "minmax": {
      // Full range normalization
      return {
        min: min(values),
        max: max(values),
      };
    }

    case "robust": {
      // IQR-based normalization using interquartile range
      const q1 = quantile(values, 0.25);
      const q3 = quantile(values, 0.75);
      return { min: q1, max: q3 };
    }

    case "zscore": {
      // Z-score: normalize around mean with ±3 standard deviations
      const meanVal = mean(values);
      const stdDev = standardDeviation(values);
      return {
        min: meanVal - 3 * stdDev,
        max: meanVal + 3 * stdDev,
      };
    }

    case "mad": {
      // MAD (Median Absolute Deviation): Most robust to outliers
      // Center around median, scale by MAD (using constant 1.4826 for normal distribution)
      const medianVal = median(values);
      const mad = medianAbsoluteDeviation(values);
      // Scale factor k=3 for ±3 MAD (similar to ±3σ for z-score)
      const k = 3;
      const scaledMAD = k * 1.4826 * mad;
      return {
        min: medianVal - scaledMAD,
        max: medianVal + scaledMAD,
      };
    }

    default: {
      // Fallback to percentile if unknown strategy
      const minVal = quantile(values, 0.02);
      const maxVal = quantile(values, 0.98);
      return { min: minVal, max: maxVal };
    }
  }
}

/**
 * Get display name for normalization strategy
 */
export function getNormalizationStrategyLabel(
  strategy: NormalizationStrategy
): string {
  const labels: Record<NormalizationStrategy, string> = {
    percentile: "Percentile (2-98%)",
    minmax: "Min-Max",
    robust: "Robust (IQR)",
    zscore: "Z-Score",
    mad: "MAD (Median)",
  };
  return labels[strategy];
}

/**
 * Get description for normalization strategy
 */
export function getNormalizationStrategyDescription(
  strategy: NormalizationStrategy
): string {
  const descriptions: Record<NormalizationStrategy, string> = {
    percentile: "Robust to outliers, good general purpose default",
    minmax: "Full range, preserves all information but may be noisy",
    robust: "IQR-based, very resistant to outliers",
    zscore: "Mean-centered with standard deviation scaling",
    mad: "Most robust to outliers, excellent for similarity maps",
  };
  return descriptions[strategy];
}
