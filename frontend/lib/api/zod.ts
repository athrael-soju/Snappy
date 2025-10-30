import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const k = z.union([z.number(), z.null()]).optional();
const SearchItem = z
  .object({
    image_url: z.union([z.string(), z.null()]),
    label: z.union([z.string(), z.null()]),
    payload: z.object({}).partial().passthrough(),
    score: z.union([z.number(), z.null()]).optional(),
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
const OCRDefaults = z
  .object({
    mode: z.string(),
    prompt: z.string(),
    grounding: z.boolean(),
    include_caption: z.boolean(),
    base_size: z.number().int(),
    image_size: z.number().int(),
    crop_mode: z.boolean(),
    test_compress: z.boolean(),
  })
  .passthrough();
const OCRHealth = z
  .object({
    enabled: z.boolean(),
    healthy: z.boolean(),
    model_loaded: z.union([z.boolean(), z.null()]).optional(),
    device: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const Body_run_ocr_ocr_infer_post = z
  .object({
    image: z.instanceof(File),
    mode: z.union([z.string(), z.null()]).optional(),
    prompt: z.union([z.string(), z.null()]).optional(),
    grounding: z.union([z.boolean(), z.null()]).optional(),
    include_caption: z.union([z.boolean(), z.null()]).optional(),
    find_term: z.union([z.string(), z.null()]).optional(),
    kv_schema: z.union([z.string(), z.null()]).optional(),
    base_size: z.union([z.number(), z.null()]).optional(),
    image_size: z.union([z.number(), z.null()]).optional(),
    crop_mode: z.union([z.boolean(), z.null()]).optional(),
    test_compress: z.union([z.boolean(), z.null()]).optional(),
  })
  .passthrough();
const OCRBoundingBox = z
  .object({ label: z.string(), box: z.array(z.number().int()).min(4).max(4) })
  .passthrough();
const OCRMetadata = z
  .object({
    mode: z.string(),
    grounding: z.boolean(),
    base_size: z.number().int(),
    image_size: z.number().int(),
    crop_mode: z.boolean(),
    include_caption: z.boolean(),
    elapsed_ms: z.union([z.number(), z.null()]).optional(),
  })
  .passthrough();
const OCRResponse = z
  .object({
    success: z.boolean().optional().default(true),
    text: z.string(),
    raw_text: z.string(),
    boxes: z.array(OCRBoundingBox),
    image_dims: z.record(z.union([z.number(), z.null()])),
    metadata: OCRMetadata,
  })
  .passthrough();

export const schemas = {
  k,
  SearchItem,
  ValidationError,
  HTTPValidationError,
  Body_index_index_post,
  ConfigUpdate,
  OCRDefaults,
  OCRHealth,
  Body_run_ocr_ocr_infer_post,
  OCRBoundingBox,
  OCRMetadata,
  OCRResponse,
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
    method: "get",
    path: "/ocr/defaults",
    alias: "get_defaults_ocr_defaults_get",
    description: `Return the configured default values used when optional OCR fields are omitted.`,
    requestFormat: "json",
    response: OCRDefaults,
  },
  {
    method: "get",
    path: "/ocr/health",
    alias: "health_ocr_health_get",
    description: `Surface the health status of the DeepSeek OCR service.`,
    requestFormat: "json",
    response: OCRHealth,
  },
  {
    method: "post",
    path: "/ocr/infer",
    alias: "run_ocr_ocr_infer_post",
    description: `Proxy OCR requests to the DeepSeek OCR service with Snappy defaults.`,
    requestFormat: "form-data",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: Body_run_ocr_ocr_infer_post,
      },
    ],
    response: OCRResponse,
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
    path: "/ocr/info",
    alias: "info_ocr_info_get",
    description: `Expose metadata returned by the DeepSeek OCR service.`,
    requestFormat: "json",
    response: z.object({}).partial().passthrough(),
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
