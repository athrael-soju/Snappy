/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request for similarity map generation.
 */
export type SimilarityMapRequest = {
    image_url: string;
    query: string;
    selected_tokens?: (Array<number> | null);
    alpha?: number;
};

