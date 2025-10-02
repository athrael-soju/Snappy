"""Configuration management API endpoints."""
import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runtime_config import get_runtime_config
from api.dependencies import invalidate_services


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


# Define configuration schema with groupings
CONFIG_SCHEMA = {
    "application": {
        "name": "Application",
        "description": "Core application settings",
        "settings": [
            {
                "key": "LOG_LEVEL",
                "label": "Log Level",
                "type": "select",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "default": "INFO",
                "description": "Logging verbosity level"
            },
            {
                "key": "ALLOWED_ORIGINS",
                "label": "Allowed CORS Origins",
                "type": "text",
                "default": "*",
                "description": "Comma-separated list of allowed origins, or * for all"
            }
        ]
    },
    "processing": {
        "name": "Processing",
        "description": "Document processing and indexing settings",
        "settings": [
            {
                "key": "DEFAULT_TOP_K",
                "label": "Default Top K Results",
                "type": "number",
                "min": 1,
                "max": 100,
                "default": "5",
                "description": "Default number of search results to return"
            },
            {
                "key": "MAX_TOKENS",
                "label": "Max Tokens",
                "type": "number",
                "min": 100,
                "max": 4096,
                "default": "500",
                "description": "Maximum tokens for text generation"
            },
            {
                "key": "BATCH_SIZE",
                "label": "Batch Size",
                "type": "number",
                "min": 1,
                "max": 128,
                "default": "12",
                "description": "Number of documents to process in parallel"
            },
            {
                "key": "WORKER_THREADS",
                "label": "Worker Threads",
                "type": "number",
                "min": 1,
                "max": 32,
                "default": "8",
                "description": "Number of worker threads for processing"
            },
            {
                "key": "ENABLE_PIPELINE_INDEXING",
                "label": "Enable Pipeline Indexing",
                "type": "boolean",
                "default": "True",
                "description": "Enable parallel pipeline indexing"
            },
            {
                "key": "MAX_CONCURRENT_BATCHES",
                "label": "Max Concurrent Batches",
                "type": "number",
                "min": 1,
                "max": 10,
                "default": "3",
                "description": "Maximum number of concurrent batches"
            }
        ]
    },
    "colpali": {
        "name": "ColPali API",
        "description": "ColPali embedding model settings",
        "settings": [
            {
                "key": "COLPALI_MODE",
                "label": "Processing Mode",
                "type": "select",
                "options": ["cpu", "gpu"],
                "default": "gpu",
                "description": "Use CPU or GPU for embeddings"
            },
            {
                "key": "COLPALI_CPU_URL",
                "label": "CPU Service URL",
                "type": "text",
                "default": "http://localhost:7001",
                "description": "URL for CPU-based ColPali service"
            },
            {
                "key": "COLPALI_GPU_URL",
                "label": "GPU Service URL",
                "type": "text",
                "default": "http://localhost:7002",
                "description": "URL for GPU-based ColPali service"
            },
            {
                "key": "COLPALI_API_TIMEOUT",
                "label": "API Timeout (seconds)",
                "type": "number",
                "min": 10,
                "max": 600,
                "default": "300",
                "description": "Request timeout for ColPali API"
            }
        ]
    },
    "qdrant": {
        "name": "Qdrant Vector DB",
        "description": "Vector database configuration",
        "settings": [
            {
                "key": "QDRANT_URL",
                "label": "Qdrant URL",
                "type": "text",
                "default": "http://localhost:6333",
                "description": "URL for Qdrant vector database"
            },
            {
                "key": "QDRANT_COLLECTION_NAME",
                "label": "Collection Name",
                "type": "text",
                "default": "documents",
                "description": "Name of the Qdrant collection"
            },
            {
                "key": "QDRANT_SEARCH_LIMIT",
                "label": "Search Limit",
                "type": "number",
                "min": 1,
                "max": 1000,
                "default": "20",
                "description": "Maximum results from vector search"
            },
            {
                "key": "QDRANT_PREFETCH_LIMIT",
                "label": "Prefetch Limit",
                "type": "number",
                "min": 10,
                "max": 1000,
                "default": "200",
                "description": "Number of candidates to prefetch"
            },
            {
                "key": "QDRANT_ON_DISK",
                "label": "Store Vectors on Disk",
                "type": "boolean",
                "default": "True",
                "description": "Store vectors on disk instead of RAM"
            },
            {
                "key": "QDRANT_ON_DISK_PAYLOAD",
                "label": "Store Payload on Disk",
                "type": "boolean",
                "default": "True",
                "description": "Store payload data on disk"
            },
            {
                "key": "QDRANT_USE_BINARY",
                "label": "Use Binary Quantization",
                "type": "boolean",
                "default": "True",
                "description": "Enable binary quantization for vectors"
            },
            {
                "key": "QDRANT_BINARY_ALWAYS_RAM",
                "label": "Keep Binary Vectors in RAM",
                "type": "boolean",
                "default": "True",
                "description": "Always keep binary vectors in RAM"
            },
            {
                "key": "QDRANT_SEARCH_IGNORE_QUANT",
                "label": "Ignore Quantization in Search",
                "type": "boolean",
                "default": "False",
                "description": "Disable quantization during search"
            },
            {
                "key": "QDRANT_SEARCH_RESCORE",
                "label": "Enable Rescoring",
                "type": "boolean",
                "default": "True",
                "description": "Rescore results with full precision"
            },
            {
                "key": "QDRANT_SEARCH_OVERSAMPLING",
                "label": "Search Oversampling",
                "type": "number",
                "min": 1.0,
                "max": 10.0,
                "step": 0.1,
                "default": "2.0",
                "description": "Oversampling factor for search"
            },
            {
                "key": "QDRANT_MEAN_POOLING_ENABLED",
                "label": "Enable Mean Pooling",
                "type": "boolean",
                "default": "False",
                "description": "Use mean pooling for embeddings"
            }
        ]
    },
    "muvera": {
        "name": "MUVERA",
        "description": "Multi-Vector Embedding Retrieval Augmentation",
        "settings": [
            {
                "key": "MUVERA_ENABLED",
                "label": "Enable MUVERA",
                "type": "boolean",
                "default": "False",
                "description": "Enable MUVERA retrieval augmentation"
            },
            {
                "key": "MUVERA_K_SIM",
                "label": "K Similarity",
                "type": "number",
                "min": 1,
                "max": 20,
                "default": "6",
                "description": "Number of similar vectors to consider"
            },
            {
                "key": "MUVERA_DIM_PROJ",
                "label": "Projection Dimension",
                "type": "number",
                "min": 8,
                "max": 128,
                "default": "32",
                "description": "Dimensionality of projection space"
            },
            {
                "key": "MUVERA_R_REPS",
                "label": "Repetitions",
                "type": "number",
                "min": 1,
                "max": 100,
                "default": "20",
                "description": "Number of repetitions"
            },
            {
                "key": "MUVERA_RANDOM_SEED",
                "label": "Random Seed",
                "type": "number",
                "min": 0,
                "max": 9999,
                "default": "42",
                "description": "Random seed for reproducibility"
            }
        ]
    },
    "minio": {
        "name": "MinIO Storage",
        "description": "Object storage configuration",
        "settings": [
            {
                "key": "MINIO_URL",
                "label": "MinIO URL",
                "type": "text",
                "default": "http://localhost:9000",
                "description": "Internal MinIO service URL"
            },
            {
                "key": "MINIO_PUBLIC_URL",
                "label": "Public MinIO URL",
                "type": "text",
                "default": "http://localhost:9000",
                "description": "Public-facing MinIO URL"
            },
            {
                "key": "MINIO_ACCESS_KEY",
                "label": "Access Key",
                "type": "password",
                "default": "minioadmin",
                "description": "MinIO access key (username)"
            },
            {
                "key": "MINIO_SECRET_KEY",
                "label": "Secret Key",
                "type": "password",
                "default": "minioadmin",
                "description": "MinIO secret key (password)"
            },
            {
                "key": "MINIO_BUCKET_NAME",
                "label": "Bucket Name",
                "type": "text",
                "default": "documents",
                "description": "Name of the storage bucket"
            },
            {
                "key": "MINIO_WORKERS",
                "label": "Worker Threads",
                "type": "number",
                "min": 1,
                "max": 32,
                "default": "12",
                "description": "Number of concurrent upload workers"
            },
            {
                "key": "MINIO_RETRIES",
                "label": "Retry Attempts",
                "type": "number",
                "min": 0,
                "max": 10,
                "default": "3",
                "description": "Number of retry attempts on failure"
            },
            {
                "key": "MINIO_FAIL_FAST",
                "label": "Fail Fast",
                "type": "boolean",
                "default": "False",
                "description": "Stop immediately on first error"
            },
            {
                "key": "MINIO_PUBLIC_READ",
                "label": "Public Read Access",
                "type": "boolean",
                "default": "True",
                "description": "Allow public read access to files"
            },
            {
                "key": "MINIO_IMAGE_FMT",
                "label": "Image Format",
                "type": "select",
                "options": ["JPEG", "PNG", "WEBP"],
                "default": "JPEG",
                "description": "Image format for stored files"
            },
            {
                "key": "MINIO_IMAGE_QUALITY",
                "label": "Image Quality",
                "type": "number",
                "min": 1,
                "max": 100,
                "default": "75",
                "description": "Image compression quality (1-100)"
            }
        ]
    }
}


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
    valid_keys = []
    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            valid_keys.append(setting["key"])
    
    if update.key not in valid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration key: {update.key}"
        )
    
    # Update the runtime configuration
    runtime_cfg.set(update.key, update.value)
    
    # Invalidate service singletons if critical config changed
    # This forces services to re-initialize with new config on next use
    critical_keys = {
        "MUVERA_ENABLED", "QDRANT_COLLECTION_NAME", "QDRANT_MEAN_POOLING_ENABLED",
        "QDRANT_URL", "QDRANT_USE_BINARY", "QDRANT_ON_DISK"
    }
    if update.key in critical_keys:
        invalidate_services()
    
    return {
        "status": "ok",
        "message": f"Configuration updated: {update.key}",
        "key": update.key,
        "value": update.value,
        "services_invalidated": update.key in critical_keys,
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
