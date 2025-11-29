/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SimilarityMapResult } from './SimilarityMapResult';
import type { TokenInfo } from './TokenInfo';
/**
 * Response containing similarity maps.
 */
export type SimilarityMapResponse = {
    query: string;
    tokens: Array<TokenInfo>;
    similarity_maps: Array<SimilarityMapResult>;
};

