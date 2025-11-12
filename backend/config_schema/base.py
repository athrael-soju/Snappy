"""
Base utilities for configuration schema.

Shared types and helper functions used across all schema modules.
"""

from typing import Any, Dict, Literal

# Type definitions
ConfigType = Literal["str", "int", "float", "bool", "list"]
ConfigDefault = Any  # The actual default value (typed)
ConfigUIType = Literal["text", "number", "boolean", "select", "password", "multiselect"]


def _infer_ui_type(config_type: ConfigType, has_options: bool = False) -> ConfigUIType:
    """Infer UI input type from config type."""
    if has_options:
        return "select"
    mapping: Dict[ConfigType, ConfigUIType] = {
        "str": "text",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "list": "text",
    }
    return mapping[config_type]
