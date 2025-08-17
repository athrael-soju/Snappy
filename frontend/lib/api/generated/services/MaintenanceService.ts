/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MaintenanceService {
    /**
     * Clear Qdrant
     * @returns any Successful Response
     * @throws ApiError
     */
    public static clearQdrantClearQdrantPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/clear/qdrant',
        });
    }
    /**
     * Clear Minio
     * @returns any Successful Response
     * @throws ApiError
     */
    public static clearMinioClearMinioPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/clear/minio',
        });
    }
    /**
     * Clear All
     * @returns any Successful Response
     * @throws ApiError
     */
    public static clearAllClearAllPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/clear/all',
        });
    }
}
