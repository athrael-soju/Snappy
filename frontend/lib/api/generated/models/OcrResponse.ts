/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * OCR processing result.
 */
export type OcrResponse = {
    status: string;
    filename: string;
    page_number: number;
    storage_url: string;
    text_preview: string;
    regions: number;
    extracted_images: number;
};

