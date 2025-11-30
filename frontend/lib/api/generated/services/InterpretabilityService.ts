/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_generate_interpretability_maps_api_interpretability_post } from '../models/Body_generate_interpretability_maps_api_interpretability_post';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class InterpretabilityService {
    /**
     * Generate Interpretability Maps
     * Generate interpretability maps showing query-document token correspondence.
     *
     * This endpoint is separate from the search pipeline to avoid performance impact.
     * It shows which document regions contribute to similarity scores for each query token.
     *
     * Args:
     * query: The query text to interpret
     * file: The document image to analyze
     * colpali_client: Injected ColPali client dependency
     *
     * Returns:
     * Dictionary containing:
     * - query: Original query text
     * - tokens: List of query tokens (filtered)
     * - similarity_maps: Per-token similarity maps
     * - n_patches_x: Number of patches in x dimension
     * - n_patches_y: Number of patches in y dimension
     * - image_width: Original image width
     * - image_height: Original image height
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static generateInterpretabilityMapsApiInterpretabilityPost(
        formData: Body_generate_interpretability_maps_api_interpretability_post,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/interpretability',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
