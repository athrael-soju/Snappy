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
     * Clear Storage
     * @returns any Successful Response
     * @throws ApiError
     */
    public static clearStorageClearMinioPost(): CancelablePromise<any> {
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
    /**
     * Initialize
     * @returns any Successful Response
     * @throws ApiError
     */
    public static initializeInitializePost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/initialize',
        });
    }
    /**
     * Delete Collection And Bucket
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCollectionAndBucketDeleteDelete(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/delete',
        });
    }
    /**
     * Get Status
     * Get the status of collection and bucket including statistics.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getStatusStatusGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/status',
        });
    }
}
