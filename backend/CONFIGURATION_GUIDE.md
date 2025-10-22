# Configuration System Guide - Under the Hood! 🔧

Welcome to Snappy's configuration deep-dive! This guide shows you exactly how the backend loads, exposes, and updates settings at runtime. Perfect companion to `backend/docs/configuration.md`; this one's all about implementation details and pro tips! 💡

---

## Architecture Overview 🏗️

**The Configuration Flow**:
```
.env  →  os.environ  →  runtime_config  →  config.py (__getattr__)
             │                              │
             └─────── config_schema.py ─────┘
```

**The Players**:

1. **Environment** (`.env`) – Loaded once via `python-dotenv` and merged with process environment

2. **runtime_config.py** – Thread-safe storage for all key/value pairs with smart type helpers (strings, ints, floats, bools)

3. **config_schema.py** – The blueprint! Defines defaults, types, UI metadata, and "critical" keys that need service refresh

4. **config.py** – Magic `__getattr__` access! Reads schema, consults runtime_config, applies computed defaults (like auto-sized workers), raises `AttributeError` for unknown keys

5. **/config API** (`backend/api/routers/config.py`) – Exposes the schema and enables live edits. Critical changes trigger `invalidate_services()` to refresh Qdrant/MinIO/ColPali!

---

## Module Cheat Sheet 📋

| Module | What It Does | Key Functions |
|--------|--------------|---------------|
| `config_schema.py` | Defines the blueprint | `get_config_defaults`, `get_api_schema`, `get_all_config_keys`, `get_critical_keys` |
| `runtime_config.py` | Mutable store (backed by `os.environ`) | `get`, `set`, `get_int`, `get_float`, `get_bool`, `update`, `reload_from_env` |
| `config.py` | Dynamic magic accessor | `__getattr__`, `get_ingestion_worker_threads`, `get_pipeline_max_concurrency` |
| `api/routers/config.py` | REST API for live changes | `/config/schema`, `/config/values`, `/config/update`, `/config/reset` |
| `api/dependencies.py` | Service cache manager | `invalidate_services()` refreshes ColPali/MinIO/Qdrant |

---

## Configuration Types 🎨

**Supported Types**: `str`, `int`, `float`, `bool`, and `list`

For lists, we split comma-separated strings and trim whitespace automatically!

**Special Cases** ⭐:

- **`ALLOWED_ORIGINS`** – `["*"]` for wide-open CORS, or comma-separated URLs for production
- **`MINIO_PUBLIC_URL`** – Falls back to `MINIO_URL` when empty
- **`MINIO_WORKERS` / `MINIO_RETRIES`** – Auto-calculated from CPU + pipeline concurrency (unless you override)

💡 **Pro Tip**: Need a computed default? Add the logic to `config.py` so everyone accesses it via `config.MY_SETTING`!

---

## Updating Configuration at Runtime ⚡

**The Update Dance**:

1. **Call** `POST /config/update` with `{ "key": "...", "value": "..." }`
2. **Validate** – Router checks the key exists in `get_all_config_keys()`
3. **Store** – `runtime_config.set()` updates the value and `os.environ`
4. **Refresh** – If it's a critical key, `invalidate_services()` clears cached clients

⚠️ **Remember**: Runtime updates are temporary! They vanish on restart. For permanent changes, update `.env` or your deployment secrets.

---

## Adding a New Setting 🆕

**Three Easy Steps**:

1. **Define** in `config_schema.py` (category, default, type, UI metadata)
2. **Access** in code via `config.MY_SETTING`
3. **Expose** (optional) in the frontend by using the updated schema

🚨 **Critical Warning**: Never use `from config import MY_SETTING`! This caches the value at import time. Always do `import config` and access dynamically: `config.MY_SETTING`

---

## Best Practices - Pro Tips! 🌟

**Read Lazily** 🦥: Access config inside functions or via `@property` for long-lived objects. Keeps things dynamic when values change!

**Log Smart** 📝: When debugging, log the `config.*` value alongside actions. Confirms you're using the right defaults!

**Guard Against Bad Input** 🛡️: `runtime_config` handles invalid ints/floats, but always validate user input in calculations (buffer sizes, etc.)

**Mark Critical Keys** 🚨: Adding a setting that affects Qdrant collections or MinIO storage? Include it in `get_critical_keys()` for automatic cache invalidation!

---

## Debugging Checklist 🔍

**Not Working as Expected?** Try these:

✅ `GET /config/schema` – Verify the key exists and check its default

✅ `GET /config/values` – See what's currently set

✅ `runtime_config.reload_from_env()` – Reload env vars (useful for REPL/testing)

✅ **Check logs** for `invalidate_services()` messages – Confirms cache clearing

💡 **Still stuck?** Double-check that your key is in `config_schema.py` and spelled correctly!

---

## Summary - The Big Picture! 🎯

✨ **The Schema** – `config_schema.py` defines everything (settings, defaults, metadata)

🔧 **Dynamic Access** – Backend reads config via the `config` module in real-time

🎛️ **Live Tuning** – `/config/*` API + UI let you tweak without restarts

🔄 **Smart Refresh** – Critical changes auto-invalidate cached services

💾 **Persistence** – Remember: update `.env` or deployment secrets for permanent changes!

That's Snappy's configuration system in a nutshell! Questions? Check out `backend/docs/configuration.md` for the user-friendly reference. 🚀
