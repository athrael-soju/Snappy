/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type OCRMetadata = {
    /**
     * OCR mode used for the request.
     */
    mode: string;
    /**
     * Whether grounding boxes were enabled for the request.
     */
    grounding: boolean;
    /**
     * Base resize dimension passed to the model.
     */
    base_size: number;
    /**
     * Image size parameter passed to the model.
     */
    image_size: number;
    /**
     * Crop mode flag used during inference.
     */
    crop_mode: boolean;
    /**
     * Whether captions were requested.
     */
    include_caption: boolean;
    /**
     * Elapsed time reported by the OCR service in milliseconds.
     */
    elapsed_ms?: (number | null);
};

