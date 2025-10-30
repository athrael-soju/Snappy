/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type OcrConstraints = {
    /**
     * Whether every extension is accepted before proxying
     */
    allow_any_extension: boolean;
    /**
     * Normalised list of allowed extensions (lowercase, with dot)
     */
    allowed_extensions?: Array<string>;
    /**
     * Maximum upload size enforced before proxying
     */
    max_file_size_bytes: number;
    /**
     * Maximum upload size in MB
     */
    max_file_size_mb: number;
};

