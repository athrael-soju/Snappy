/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Database statistics.
 */
export type StatsResponse = {
    total_documents: number;
    total_pages: number;
    total_regions: number;
    total_extracted_images: number;
    providers: Record<string, number>;
    storage_size_mb: number;
};

