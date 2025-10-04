/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_index_index_post } from '../models/Body_index_index_post';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class IndexingService {
    /**
     * Index
     * Upload and index files. Returns 202 Accepted with job_id.
     * Use /sse/ingestion/{job_id} to track progress.
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static indexIndexPost(
        formData: Body_index_index_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/index',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Stream Ingestion Progress
     * Server-Sent Events endpoint for ingestion progress.
     * Returns events: queued, intake, image, embed, index, storage, completed, error.
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamIngestionProgressSseIngestionJobIdGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/sse/ingestion/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Ingestion
     * Cancel an ongoing ingestion job (best effort).
     * Note: Cancellation is not fully implemented in the concurrent pipeline yet.
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelIngestionIndexCancelJobIdPost(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/index/cancel/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
