"""
Configuration module for FastAPI backend.

All settings are dynamically loaded from runtime configuration.
Values can be updated at runtime via the configuration API.
Defaults and types are defined in config_schema.py (single source of truth).
"""

import os
from typing import Any
from dotenv import load_dotenv
from runtime_config import get_runtime_config
from config_schema import get_config_defaults

load_dotenv()

# Initialize runtime config with environment variables
_runtime = get_runtime_config()

# Get configuration defaults from schema (single source of truth)
_CONFIG_DEFAULTS = get_config_defaults()


def __getattr__(name: str) -> Any:
    """
    Dynamically retrieve configuration values.
    This allows config values to be accessed like module constants but read from runtime config.
    """
    if name in _CONFIG_DEFAULTS:
        type_str, default = _CONFIG_DEFAULTS[name]
        
        if type_str == "int":
            return _runtime.get_int(name, default)
        elif type_str == "float":
            return _runtime.get_float(name, default)
        elif type_str == "bool":
            return _runtime.get_bool(name, default)
        elif type_str == "list":
            raw = _runtime.get(name, str(default))
            if raw.strip() == "*":
                return ["*"]
            return [o.strip() for o in raw.split(",") if o.strip()]
        else:  # str
            value = _runtime.get(name, str(default))
            # Handle special cases
            if name == "COLPALI_MODE":
                return value.lower()
            elif name == "COLPALI_API_BASE_URL" and not value:
                mode = __getattr__("COLPALI_MODE")
                return __getattr__("COLPALI_GPU_URL") if mode == "gpu" else __getattr__("COLPALI_CPU_URL")
            elif name == "MINIO_PUBLIC_URL" and not value:
                return __getattr__("MINIO_URL")
            return value
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
