/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FilesService {
    /**
     * Serve File
     * Serve files from local storage.
     *
     * Security measures:
     * - Validates bucket name matches configured bucket
     * - Resolves path and ensures it stays within storage directory
     * - Returns appropriate content types
     * @param bucket
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static serveFileFilesBucketPathGet(
        bucket: string,
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/files/{bucket}/{path}',
            path: {
                'bucket': bucket,
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
