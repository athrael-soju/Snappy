/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConfigUpdate } from '../models/ConfigUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ConfigurationService {
    /**
     * Get Config Schema
     * Get the configuration schema with categories and settings.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getConfigSchemaConfigSchemaGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/config/schema',
        });
    }
    /**
     * Get Config Values
     * Get current values for all configuration variables.
     * @returns string Successful Response
     * @throws ApiError
     */
    public static getConfigValuesConfigValuesGet(): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/config/values',
        });
    }
    /**
     * Update Config
     * Update a configuration value at runtime.
     *
     * Note: This only updates the runtime environment variable.
     * To persist changes, you must update your .env file manually.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateConfigConfigUpdatePost(
        requestBody: ConfigUpdate,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/config/update',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reset Config
     * Reset all configuration to defaults from schema.
     *
     * Note: This only affects runtime values. Your .env file remains unchanged.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static resetConfigConfigResetPost(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/config/reset',
        });
    }
}
