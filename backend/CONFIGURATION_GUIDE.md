# Configuration System Guide 🔧

This guide explains how Snappy's backend loads, exposes, and updates configuration at runtime. Use it alongside `backend/docs/configuration.md`: that file lists every setting, while this one focuses on implementation details and best practices.

---

## Architecture Overview

```
.env  →  os.environ  →  runtime_config  →  config.py (__getattr__)
             │                              │
             └─────── config_schema.py ─────┘
```

**Key modules**

1. **Environment (`.env`)** – Loaded once with `python-dotenv` and merged with the process environment.
2. **`runtime_config.py`** – Thread-safe store that keeps every key/value pair with helpers for strings, ints, floats, bools.
3. **`config_schema.py`** – Single source of truth: defaults, types, UI metadata, and critical-key definitions.
4. **`config.py`** – Lazy access via `config.MY_SETTING`; applies computed defaults and raises `AttributeError` for unknown keys.
5. **`/config` routers** – `backend/api/routers/config.py` serves schema/data and applies runtime updates. Critical updates call `invalidate_services()` so cached clients refresh automatically.

---

## Module Quick Reference

| Module | Purpose | Highlights |
|--------|---------|------------|
| `config_schema.py` | Defines defaults, types, UI metadata | `get_config_defaults`, `get_api_schema`, `get_all_config_keys`, `get_critical_keys` |
| `runtime_config.py` | Mutable backing store | `get`, `set`, `get_int`, `get_float`, `get_bool`, `update`, `reload_from_env` |
| `config.py` | Public accessor | Dynamic `__getattr__`, computed helpers like `get_pipeline_max_concurrency()` |
| `api/routers/config.py` | REST surface | `/config/schema`, `/config/values`, `/config/update`, `/config/reset` |
| `api/dependencies.py` | Service cache invalidation | `invalidate_services()` handles ColPali, MinIO, Qdrant clients |

---

## Supported Types

- `str`, `int`, `float`, `bool`, `list`
- Lists are comma-separated; whitespace is trimmed automatically.
- Computed defaults live in `config.py` (e.g., auto-sized MinIO workers).

---

## Runtime Updates

1. Client calls `POST /config/update` with `{ "key": "...", "value": "..." }`.
2. Router validates the key via `get_all_config_keys()`.
3. `runtime_config.set()` stores the value and mirrors it in `os.environ`.
4. Critical keys trigger `invalidate_services()` so the next request reconnects.

Updates affect the running process only—restart the app or edit `.env` to persist changes.

---

## Adding a Setting

1. Define it in `config_schema.py` (category, default, metadata).
2. Reference it via `config.MY_SETTING`.
3. Optionally surface it in the UI; the schema already contains the metadata the frontend needs.

Avoid `from config import MY_SETTING`; import the module and access `config.MY_SETTING` so values remain dynamic.

---

## Recommended Practices

- **Access lazily**: Read configuration inside functions or properties instead of module-level constants.
- **Log clearly**: When debugging, include the relevant `config.*` value in log messages.
- **Validate inputs**: `runtime_config` guards type coercion, but downstream calculations should handle edge cases (e.g., buffer sizes).
- **Label critical keys**: Anything that changes Qdrant collections or MinIO endpoints should be marked in `get_critical_keys()` so clients refresh automatically.

---

## Debugging Checklist

- `GET /config/schema` – confirm the key exists and review metadata.
- `GET /config/values` – inspect the live value.
- `runtime_config.reload_from_env()` – reload the environment during tests or REPL sessions.
- Watch logs for `invalidate_services()` messages to confirm cache refreshes.

If a value still refuses to change, double-check the spelling in `config_schema.py`.

---

## Summary

- `config_schema.py` holds defaults, metadata, and critical-key definitions.
- `runtime_config` and `config.py` provide dynamic, typed access.
- `/config/*` endpoints enable live updates, with automatic cache invalidation.
- Persistent changes belong in `.env` or your deployment secrets.

For the full list of settings and recommended values, see `backend/docs/configuration.md`.

