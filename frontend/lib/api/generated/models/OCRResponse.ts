/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OCRBoundingBox } from './OCRBoundingBox';
import type { OCRMetadata } from './OCRMetadata';
export type OCRResponse = {
    success?: boolean;
    text: string;
    raw_text: string;
    boxes: Array<OCRBoundingBox>;
    image_dims: Record<string, (number | null)>;
    metadata: OCRMetadata;
};

