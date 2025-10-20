# Morty™ Configuration Guide – Master Your Settings

This reference lists every runtime setting exposed by the Morty backend. Morty is a pro-bono rebrand of Snappy, so configuration names and defaults remain unchanged; only the documentation and branding differ.

## How to Read This Guide

- **Key:** Environment variable or JSON path used by Morty.  
- **Type:** Data type validated by the schema.  
- **Default:** Value applied when you omit the field.  
- **Notes:** Guidance on when to modify the setting.

## ColPali Embedding Service

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `COLPALI_MODE` | string (`cpu` or `gpu`) | `cpu` | Selects which downstream service Morty contacts. |
| `COLPALI_CPU_URL` | string | `http://localhost:7001` | Change if the CPU embedding service lives elsewhere. |
| `COLPALI_GPU_URL` | string | `http://localhost:7002` | Point to the GPU service when available. |
| `COLPALI_API_TIMEOUT` | integer (seconds) | `180` | Increase for large PDFs or remote deployments. |

## Qdrant Vector Store

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `QDRANT_URL` | string | `http://localhost:6333` | Set to managed Qdrant when running remotely. |
| `QDRANT_COLLECTION_NAME` | string | `morty_pages` | Collection name for multivector embeddings. |
| `QDRANT_PREFETCH_LIMIT` | integer | `64` | Prefetch size for streaming tasks. |
| `QDRANT_USE_BINARY` | boolean | `false` | Enable to reduce storage footprint with slight recall trade-offs. |
| `QDRANT_VECTOR_SIZE` | integer | `2048` | Matches ColPali embedding output. |

## MinIO Object Storage

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `MINIO_URL` | string | `http://localhost:9000` | Update when using managed object storage. |
| `MINIO_PUBLIC_URL` | string | `http://localhost:9000` | Controls public thumbnail URLs. |
| `MINIO_BUCKET_NAME` | string | `morty-documents` | Stores rendered page images. |
| `MINIO_ACCESS_KEY` | string | _required_ | Supply credentials before boot. |
| `MINIO_SECRET_KEY` | string | _required_ | Supply credentials before boot. |
| `IMAGE_FORMAT` | string | `webp` | Use `jpeg` if clients lack WebP support. |
| `IMAGE_QUALITY` | integer (0-100) | `85` | Reduce for smaller thumbnails. |

## MUVERA Acceleration

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `MUVERA_ENABLED` | boolean | `false` | Enables two-stage vector search. |
| `MUVERA_CONFIG` | json | `{}` | Optional overrides for MUVERA strategy. |

## API and Runtime

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `LOG_LEVEL` | string | `info` | Accepts standard Uvicorn log levels. |
| `ALLOWED_ORIGINS` | list | `["*"]` | Restrict before production. |
| `UVICORN_RELOAD` | boolean | `false` | Enable for local development. |
| `REQUEST_TIMEOUT` | integer (seconds) | `120` | Applies to ingestion endpoints. |

## Configuration Endpoints

- `GET /config/schema` – Returns the schema with categories, defaults, and metadata used by the Morty frontend UI.  
- `GET /config/values` – Provides current settings including overrides.  
- `POST /config/update` – Apply runtime changes. Morty validates input against the schema.  
- `POST /config/reset` – Remove overrides and return to defaults.  
- `POST /config/optimize` – Generate environment-aware recommendations; no changes occur until you confirm them.

## Best Practices

- Commit `.env` to a secure secret manager rather than version control.  
- Treat `/config/update` as temporary; redeploys revert to `.env` values.  
- Pair MUVERA with GPU-backed ColPali to maximize speedups.  
- Rotate MinIO credentials periodically and ensure HTTPS when running outside localhost.

## Troubleshooting

- **Timeouts:** Increase `COLPALI_API_TIMEOUT` or add GPU capacity.  
- **Missing thumbnails:** Confirm MinIO credentials and the `MINIO_PUBLIC_URL`.  
- **CORS issues:** Provide an explicit comma-separated list in `ALLOWED_ORIGINS`.  
- **Schema errors:** The response body identifies the invalid field and acceptable values.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
