/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to process a single page.
 */
export type OcrPageRequest = {
    /**
     * Document filename in storage
     */
    filename: string;
    /**
     * Page number to process
     */
    page_number: number;
    /**
     * OCR mode (Gundam, Tiny, etc.)
     */
    mode?: (string | null);
    /**
     * Task type (markdown, plain_ocr, etc.)
     */
    task?: (string | null);
    /**
     * Custom prompt for custom tasks
     */
    custom_prompt?: (string | null);
};

