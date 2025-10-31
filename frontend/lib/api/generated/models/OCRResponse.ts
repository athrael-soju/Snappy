/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OCRBoundingBox } from './OCRBoundingBox';
import type { OCRFigure } from './OCRFigure';
import type { OCRMetadata } from './OCRMetadata';
export type OCRResponse = {
    success?: boolean;
    text: string;
    raw_text: string;
    markdown?: (string | null);
    boxes: Array<OCRBoundingBox>;
    figures?: Array<OCRFigure>;
    image_dims: Record<string, (number | null)>;
    metadata: OCRMetadata;
};

