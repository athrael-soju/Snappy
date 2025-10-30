/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type OcrElement = {
    /**
     * Element index in the document response
     */
    index: number;
    /**
     * Content payload returned by PaddleOCR-VL
     */
    content?: Record<string, any>;
    /**
     * Metadata (bbox, confidence, type, etc.)
     */
    metadata?: Record<string, any>;
};

