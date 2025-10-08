/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { HardwareSnapshot } from './HardwareSnapshot';
export type ConfigOptimizationResponse = {
    status: string;
    message: string;
    profile: string;
    applied: Record<string, string>;
    unchanged: Array<string>;
    detection: HardwareSnapshot;
    services_invalidated: boolean;
};

