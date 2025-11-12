import { RetrievalService } from "@/lib/api/generated/services/RetrievalService";
import { parseSearchResults } from "@/lib/api/runtime";
import { logger } from '@/lib/utils/logger';

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

export async function executeDocumentSearch(query: string, k: number, includeOcr: boolean = false) {
    try {
        // Use the generated RetrievalService from OpenAPI spec
        const data = await RetrievalService.searchSearchGet(query, k, includeOcr);

        const results = parseSearchResults(data);
        const imageUrls = results
            .map((result) => result.image_url)
            .filter((url): url is string => typeof url === "string" && url.length > 0);

        return {
            success: true,
            query,
            images: imageUrls,
            results: results,
            count: imageUrls.length
        };
    } catch (error) {
        logger.error('Document search error', { error, query, k });
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error occurred',
            query
        };
    }
}
