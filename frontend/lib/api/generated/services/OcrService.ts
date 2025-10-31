/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_run_ocr_ocr_infer_post } from '../models/Body_run_ocr_ocr_infer_post';
import type { OCRDefaults } from '../models/OCRDefaults';
import type { OCRHealth } from '../models/OCRHealth';
import type { OCRPresets } from '../models/OCRPresets';
import type { OCRResponse } from '../models/OCRResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class OcrService {
    /**
     * Get Defaults
     * Return the configured default values used when optional OCR fields are omitted.
     * @returns OCRDefaults Successful Response
     * @throws ApiError
     */
    public static getDefaultsOcrDefaultsGet(): CancelablePromise<OCRDefaults> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/defaults',
        });
    }
    /**
     * Health
     * Surface the health status of the DeepSeek OCR service.
     * @returns OCRHealth Successful Response
     * @throws ApiError
     */
    public static healthOcrHealthGet(): CancelablePromise<OCRHealth> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/health',
        });
    }
    /**
     * Info
     * Expose metadata returned by the DeepSeek OCR service.
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
     * Presets
     * Expose available profile and task presets from the OCR service.
     * @returns OCRPresets Successful Response
     * @throws ApiError
     */
    public static presetsOcrPresetsGet(): CancelablePromise<OCRPresets> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/ocr/presets',
        });
    }
    /**
     * Run Ocr
     * Proxy OCR requests to the DeepSeek OCR service with Snappy defaults.
     * @param formData
     * @returns OCRResponse Successful Response
     * @throws ApiError
     */
    public static runOcrOcrInferPost(
        formData: Body_run_ocr_ocr_infer_post,
    ): CancelablePromise<OCRResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ocr/infer',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
