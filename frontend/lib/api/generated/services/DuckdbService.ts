/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentInfo } from '../models/DocumentInfo';
import type { QueryRequest } from '../models/QueryRequest';
import type { QueryResponse } from '../models/QueryResponse';
import type { StatsResponse } from '../models/StatsResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DuckdbService {
    /**
     * Health Check
     * Check DuckDB service health.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthCheckDuckdbHealthGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/duckdb/health',
        });
    }
    /**
     * Get Stats
     * Get aggregate statistics from DuckDB.
     * @returns StatsResponse Successful Response
     * @throws ApiError
     */
    public static getStatsDuckdbStatsGet(): CancelablePromise<StatsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/duckdb/stats',
        });
    }
    /**
     * List Documents Endpoint
     * List all indexed documents in DuckDB.
     * @param limit Maximum results
     * @param offset Results offset
     * @returns DocumentInfo Successful Response
     * @throws ApiError
     */
    public static listDocumentsEndpointDuckdbDocumentsGet(
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<DocumentInfo>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/duckdb/documents',
            query: {
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Document
     * Get information about a specific document.
     * @param filename
     * @returns DocumentInfo Successful Response
     * @throws ApiError
     */
    public static getDocumentDuckdbDocumentsFilenameGet(
        filename: string,
    ): CancelablePromise<DocumentInfo> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/duckdb/documents/{filename}',
            path: {
                'filename': filename,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Document
     * Delete all data for a document from DuckDB.
     * @param filename
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteDocumentDuckdbDocumentsFilenameDelete(
        filename: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/duckdb/documents/{filename}',
            path: {
                'filename': filename,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Page
     * Get OCR data for a specific page from DuckDB.
     * @param filename
     * @param pageNumber
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPageDuckdbPagesFilenamePageNumberGet(
        filename: string,
        pageNumber: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/duckdb/pages/{filename}/{page_number}',
            path: {
                'filename': filename,
                'page_number': pageNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute Query
     * Execute a SQL query against DuckDB.
     *
     * Note: Only SELECT queries are allowed. Dangerous operations are blocked.
     * @param requestBody
     * @returns QueryResponse Successful Response
     * @throws ApiError
     */
    public static executeQueryDuckdbQueryPost(
        requestBody: QueryRequest,
    ): CancelablePromise<QueryResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/duckdb/query',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Search Text
     * Full-text search across all OCR data.
     * @param q Search query
     * @param limit Maximum results
     * @returns any Successful Response
     * @throws ApiError
     */
    public static searchTextDuckdbSearchPost(
        q: string,
        limit: number = 50,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/duckdb/search',
            query: {
                'q': q,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
