import { RetrievalService } from "@/lib/api/generated/services/RetrievalService";
import { parseSearchResults } from "@/lib/api/runtime";
import { logger } from '@/lib/utils/logger';

export const documentSearchTool = {
    type: "function" as const,
    strict: false,
    name: "document_search",
    description: "Search for relevant documents and images based on a query. Returns citation labels (e.g., 'report.pdf - Page 2 of 10') that should be used when citing sources in your response. The actual document images will be provided separately in the conversation.",
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
        const labels = results
            .map((result) => result.label)
            .filter((label): label is string => typeof label === "string" && label.length > 0);

        return {
            success: true,
            query,
            labels: labels,
            count: labels.length
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
