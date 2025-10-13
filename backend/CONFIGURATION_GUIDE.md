# Configuration System Guide

This guide explains how the backend loads, exposes, and updates configuration
values at runtime. It complements the concise reference in
`backend/docs/configuration.md` with additional implementation details and best
practices.

---

## Architecture overview

```
.env  →  os.environ  →  runtime_config  →  config.py (__getattr__)
             │                              │
             └─────── config_schema.py ─────┘
```

1. **Environment** – `.env` is loaded once (via `python-dotenv`) and merged with
   the process environment.
2. **runtime_config.py** – stores a thread-safe copy of all key/value pairs.
   Provides helpers to get/set values as strings, ints, floats, or booleans.
3. **config_schema.py** – single source of truth for defaults, types, UI
   metadata, and “critical” keys that require service invalidation.
4. **config.py** – exposes dynamic, typed access through `__getattr__`. It
   reads the schema, consults `runtime_config`, applies computed defaults (for
   example deriving MinIO worker counts), and raises `AttributeError` for
   unknown keys.
5. **/config API** – `backend/api/routers/config.py` surfaces the schema and
   allows runtime edits. Critical keys trigger `invalidate_services()` so cached
   dependencies (Qdrant, MinIO, ColPali) are recreated on next use.

---

## Module cheat sheet

| Module | Responsibility | Helpful functions |
|--------|----------------|-------------------|
| `config_schema.py` | Defines categories, defaults, UI metadata | `get_config_defaults`, `get_api_schema`, `get_all_config_keys`, `get_critical_keys` |
| `runtime_config.py` | Mutable store backed by `os.environ` | `get`, `set`, `get_int`, `get_float`, `get_bool`, `update`, `reload_from_env` |
| `config.py` | Dynamic access used by the rest of the codebase | `__getattr__`, `get_ingestion_worker_threads`, `get_pipeline_max_concurrency` |
| `api/routers/config.py` | REST API for runtime changes | `/config/schema`, `/config/values`, `/config/update`, `/config/reset`, `/config/optimize` |
| `api/dependencies.py` | Service caching + invalidation | `invalidate_services()` clears cached ColPali/MinIO/Qdrant clients |

---

## Configuration types

The schema supports `str`, `int`, `float`, `bool`, and `list`. For list values
the helper in `config.py` splits comma-separated strings and trims whitespace.

Special handling:

- `ALLOWED_ORIGINS` – `["*"]` keeps CORS permissive; otherwise a comma-separated
  list is converted to `["https://example.com", ...]`.
- `MINIO_PUBLIC_URL` – falls back to `MINIO_URL` when left blank.
- `MINIO_WORKERS` / `MINIO_RETRIES` – auto-calculated from CPU count and pipeline
  concurrency unless explicitly set.

If you need a new computed default, add the logic to `config.py` so callers
continue to access it via `config.MY_SETTING`.

---

## Updating configuration at runtime

1. Call `POST /config/update` with `{ "key": "...", "value": "..." }`.
2. The router validates the key against `get_all_config_keys()`.
3. `runtime_config.set()` stores the value and updates `os.environ`.
4. If the key is in `get_critical_keys()`, `invalidate_services()` clears the
   cached MinIO/Qdrant/ColPali clients.

Runtime updates are **not** persisted to `.env`. For durable changes commit the
new value to your environment file or deployment secret.

---

## Adding a new setting

1. Define it in `config_schema.py` (category, default, type, optional UI
   metadata).
2. Access it in code through `config.MY_SETTING`.
3. (Optional) expose it in the frontend by consuming the updated schema.

Avoid importing literal values: `from config import MY_SETTING` caches the value
at import time. Always `import config` and access attributes dynamically.

---

## Best practices

- **Read lazily** – access configuration inside functions or via `@property`
  accessors when used in long-lived objects. This keeps behaviour dynamic if
  values change at runtime.
- **Log what matters** – when debugging, log the relevant `config.*` value
  alongside the action. It helps confirm the expected defaults are in play.
- **Handle conversion errors** – `runtime_config` already guards against invalid
  ints/floats by returning the default. Still, validate user input when it flows
  into calculations (for example when deriving buffer sizes).
- **Respect critical keys** – if you add a setting that changes the shape of the
  Qdrant collection or MinIO storage, include it in `get_critical_keys()` so the
  service cache is invalidated automatically.

---

## Debugging checklist

- `GET /config/schema` – verify the key exists and check its default.
- `GET /config/values` – inspect the current runtime values.
- `runtime_config.reload_from_env()` – reload environment variables if you
  changed them outside the process (primarily for REPL/testing).
- Check logs for messages emitted by `invalidate_services()`; they confirm
  whether caches were cleared.

---

## Summary

- `config_schema.py` defines every runtime setting and default.
- The backend reads configuration dynamically via the `config` module.
- The `/config/*` API and the maintenance UI allow live tuning without
  restarts.
- Critical changes invalidate cached dependencies so the next request observes
  the updated settings.
- Persist important changes to `.env` or deployment secrets to survive restarts.
