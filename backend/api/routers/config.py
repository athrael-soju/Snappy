"""Configuration management API endpoints."""

import logging
from copy import deepcopy
from typing import Any, Dict, List

from api.dependencies import invalidate_services
from config.runtime import get_runtime_config
from config.schema import get_all_config_keys, get_api_schema
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.timing import PerformanceTimer

logger = logging.getLogger(__name__)

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

# Use schema from single source of truth
CONFIG_SCHEMA = _API_SCHEMA


@router.get("/schema")
async def get_config_schema() -> Dict[str, Any]:
    """Get the configuration schema with categories and settings."""
    with PerformanceTimer("get config schema", log_on_exit=False) as timer:
        schema = deepcopy(CONFIG_SCHEMA)

    logger.debug(
        "Configuration schema retrieved",
        extra={
            "operation": "get_schema",
            "category_count": len(schema),
            "duration_ms": timer.duration_ms,
        },
    )

    return schema


@router.get("/values")
async def get_config_values() -> Dict[str, str]:
    """Get current values for all configuration variables."""
    with PerformanceTimer("get config values", log_on_exit=False) as timer:
        runtime_cfg = get_runtime_config()
        values = {}

        for category in CONFIG_SCHEMA.values():
            for setting in category["settings"]:
                key = setting["key"]
                default = setting.get("default", "")
                values[key] = runtime_cfg.get(key, default)

    logger.debug(
        "Configuration values retrieved",
        extra={
            "operation": "get_values",
            "key_count": len(values),
            "duration_ms": timer.duration_ms,
        },
    )

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
        logger.warning(
            "Attempt to update invalid configuration key",
            extra={
                "operation": "update_config",
                "key": update.key,
                "error": "invalid_key",
            },
        )
        raise HTTPException(
            status_code=400, detail=f"Invalid configuration key: {update.key}"
        )

    # Capture old value for audit trail
    old_value = runtime_cfg.get(update.key, "")

    try:
        with PerformanceTimer("update config", log_on_exit=False) as timer:
            # Update the runtime configuration
            runtime_cfg.set(update.key, update.value)

            # Always invalidate service singletons when config changes
            # This ensures all changes apply immediately without requiring restarts
            invalidate_services()

        logger.info(
            f"Config updated: {update.key}={update.value}",
            extra={
                "operation": "update_config",
                "key": update.key,
                "old_value": old_value,
                "new_value": update.value,
                "services_invalidated": True,
                "duration_ms": timer.duration_ms,
            },
        )

        return {
            "status": "ok",
            "message": f"Configuration updated: {update.key}",
            "key": update.key,
            "value": update.value,
            "services_invalidated": True,
            "warning": "This change is runtime-only and will not persist after restart. Update your .env file to make it permanent.",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to update configuration",
            exc_info=exc,
            extra={
                "operation": "update_config",
                "key": update.key,
                "old_value": old_value,
                "new_value": update.value,
            },
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
async def reset_config() -> Dict[str, Any]:
    """
    Reset all configuration to defaults from schema.

    Note: This only affects runtime values. Your .env file remains unchanged.
    """
    logger.warning(
        "Configuration reset to defaults requested", extra={"operation": "reset_config"}
    )

    try:
        with PerformanceTimer("reset config", log_on_exit=False) as timer:
            runtime_cfg = get_runtime_config()
            reset_count = 0
            reset_keys = []

            for category in CONFIG_SCHEMA.values():
                for setting in category["settings"]:
                    key = setting["key"]
                    default = setting.get("default", "")
                    runtime_cfg.set(key, default)
                    reset_keys.append(key)
                    reset_count += 1

            # Invalidate services to apply default config
            invalidate_services()

        logger.warning(
            "Configuration reset to defaults completed",
            extra={
                "operation": "reset_config",
                "reset_count": reset_count,
                "services_invalidated": True,
                "duration_ms": timer.duration_ms,
            },
        )

        return {
            "status": "ok",
            "message": f"Reset {reset_count} configuration values to defaults",
            "services_invalidated": True,
        }

    except Exception as exc:
        logger.error(
            "Failed to reset configuration",
            exc_info=exc,
            extra={"operation": "reset_config"},
        )
        raise HTTPException(status_code=500, detail=str(exc))
