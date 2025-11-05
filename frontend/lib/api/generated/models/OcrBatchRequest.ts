/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to process multiple pages.
 */
export type OcrBatchRequest = {
    /**
     * Document filename in storage
     */
    filename: string;
    /**
     * Page numbers to process
     */
    page_numbers: Array<number>;
    mode?: (string | null);
    task?: (string | null);
    max_workers?: (number | null);
};

