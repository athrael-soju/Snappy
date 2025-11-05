/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Batch OCR processing result.
 */
export type OcrBatchResponse = {
    status: string;
    total_pages: number;
    successful: number;
    failed: number;
    results: Array<Record<string, any>>;
};

