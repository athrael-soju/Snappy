/**
 * Zod schemas for API validation
 * 
 * These schemas are used for runtime validation of API responses.
 * The actual API client uses the generated TypeScript types from lib/api/generated.
 */

import { z } from "zod";

/**
 * Schema for search result items returned by the /search endpoint
 */
export const SearchItem = z
    .object({
        image_url: z.union([z.string(), z.null()]),
        label: z.union([z.string(), z.null()]),
        payload: z.object({}).partial().passthrough(),
        score: z.union([z.number(), z.null()]).optional(),
    })
    .passthrough();

/**
 * Export all schemas for use in validation
 */
export const schemas = {
    SearchItem,
};
