import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const k = z.union([z.number(), z.null()]).optional();
const SearchItem = z
  .object({
    image_url: z.union([z.string(), z.null()]),
    label: z.union([z.string(), z.null()]),
    payload: z.object({}).partial().passthrough(),
    score: z.union([z.number(), z.null()]).optional(),
    json_url: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const ValidationError = z
  .object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string(),
  })
  .passthrough();
const HTTPValidationError = z
  .object({ detail: z.array(ValidationError) })
  .partial()
  .passthrough();
const Body_index_index_post = z
  .object({ files: z.array(z.instanceof(File)) })
  .passthrough();
const ConfigUpdate = z
  .object({ key: z.string(), value: z.string() })
  .passthrough();
const OcrPageRequest = z
  .object({
    filename: z.string(),
    page_number: z.number().int().gte(0),
    mode: z.union([z.string(), z.null()]).optional(),
    task: z.union([z.string(), z.null()]).optional(),
    custom_prompt: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const OcrResponse = z
  .object({
    status: z.string(),
    filename: z.string(),
    page_number: z.number().int(),
    storage_url: z.string(),
    text_preview: z.string(),
    regions: z.number().int(),
    extracted_images: z.number().int(),
  })
  .passthrough();
const OcrBatchRequest = z
  .object({
    filename: z.string(),
    page_numbers: z.array(z.number().int()),
    mode: z.union([z.string(), z.null()]).optional(),
    task: z.union([z.string(), z.null()]).optional(),
    max_workers: z.union([z.number(), z.null()]).optional(),
  })
  .passthrough();
const OcrBatchResponse = z
  .object({
    status: z.string(),
    total_pages: z.number().int(),
    successful: z.number().int(),
    failed: z.number().int(),
    results: z.array(z.object({}).partial().passthrough()),
  })
  .passthrough();
const OcrDocumentRequest = z
  .object({
    filename: z.string(),
    mode: z.union([z.string(), z.null()]).optional(),
    task: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();

export const schemas = {
  k,
  SearchItem,
  ValidationError,
  HTTPValidationError,
  Body_index_index_post,
  ConfigUpdate,
  OcrPageRequest,
  OcrResponse,
  OcrBatchRequest,
  OcrBatchResponse,
  OcrDocumentRequest,
};

const endpoints = makeApi([
  {
    method: "get",
    path: "/",
    alias: "root__get",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/clear/all",
    alias: "clear_all_clear_all_post",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/clear/minio",
    alias: "clear_minio_clear_minio_post",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/clear/qdrant",
    alias: "clear_qdrant_clear_qdrant_post",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/config/reset",
    alias: "reset_config_config_reset_post",
    description: `Reset all configuration to defaults from schema.

Note: This only affects runtime values. Your .env file remains unchanged.`,
    requestFormat: "json",
    response: z.object({}).partial().passthrough(),
  },
  {
    method: "get",
    path: "/config/schema",
    alias: "get_config_schema_config_schema_get",
    description: `Get the configuration schema with categories and settings.`,
    requestFormat: "json",
    response: z.object({}).partial().passthrough(),
  },
  {
    method: "post",
    path: "/config/update",
    alias: "update_config_config_update_post",
    description: `Update a configuration value at runtime.

Note: This updates the runtime configuration immediately.
To persist changes across restarts, update your .env file manually.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ConfigUpdate,
      },
    ],
    response: z.object({}).partial().passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/config/values",
    alias: "get_config_values_config_values_get",
    description: `Get current values for all configuration variables.`,
    requestFormat: "json",
    response: z.record(z.string()),
  },
  {
    method: "delete",
    path: "/delete",
    alias: "delete_collection_and_bucket_delete_delete",
    description: `Delete collection and bucket completely.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "get",
    path: "/health",
    alias: "health_health_get",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/index",
    alias: "index_index_post",
    requestFormat: "form-data",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: Body_index_index_post,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/index/cancel/:job_id",
    alias: "cancel_upload_index_cancel__job_id__post",
    description: `Cancel an ongoing upload/indexing job.`,
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/initialize",
    alias: "initialize_initialize_post",
    description: `Initialize/create collection and bucket based on current configuration.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/ocr/cancel/:job_id",
    alias: "cancel_job_ocr_cancel__job_id__post",
    description: `Cancel a running OCR job.`,
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/ocr/health",
    alias: "health_check_ocr_health_get",
    description: `Check OCR service health.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/ocr/process-batch",
    alias: "process_batch_ocr_process_batch_post",
    description: `Process multiple pages from the same document in parallel.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OcrBatchRequest,
      },
    ],
    response: OcrBatchResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/ocr/process-document",
    alias: "process_document_ocr_process_document_post",
    description: `Process all pages of an indexed document with OCR.

This is a long-running operation that runs in the background.
Use the returned job_id to track progress via SSE.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OcrDocumentRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/ocr/process-page",
    alias: "process_page_ocr_process_page_post",
    description: `Process a single document page with DeepSeek OCR.

The page must already be indexed and stored in MinIO.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OcrPageRequest,
      },
    ],
    response: OcrResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/ocr/progress/:job_id",
    alias: "get_progress_ocr_progress__job_id__get",
    description: `Get OCR processing progress for a job.`,
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/ocr/progress/stream/:job_id",
    alias: "stream_progress_ocr_progress_stream__job_id__get",
    description: `Stream OCR processing progress via Server-Sent Events.`,
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/progress/stream/:job_id",
    alias: "stream_progress_progress_stream__job_id__get",
    requestFormat: "json",
    parameters: [
      {
        name: "job_id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/search",
    alias: "search_search_get",
    requestFormat: "json",
    parameters: [
      {
        name: "q",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "k",
        type: "Query",
        schema: k,
      },
      {
        name: "include_ocr",
        type: "Query",
        schema: z.boolean().optional().default(false),
      },
    ],
    response: z.array(SearchItem),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/status",
    alias: "get_status_status_get",
    description: `Get the status of collection and bucket including statistics.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "get",
    path: "/version",
    alias: "version_version_get",
    description: `Get the current version of the backend API.`,
    requestFormat: "json",
    response: z.unknown(),
  },
]);

export const api = new Zodios(endpoints);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}
