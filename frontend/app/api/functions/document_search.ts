import { NextRequest } from 'next/server';

export const documentSearchTool = {
  type: "function" as const,
  strict: false,
  name: "document_search",
  description: "Search for relevant documents and images based on a query. Returns image URLs from the backend search API.",
  parameters: {
    type: "object" as const,
    properties: {
      query: {
        type: "string" as const,
        description: "The search query to find relevant documents and images"
      }
    },
    required: ["query"]
  }
};

export async function executeDocumentSearch(query: string, k: number) {
  try {
    // Call your backend /search API - GET request with query parameters
    
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const searchParams = new URLSearchParams({
      q: query,
      k: k.toString()
    });
    const response = await fetch(`${backendUrl}/search?${searchParams}`);
    if (!response.ok) {
      throw new Error(`Search API error: ${response.status}`);
    }

    const data = await response.json();

    // Backend returns array of SearchItem directly
    const imageUrls = data.map((result: any) => result.image_url).filter(Boolean);
    const results = data.map((result: any) => ({
      image_url: result.image_url,
      label: result.label,
      score: result.score,
      payload: result.payload
    }));

    return {
      success: true,
      query,
      images: imageUrls,
      results: results,
      count: imageUrls.length
    };
  } catch (error) {
    console.error('Document search error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      query
    };
  }
}
