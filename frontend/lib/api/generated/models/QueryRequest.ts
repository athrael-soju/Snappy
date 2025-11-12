/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * SQL query request.
 */
export type QueryRequest = {
    /**
     * SQL query to execute
     */
    query: string;
    /**
     * Maximum rows to return
     */
    limit?: (number | null);
};

