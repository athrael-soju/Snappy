import { useCallback, useEffect, useRef, useState } from "react";
import { generateInterpretabilityMaps } from "@/lib/api/interpretability";
import type { InterpretabilityData } from "@/components/interpretability-heatmap";
import type { ColorScale } from "@/components/interpretability-heatmap";
import type { NormalizationStrategy } from "@/lib/utils/normalization";

// Maximum number of cached interpretability results
const MAX_CACHE_SIZE = 20;

export function useInterpretability(query?: string, src?: string) {
  // Persistent cache across dialog open/close cycles
  const cacheRef = useRef<Map<string, InterpretabilityData>>(new Map());
  // Track if we've already attempted to fetch for this query/src combo
  const fetchAttemptedRef = useRef<string | null>(null);

  const [interpretabilityData, setInterpretabilityData] =
    useState<InterpretabilityData | null>(null);
  const [selectedToken, setSelectedToken] = useState<number | null>(null);
  const [colorScale, setColorScale] = useState<ColorScale>("YlOrRd");
  const [normalizationStrategy, setNormalizationStrategy] =
    useState<NormalizationStrategy>("minmax");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preferences from localStorage on mount (client-side only)
  useEffect(() => {
    const storedColorScale = localStorage.getItem("interpretability-color-scale");
    const storedNormalization = localStorage.getItem(
      "interpretability-normalization-strategy"
    );

    if (storedColorScale) {
      setColorScale(storedColorScale as ColorScale);
    }
    if (storedNormalization) {
      setNormalizationStrategy(storedNormalization as NormalizationStrategy);
    }
  }, []);

  // Save color scale to localStorage
  useEffect(() => {
    localStorage.setItem("interpretability-color-scale", colorScale);
  }, [colorScale]);

  // Save normalization strategy to localStorage
  useEffect(() => {
    localStorage.setItem(
      "interpretability-normalization-strategy",
      normalizationStrategy
    );
  }, [normalizationStrategy]);

  const fetchInterpretability = useCallback(async () => {
    if (!query || !src) {
      setError("Query and source are required");
      return;
    }

    // Create cache key from query and src
    const cacheKey = `${query}::${src}`;

    // Prevent duplicate fetches for the same query/src
    if (fetchAttemptedRef.current === cacheKey) {
      return;
    }

    // Check cache first
    const cachedData = cacheRef.current.get(cacheKey);
    if (cachedData) {
      setInterpretabilityData(cachedData);
      fetchAttemptedRef.current = cacheKey;
      // Auto-select the first token to show the heatmap immediately
      if (cachedData.tokens && cachedData.tokens.length > 0) {
        setSelectedToken(0);
      }
      return;
    }

    // Mark as attempted before fetching
    fetchAttemptedRef.current = cacheKey;
    setLoading(true);
    setError(null);

    try {
      const data = await generateInterpretabilityMaps(query, src);
      setInterpretabilityData(data);

      // Store in cache with LRU eviction
      if (cacheRef.current.size >= MAX_CACHE_SIZE) {
        // Remove oldest entry (first entry in Map)
        const firstKey = cacheRef.current.keys().next().value;
        if (firstKey !== undefined) {
          cacheRef.current.delete(firstKey);
        }
      }
      cacheRef.current.set(cacheKey, data);

      // Auto-select the first token to show the heatmap immediately
      if (data.tokens && data.tokens.length > 0) {
        setSelectedToken(0);
      }
    } catch (err) {
      setError(
        `Failed to load interpretability: ${err instanceof Error ? err.message : String(err)}`
      );
    } finally {
      setLoading(false);
    }
  }, [query, src]);

  const reset = useCallback(() => {
    setInterpretabilityData(null);
    setSelectedToken(null);
    setError(null);
    // Reset the fetch attempt tracker so we can retry on next open
    fetchAttemptedRef.current = null;
    // Note: We intentionally do NOT clear the cache on reset
    // This allows reusing cached data when reopening the same image
  }, []);

  const clearCache = () => {
    cacheRef.current.clear();
  };

  return {
    interpretabilityData,
    selectedToken,
    setSelectedToken,
    colorScale,
    setColorScale,
    normalizationStrategy,
    setNormalizationStrategy,
    loading,
    error,
    fetchInterpretability,
    reset,
    clearCache,
  };
}
