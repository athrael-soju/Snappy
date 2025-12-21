"""
Configuration schema - Single source of truth for all configuration settings.

This module defines:
1. Default values for all settings
2. Type information (str, int, float, bool, list)
3. UI metadata for the configuration panel (labels, descriptions, validation)

The schema is split into separate modules by service/category for better maintainability.
Both config.py and the API router import from here to ensure consistency.
"""

from typing import Any, Dict, List, Tuple

# Import all category schemas
from .application import SCHEMA as APPLICATION_SCHEMA

# Import base types and utilities
from .base import ConfigDefault, ConfigType, ConfigUIType, _infer_ui_type
from .colpali import SCHEMA as COLPALI_SCHEMA
from .deepseek_ocr import SCHEMA as DEEPSEEK_OCR_SCHEMA
from .duckdb import SCHEMA as DUCKDB_SCHEMA
from .local_storage import SCHEMA as LOCAL_STORAGE_SCHEMA
from .processing import SCHEMA as PROCESSING_SCHEMA
from .qdrant import SCHEMA as QDRANT_SCHEMA
from .retrieval import SCHEMA as RETRIEVAL_SCHEMA
from .upload import SCHEMA as UPLOAD_SCHEMA

# Combine all schemas into the main CONFIG_SCHEMA
CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    **APPLICATION_SCHEMA,
    **PROCESSING_SCHEMA,
    **UPLOAD_SCHEMA,
    **RETRIEVAL_SCHEMA,
    **COLPALI_SCHEMA,
    **DEEPSEEK_OCR_SCHEMA,
    **QDRANT_SCHEMA,
    **LOCAL_STORAGE_SCHEMA,
    **DUCKDB_SCHEMA,
}


def get_config_defaults() -> Dict[str, Tuple[ConfigType, Any]]:
    """
    Extract type information and defaults for config.py.

    Returns:
        Dict mapping config key to (type, default_value)
        Example: {"LOG_LEVEL": ("str", "INFO"), "BATCH_SIZE": ("int", 4)}
    """
    defaults = {}
    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            key = setting["key"]
            config_type = setting["type"]
            default_value = setting["default"]
            defaults[key] = (config_type, default_value)
    return defaults


def get_api_schema() -> Dict[str, Any]:
    """
    Convert schema to API format for frontend consumption.
    All numeric defaults converted to strings for UI compatibility.

    Returns:
        Schema dict with string defaults suitable for API responses
    """
    api_schema = {}
    for cat_key, category in CONFIG_SCHEMA.items():
        api_schema[cat_key] = {
            "name": category["name"],
            "description": category["description"],
            "order": category.get("order", 99),
            "icon": category.get("icon", "settings"),
            "ui_hidden": category.get("ui_hidden", False),
            "settings": [],
        }

        for setting in category["settings"]:
            api_setting = {
                "key": setting["key"],
                "label": setting["label"],
                "type": setting.get(
                    "ui_type", _infer_ui_type(setting["type"], "options" in setting)
                ),
                "default": str(setting["default"]),  # Convert to string for UI
                "description": setting["description"],
            }

            # Add optional fields
            if "options" in setting:
                api_setting["options"] = setting["options"]
            if "min" in setting:
                api_setting["min"] = setting["min"]
            if "max" in setting:
                api_setting["max"] = setting["max"]
            if "step" in setting:
                api_setting["step"] = setting["step"]
            if "depends_on" in setting:
                api_setting["depends_on"] = setting["depends_on"]
            if "help_text" in setting:
                api_setting["help_text"] = setting["help_text"]
            if "ui_hidden" in setting:
                api_setting["ui_hidden"] = setting["ui_hidden"]
            if "ui_indent_level" in setting:
                api_setting["ui_indent_level"] = setting["ui_indent_level"]
            if "ui_confirm" in setting:
                api_setting["ui_confirm"] = setting["ui_confirm"]
            if "ui_confirm_message" in setting:
                api_setting["ui_confirm_message"] = setting["ui_confirm_message"]

            api_schema[cat_key]["settings"].append(api_setting)

    return api_schema


def get_all_config_keys() -> List[str]:
    """Get list of all configuration keys."""
    keys = []
    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            keys.append(setting["key"])
    return keys


# Export all public APIs
__all__ = [
    "CONFIG_SCHEMA",
    "ConfigType",
    "ConfigDefault",
    "ConfigUIType",
    "get_config_defaults",
    "get_api_schema",
    "get_all_config_keys",
]
