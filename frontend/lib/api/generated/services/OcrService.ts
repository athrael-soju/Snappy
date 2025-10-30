/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_extract_document_ocr_extract_post } from '../models/Body_extract_document_ocr_extract_post';
import type { OCRExtractionResponse } from '../models/OCRExtractionResponse';
import type { OCRHealthResponse } from '../models/OCRHealthResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OcrService {
    /**
     * Check PaddleOCR-VL service health
     * Forward a health probe to the OCR microservice.
     * @returns OCRHealthResponse Successful Response
     * @throws ApiError
     */
    public static healthOcrHealthGet(): CancelablePromise<OCRHealthResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/health',
        });
    }
    /**
     * Fetch PaddleOCR-VL service metadata
     * Return root metadata from the OCR microservice.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static infoOcrInfoGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/info',
        });
    }
    /**
     * Extract structured OCR data from a document
     * Upload a document and return the structured OCR response.
     * @param formData
     * @returns OCRExtractionResponse Successful Response
     * @throws ApiError
     */
    public static extractDocumentOcrExtractPost(
        formData: Body_extract_document_ocr_extract_post,
    ): CancelablePromise<OCRExtractionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/extract',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                413: `File too large`,
                422: `Validation Error`,
                503: `Service disabled or unavailable`,
            },
        });
    }
}
