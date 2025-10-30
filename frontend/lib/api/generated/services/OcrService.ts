/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_extract_document_ocr_extract_post } from '../models/Body_extract_document_ocr_extract_post';
import type { OcrDisabledResponse } from '../models/OcrDisabledResponse';
import type { OcrExtractionResponse } from '../models/OcrExtractionResponse';
import type { OcrHealthResponse } from '../models/OcrHealthResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OcrService {
    /**
     * Extract document structure with PaddleOCR-VL
     * Proxy document extraction requests to PaddleOCR-VL.
     *
     * Validates file size and extension locally before forwarding the upload.
     * @param formData
     * @returns OcrExtractionResponse Successful Response
     * @throws ApiError
     */
    public static extractDocumentOcrExtractPost(
        formData: Body_extract_document_ocr_extract_post,
    ): CancelablePromise<OcrExtractionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/extract',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Check PaddleOCR-VL health
     * Report health information about the PaddleOCR-VL integration.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static ocrHealthOcrHealthGet(): CancelablePromise<(OcrHealthResponse | OcrDisabledResponse)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/health',
        });
    }
}
