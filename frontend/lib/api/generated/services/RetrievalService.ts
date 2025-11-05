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
}
