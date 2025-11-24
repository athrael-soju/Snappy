# DuckDB Analytics Service

FastAPI wrapper around DuckDB for OCR analytics, deduplication, and inline OCR responses. Runs only in the full profile (`make up-full`).

## Quick start (Docker)
```bash
cd duckdb
docker compose up -d --build
```
Service: `http://localhost:8300` (UI at `http://localhost:42130` when bundled).

## What it stores
- Document metadata, OCR pages, and regions (text + bounding boxes).
- Dedup checks use filename, size, and page count before indexing.

## Key endpoints
- `GET /health`
- `POST /query` - run read-only SQL (SELECT only; LIMIT enforced)
- `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}`
- `GET /pages/{id}`, `GET /regions/{id}`

## Query safety
- Only SELECT allowed; DROP/DELETE/ALTER/INSERT/UPDATE blocked.
- Automatic LIMIT (max 10,000) if missing.

## Production tips
- Add auth, rate limits, backups, and query timeouts.
- Monitor DB size; consider retention if datasets grow large.

## Troubleshooting
- DB locked: ensure a single writer.
- UI missing: confirm `ui/` assets exist. 
