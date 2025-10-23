"""Configuration management API endpoints."""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

from api.dependencies import get_colpali_client, invalidate_services
from config_schema import get_all_config_keys, get_api_schema, get_critical_keys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runtime_config import get_runtime_config

router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigCategory(BaseModel):
    """Configuration category with its settings."""

    name: str
    description: str
    settings: List[Dict[str, Any]]
    ui_hidden: bool = False


class ConfigUpdate(BaseModel):
    """Request model for updating configuration."""

    key: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="New value")


# Get configuration schema from single source of truth
_API_SCHEMA = get_api_schema()
_ALL_KEYS = get_all_config_keys()
_CRITICAL_KEYS = get_critical_keys()

# Use schema from single source of truth
CONFIG_SCHEMA = _API_SCHEMA


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _check_mean_pooling_support() -> Tuple[bool, str | None]:
    """Probe the ColPali service to determine if patch metadata is available."""
    client = get_colpali_client()
    try:
        probe = client.get_patches([{"width": 256, "height": 256}])
    except Exception as exc:
        return False, f"Failed to query ColPali /patches endpoint ({exc})."

    if not probe:
        return False, "ColPali /patches endpoint returned no results."

    first = probe[0]
    if isinstance(first, dict):
        if first.get("error"):
            return (
                False,
                f"ColPali reported patch estimation unavailable ({first['error']}).",
            )
        if "n_patches_x" not in first or "n_patches_y" not in first:
            return (
                False,
                "ColPali did not return 'n_patches_x'/'n_patches_y'.",
            )
        return True, None

    return False, "Unexpected response format from ColPali /patches endpoint."


def _ensure_mean_pooling_supported() -> None:
    """
    Validate that the current ColPali deployment exposes patch metadata.

    Raises:
        HTTPException: if the embedding service does not support patch estimation.
    """
    supported, reason = _check_mean_pooling_support()
    if not supported:
        detail = (
            "Cannot enable mean pooling: "
            "the active model does not expose patch metadata."
        )
        if reason:
            detail = f"{detail} {reason}"
        raise HTTPException(status_code=400, detail=detail)


@router.get("/schema")
async def get_config_schema() -> Dict[str, Any]:
    """Get the configuration schema with categories and settings."""
    schema = deepcopy(CONFIG_SCHEMA)
    supported, reason = _check_mean_pooling_support()
    if not supported:
        explanation = (
            "Mean pooling requires patch metadata from the embedding model. "
            "The current ColPali deployment does not expose patch counts."
        )
        if reason:
            explanation = f"{explanation} {reason}"

        for category in schema.values():
            for setting in category["settings"]:
                if setting.get("key") == "QDRANT_MEAN_POOLING_ENABLED":
                    setting["ui_disabled"] = True
                    existing_help = setting.get("help_text") or ""
                    disabled_help = f"Why disabled: {explanation}"
                    setting["help_text"] = (
                        f"{existing_help}\n\n{disabled_help}".strip()
                        if existing_help
                        else disabled_help
                    )
                    break
    return schema


@router.get("/values")
async def get_config_values() -> Dict[str, str]:
    """Get current values for all configuration variables."""
    runtime_cfg = get_runtime_config()
    values = {}

    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            key = setting["key"]
            default = setting.get("default", "")
            values[key] = runtime_cfg.get(key, default)

    return values


@router.post("/update")
async def update_config(update: ConfigUpdate) -> Dict[str, Any]:
    """
    Update a configuration value at runtime.

    Note: This updates the runtime configuration immediately.
    To persist changes across restarts, update your .env file manually.
    """
    runtime_cfg = get_runtime_config()

    # Validate that the key exists in schema
    if update.key not in _ALL_KEYS:
        raise HTTPException(
            status_code=400, detail=f"Invalid configuration key: {update.key}"
        )

    if update.key == "QDRANT_MEAN_POOLING_ENABLED" and _is_truthy(update.value):
        _ensure_mean_pooling_supported()

    # Update the runtime configuration
    runtime_cfg.set(update.key, update.value)

    # Invalidate service singletons if critical config changed
    # This forces services to re-initialize with new config on next use
    if update.key in _CRITICAL_KEYS:
        invalidate_services()

    return {
        "status": "ok",
        "message": f"Configuration updated: {update.key}",
        "key": update.key,
        "value": update.value,
        "services_invalidated": update.key in _CRITICAL_KEYS,
        "warning": "This change is runtime-only and will not persist after restart. Update your .env file to make it permanent.",
    }


@router.post("/reset")
async def reset_config() -> Dict[str, Any]:
    """
    Reset all configuration to defaults from schema.

    Note: This only affects runtime values. Your .env file remains unchanged.
    """
    runtime_cfg = get_runtime_config()
    reset_count = 0

    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            key = setting["key"]
            default = setting.get("default", "")
            runtime_cfg.set(key, default)
            reset_count += 1

    # Invalidate services to apply default config
    invalidate_services()

    return {
        "status": "ok",
        "message": f"Reset {reset_count} configuration values to defaults",
        "services_invalidated": True,
    }


@router.post("/persist")
async def persist_config() -> Dict[str, Any]:
    """
    Persist current runtime configuration to .env file.

    This writes all current configuration values to the .env file,
    making them permanent across server restarts.

    Note: This will overwrite your existing .env file with current runtime values.
    """
    runtime_cfg = get_runtime_config()

    # Determine the .env file path (project root)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"

    try:
        # Collect all config values
        config_lines = []
        config_lines.append("# Configuration persisted from runtime settings")
        config_lines.append(f"# Generated automatically - edit with care\n")

        for category in CONFIG_SCHEMA.values():
            config_lines.append(f"\n# {category['name']}")
            if category.get("description"):
                config_lines.append(f"# {category['description']}")

            for setting in category["settings"]:
                key = setting["key"]
                current_value = runtime_cfg.get(key, setting.get("default", ""))

                # Add helpful comment with description
                if setting.get("description"):
                    config_lines.append(f"# {setting['description']}")

                config_lines.append(f"{key}={current_value}")

        # Write to .env file
        env_content = "\n".join(config_lines)
        env_path.write_text(env_content, encoding="utf-8")

        return {
            "status": "ok",
            "message": "Configuration persisted to .env file",
            "path": str(env_path),
            "settings_count": len(_ALL_KEYS),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist configuration to .env file: {str(e)}",
        )
