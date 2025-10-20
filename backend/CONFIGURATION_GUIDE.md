# Morty™ Configuration System Guide – Under the Hood

This guide explains how Morty loads, validates, and persists configuration. Morty is a pro-bono rebrand based on Snappy, so everything here mirrors the upstream design with refreshed naming.

Use this document as the implementation companion to the user-facing reference in `backend/docs/configuration.md`.

## Runtime Sources

Morty merges settings from three layers (highest precedence last):

1. Default values defined in `backend/config_schema.py`  
2. Environment variables read at startup (dotenv support remains intact)  
3. Ephemeral overrides issued through `/config/update`

`backend/config.py:get_settings()` handles this merge and memoizes the result. A reset triggers a cache invalidation so subsequent reads pick up defaults again.

## Schema Anatomy

Each configuration section is modeled with Pydantic. Key fields:

- `title`, `description`, and `category` for UI grouping  
- `type` metadata for generating the Morty frontend controls  
- `advanced` and `requires_restart` flags for contextual messaging  
- Optional `choices` and `units` for select-like inputs

See `backend/config_schema.py` for the authoritative model definitions.

## Persisted Overrides

Morty stores runtime overrides in `morty_state.json`. The file mirrors the schema shape and contains only keys that differ from defaults. `/config/reset` deletes the file; `/config/update` writes a fresh version.

The backend locks writes to guarantee atomic updates and avoid race conditions when multiple requests attempt to save simultaneously.

## Optimize Endpoint

`POST /config/optimize` inspects the environment and suggests tuned values:

- Applies MUVERA configuration when GPU resources are present  
- Adjusts Qdrant binary quantization flags for low-memory deployments  
- Recommends MinIO concurrency based on CPU count

Optimization runs are idempotent; Morty reports recommended changes without forcing them so operators retain control.

## Validation Pipeline

1. Requests land in `backend/api/routers/config.py`.  
2. Input is validated against `ConfigUpdateRequest`.  
3. Settings merge with existing overrides; conflicts are resolved in favor of the newest values.  
4. Pydantic re-validation occurs on the merged object before persistence.  
5. Cache invalidation ensures subsequent dependency injections use the latest configuration.

Errors surface with actionable messages describing which field failed and why.

## Frontend Experience

The Morty frontend renders configuration forms directly from the schema:

- Draft state banner highlights un-applied browser changes.  
- Field-level helpers describe default values and acceptable ranges.  
- Reset controls revert to defaults section-by-section or globally.  
- The optimize action triggers the endpoint described above and previews changes before applying.

## Migration Considerations

- File names and env var prefixes still use `SNAPPY_` in code where applicable; the rebrand touches documentation only.  
- Review `MIGRATION.md` for end-user guidance and compatibility FAQs.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
