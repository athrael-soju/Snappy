"""Configuration management API endpoints."""
import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runtime_config import get_runtime_config
from api.dependencies import invalidate_services
from config_schema import get_api_schema, get_all_config_keys, get_critical_keys


router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigCategory(BaseModel):
    """Configuration category with its settings."""
    name: str
    description: str
    settings: List[Dict[str, Any]]


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


@router.get("/schema")
async def get_config_schema() -> Dict[str, Any]:
    """Get the configuration schema with categories and settings."""
    return CONFIG_SCHEMA


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
            status_code=400,
            detail=f"Invalid configuration key: {update.key}"
        )
    
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
        "warning": "This change is runtime-only and will not persist after restart. Update your .env file to make it permanent."
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
        "services_invalidated": True
    }
