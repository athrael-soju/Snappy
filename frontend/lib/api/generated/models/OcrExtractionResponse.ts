/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OcrElement } from './OcrElement';
export type OcrExtractionResponse = {
    /**
     * Whether the OCR processing succeeded
     */
    success: boolean;
    /**
     * Status message from PaddleOCR-VL
     */
    message: string;
    /**
     * Processing time in seconds
     */
    processing_time: number;
    /**
     * Extracted OCR elements
     */
    elements?: Array<OcrElement>;
    /**
     * Markdown representation of the extracted content
     */
    markdown?: (string | null);
    /**
     * Timestamp emitted by PaddleOCR-VL
     */
    timestamp?: (string | null);
};

