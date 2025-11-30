import { baseUrl } from './client';
import type { InterpretabilityData } from '@/components/interpretability-heatmap';

/**
 * Convert a data URL to a Blob
 */
function dataUrlToBlob(dataUrl: string): Blob {
  const [header, base64Data] = dataUrl.split(',');
  const mimeMatch = header.match(/:(.*?);/);
  const mimeType = mimeMatch ? mimeMatch[1] : 'image/webp';
  const byteString = atob(base64Data);
  const arrayBuffer = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    arrayBuffer[i] = byteString.charCodeAt(i);
  }
  return new Blob([arrayBuffer], { type: mimeType });
}

/**
 * Generate interpretability maps for a query-image pair
 * Shows which document regions contribute to similarity scores for each query token
 *
 * @param query - The query text to interpret
 * @param imageUrl - The URL or data URI of the image to analyze
 * @returns Promise<InterpretabilityData>
 */
export async function generateInterpretabilityMaps(
  query: string,
  imageUrl: string
): Promise<InterpretabilityData> {
  let imageBlob: Blob;

  // Check if this is a data URL (inline image)
  if (imageUrl.startsWith('data:')) {
    imageBlob = dataUrlToBlob(imageUrl);
  } else {
    // Fetch the image from URL
    const imageResponse = await fetch(imageUrl);
    if (!imageResponse.ok) {
      throw new Error(`Failed to fetch image: ${imageResponse.statusText}`);
    }
    imageBlob = await imageResponse.blob();
  }

  // Create form data
  const formData = new FormData();
  formData.append('query', query);
  formData.append('file', imageBlob, 'image.webp');

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
