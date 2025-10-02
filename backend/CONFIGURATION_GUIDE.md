# Configuration System Guide

## Overview

The backend uses a centralized, dynamic configuration system that allows runtime updates without restarting the server.

## Architecture

### Single Source of Truth: `config_schema.py`

All configuration defaults, types, and UI metadata are defined in **`config_schema.py`**. This ensures consistency across the entire system.

```python
from config_schema import CONFIG_SCHEMA

# Schema structure:
{
  "category_key": {
    "name": "Category Name",
    "description": "Category description",
    "settings": [
      {
        "key": "ENV_VAR_NAME",
        "type": "int",              # Config type: str, int, float, bool, list
        "default": 42,              # Actual typed default value
        "label": "Display Label",   # UI label
        "ui_type": "number",        # UI input type
        "min": 1,                   # Optional: validation
        "max": 100,
        "description": "Setting description"
      }
    ]
  }
}
```

### Configuration Modules

#### 1. **`config_schema.py`** ⭐ (Single Source of Truth)
- Defines all settings with types, defaults, and UI metadata
- Provides helper functions to extract data in different formats

**Key functions:**
```python
get_config_defaults()    # Returns: {"KEY": ("type", default_value)}
get_api_schema()        # Returns: API-formatted schema for frontend
get_all_config_keys()   # Returns: List of all config keys
get_critical_keys()     # Returns: Keys that require service restart
```

#### 2. **`runtime_config.py`**
- Thread-safe configuration manager
- Stores config values in memory and syncs with `os.environ`
- Provides get/set methods with type conversion

**Key methods:**
```python
runtime_config.get(key, default)           # Get as string
runtime_config.get_int(key, default)       # Get as int
runtime_config.get_float(key, default)     # Get as float
runtime_config.get_bool(key, default)      # Get as bool
runtime_config.set(key, value)             # Set value (updates os.environ)
```

#### 3. **`config.py`**
- Dynamic configuration access using `__getattr__`
- Reads from `config_schema.py` for defaults
- All code accesses config like: `config.BATCH_SIZE`

**Usage in code:**
```python
import config

batch_size = config.BATCH_SIZE              # Always gets current value
use_binary = config.QDRANT_USE_BINARY       # Dynamic - updates take effect
```

#### 4. **`api/routers/config.py`**
- REST API endpoints for configuration management
- Uses schema for validation and defaults
- Auto-invalidates services when critical settings change

**API endpoints:**
- `GET /config/schema` - Get configuration schema
- `GET /config/values` - Get current values
- `POST /config/update` - Update a setting
- `POST /config/reset` - Reset all to defaults

## How It Works

### 1. Loading Defaults
```
.env file → os.environ → runtime_config → config.py
                            ↑
                      config_schema.py
                      (defines defaults)
```

### 2. Reading Configuration
```python
# In your code
import config

# This triggers __getattr__ in config.py
value = config.BATCH_SIZE

# Which calls:
runtime_config.get_int("BATCH_SIZE", default_from_schema)
```

### 3. Updating Configuration
```
Frontend → POST /config/update → runtime_config.set()
                                      ↓
                          Updates os.environ + memory
                                      ↓
                          Invalidate services if critical
                                      ↓
                          Next access gets new value
```

## Configuration Types

### Basic Types

| Type   | Python Type | Example Default | Description |
|--------|-------------|-----------------|-------------|
| `str`  | `str`       | `"gpu"`         | Text values |
| `int`  | `int`       | `12`            | Integers    |
| `float`| `float`     | `2.0`           | Decimals    |
| `bool` | `bool`      | `True`          | True/False  |
| `list` | `List[str]` | `"*"` or `"a,b"`| Comma-separated |

### Special Cases

**ALLOWED_ORIGINS (list type):**
```python
# Value: "*" → Returns: ["*"]
# Value: "http://a.com,http://b.com" → Returns: ["http://a.com", "http://b.com"]
```

**COLPALI_API_BASE_URL (computed):**
```python
# If empty, automatically computed from:
# COLPALI_MODE == "gpu" ? COLPALI_GPU_URL : COLPALI_CPU_URL
```

**MINIO_PUBLIC_URL (computed):**
```python
# If empty, falls back to MINIO_URL
```

## Critical Configuration Keys

These settings trigger service re-initialization when changed:

- `MUVERA_ENABLED` - Requires new service with/without MUVERA
- `QDRANT_COLLECTION_NAME` - Collection must be recreated
- `QDRANT_MEAN_POOLING_ENABLED` - Vector configuration changes
- `QDRANT_URL` - Database connection changes
- `QDRANT_USE_BINARY` - Quantization settings
- `QDRANT_ON_DISK` - Storage configuration

## Adding New Configuration

### Step 1: Add to `config_schema.py`

```python
CONFIG_SCHEMA = {
    "my_category": {
        "name": "My Category",
        "description": "My settings",
        "settings": [
            {
                "key": "MY_NEW_SETTING",
                "type": "int",              # Type for config.py
                "default": 42,              # Actual default value
                "label": "My Setting",      # UI label
                "ui_type": "number",        # UI input type
                "min": 1,
                "max": 100,
                "description": "My setting description"
            }
        ]
    }
}
```

### Step 2: Use in Code

```python
import config

value = config.MY_NEW_SETTING  # Automatically available!
```

### Step 3: Update Frontend (Optional)

The frontend will automatically get the new setting via `/config/schema`, but you may need to update the TypeScript types if using them.

## Best Practices

### ✅ DO

```python
# Always import module, not values
import config
value = config.SETTING_NAME

# Access config dynamically
if config.MUVERA_ENABLED:
    process_with_muvera()
```

### ❌ DON'T

```python
# Never import specific values
from config import SETTING_NAME  # ❌ Will cache at import time!

# Never cache config values
self.batch_size = config.BATCH_SIZE  # ❌ Won't update when config changes!
```

### Service Initialization

If your service depends on config values:

```python
class MyService:
    def __init__(self):
        # DON'T cache config in __init__
        # self.url = config.MY_URL  # ❌
        pass
    
    @property
    def url(self):
        # DO use properties
        return config.MY_URL  # ✅ Always fresh
```

## Configuration Persistence

### Runtime (Default)
Changes via API are stored in memory and `os.environ`. They persist until the server restarts.

### Permanent
To make changes permanent, update your `.env` file:

```bash
# .env
BATCH_SIZE=24
MUVERA_ENABLED=True
QDRANT_USE_BINARY=True
```

## Debugging

### Check Current Values

```python
# In Python code
import config
print(f"BATCH_SIZE = {config.BATCH_SIZE}")

# Via API
GET /config/values
```

### Check If Config Updated

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Using BATCH_SIZE={config.BATCH_SIZE}")
```

### Verify Schema

```bash
# Via API
GET /config/schema

# Returns all settings with defaults
```

## Migration Guide

If you have old code using `from config import X`:

### Before (❌ Wrong)
```python
from config import BATCH_SIZE, MUVERA_ENABLED

def process():
    for i in range(0, total, BATCH_SIZE):  # Cached value!
        if MUVERA_ENABLED:  # Cached value!
            ...
```

### After (✅ Correct)
```python
import config

def process():
    for i in range(0, total, config.BATCH_SIZE):  # Dynamic!
        if config.MUVERA_ENABLED:  # Dynamic!
            ...
```

## Summary

- **One source of truth**: `config_schema.py` defines everything
- **Dynamic access**: Use `config.SETTING_NAME` (never `from config import`)
- **Runtime updates**: Changes via API take effect immediately
- **Type safe**: Schema defines types, runtime_config enforces them
- **Service invalidation**: Critical changes auto-restart affected services

**To change a default:** Edit `config_schema.py` → Restart server → All systems use new default ✅
