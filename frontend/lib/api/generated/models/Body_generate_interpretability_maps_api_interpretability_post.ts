/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Body_generate_interpretability_maps_api_interpretability_post = {
    /**
     * Query text to interpret
     */
    query: string;
    /**
     * Document image to analyze
     */
    file?: (Blob | null);
    /**
     * URL of the image to analyze
     */
    image_url?: (string | null);
};

