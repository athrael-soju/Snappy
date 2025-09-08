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
     * Stream Progress
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamProgressProgressStreamJobIdGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/progress/stream/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
