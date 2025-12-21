import type { InterpretabilityData } from '@/components/interpretability-heatmap';
import { InterpretabilityService } from './generated';

/**
 * Generate interpretability maps for a query-image pair
 * Shows which document regions contribute to similarity scores for each query token
 *
 * @param query - The query text to interpret
 * @param imageUrl - The URL of the image to analyze
 * @returns Promise<InterpretabilityData>
 */
export async function generateInterpretabilityMaps(
  query: string,
  imageUrl: string
): Promise<InterpretabilityData> {
  // Use the generated SDK - backend reads image directly from local storage
  const result = await InterpretabilityService.generateInterpretabilityMapsApiInterpretabilityPost({
    query,
    image_url: imageUrl,
  });

  return result as InterpretabilityData;
}
