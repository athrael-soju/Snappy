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
     * @returns SearchItem Successful Response
     * @throws ApiError
     */
    public static searchSearchGet(
        q: string,
        k: number = 5,
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
}
