/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OcrBatchRequest } from '../models/OcrBatchRequest';
import type { OcrBatchResponse } from '../models/OcrBatchResponse';
import type { OcrDocumentRequest } from '../models/OcrDocumentRequest';
import type { OcrPageRequest } from '../models/OcrPageRequest';
import type { OcrResponse } from '../models/OcrResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OcrService {
    /**
     * Process Page
     * Process a single document page with DeepSeek OCR.
     * @param requestBody
     * @returns OcrResponse Successful Response
     * @throws ApiError
     */
    public static processPageOcrProcessPagePost(
        requestBody: OcrPageRequest,
    ): CancelablePromise<OcrResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/process-page',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Process Batch
     * Process multiple pages from the same document in parallel.
     * @param requestBody
     * @returns OcrBatchResponse Successful Response
     * @throws ApiError
     */
    public static processBatchOcrProcessBatchPost(
        requestBody: OcrBatchRequest,
    ): CancelablePromise<OcrBatchResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/process-batch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Process Document
     * Process all pages of an indexed document with OCR.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static processDocumentOcrProcessDocumentPost(
        requestBody: OcrDocumentRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/process-document',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Health Check
     * Check OCR service health.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthCheckOcrHealthGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/health',
        });
    }
    /**
     * Get Progress
     * Get OCR processing progress for a job.
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getProgressOcrProgressJobIdGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/progress/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Stream Progress
     * Stream OCR processing progress via Server-Sent Events.
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamProgressOcrProgressStreamJobIdGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/progress/stream/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Job
     * Cancel a running OCR job.
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelJobOcrCancelJobIdPost(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/cancel/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
