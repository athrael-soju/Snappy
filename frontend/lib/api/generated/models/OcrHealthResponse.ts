/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OcrConstraints } from './OcrConstraints';
export type OcrHealthResponse = {
    /**
     * Service status reported by PaddleOCR-VL
     */
    status: string;
    /**
     * Service name
     */
    service: string;
    /**
     * Service version
     */
    version: string;
    /**
     * Whether GPU is available to the service
     */
    gpu_enabled: boolean;
    /**
     * Whether PaddleOCR-VL has initialised its pipeline
     */
    pipeline_ready: boolean;
    /**
     * Timestamp reported by the service
     */
    timestamp?: (string | null);
    /**
     * Upload constraints enforced by the backend proxy
     */
    constraints: OcrConstraints;
};

