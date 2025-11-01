/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { HeatmapResult } from '../models/HeatmapResult';
import type { SearchItem } from '../models/SearchItem';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RetrievalService {
    /**
     * Search
     * @param q User query
     * @param k
     * @returns SearchItem Successful Response
     * @throws ApiError
     */
    public static searchSearchGet(
        q: string,
        k?: (number | null),
    ): CancelablePromise<Array<SearchItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/search',
            query: {
                'q': q,
                'k': k,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate a similarity heatmap for a retrieved page
     * @param documentId
     * @param q Original search query
     * @param aggregate Aggregation strategy for query-token similarities (max, mean, sum)
     * @returns HeatmapResult Successful Response
     * @throws ApiError
     */
    public static searchHeatmapSearchDocumentIdHeatmapGet(
        documentId: string,
        q: string,
        aggregate: string = 'max',
    ): CancelablePromise<HeatmapResult> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/search/{document_id}/heatmap',
            path: {
                'document_id': documentId,
            },
            query: {
                'q': q,
                'aggregate': aggregate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
