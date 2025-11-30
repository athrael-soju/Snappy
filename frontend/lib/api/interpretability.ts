import { baseUrl } from './client';
import type { InterpretabilityData } from '@/components/interpretability-heatmap';

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
  // Fetch the image as a blob
  const imageResponse = await fetch(imageUrl);
  if (!imageResponse.ok) {
    throw new Error(`Failed to fetch image: ${imageResponse.statusText}`);
  }
  const imageBlob = await imageResponse.blob();

  // Create form data
  const formData = new FormData();
  formData.append('query', query);
  formData.append('file', imageBlob, 'image.png');

  // Call the ColPali interpretability endpoint via backend proxy
  const response = await fetch(`${baseUrl}/api/interpretability`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Interpretability request failed: ${error}`);
  }

  return response.json();
}
