/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SearchItem } from '../models/SearchItem';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RetrievalService {
    /**
     * Search
     * @param q User query
     * @param k
     * @param includeOcr Include OCR results if available
     * @returns SearchItem Successful Response
     * @throws ApiError
     */
    public static searchSearchGet(
        q: string,
        k?: (number | null),
        includeOcr: boolean = false,
    ): CancelablePromise<Array<SearchItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/search',
            query: {
                'q': q,
                'k': k,
                'include_ocr': includeOcr,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Heatmap
     * Generate attention heatmap for a query-image pair.
     *
     * Fetches the image from the provided URL, generates an attention heatmap
     * using the ColPali service, and returns a PNG image with the heatmap overlay.
     *
     * The heatmap visualizes which regions of the document are most relevant
     * to the search query based on the ColPali model's late interaction attention.
     *
     * Args:
     * image_url: URL of the document page image (typically from MinIO)
     * query: The search query to visualize attention for
     * alpha: Heatmap overlay transparency (0=invisible, 1=opaque)
     *
     * Returns:
     * PNG image with heatmap overlay
     * @param imageUrl URL of the document page image
     * @param query Search query text
     * @param alpha Heatmap transparency
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getHeatmapHeatmapGet(
        imageUrl: string,
        query: string,
        alpha: number = 0.5,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/heatmap',
            query: {
                'image_url': imageUrl,
                'query': query,
                'alpha': alpha,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
