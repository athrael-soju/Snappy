"""
Configuration schema - Single source of truth for all configuration settings.

This module defines:
1. Default values for all settings
2. Type information (str, int, float, bool, list)
3. UI metadata for the configuration panel (labels, descriptions, validation)

Both config.py and the API router import from here to ensure consistency.
"""

from typing import Dict, Any, List, Tuple, Literal


# Type definitions
ConfigType = Literal["str", "int", "float", "bool", "list"]
ConfigDefault = Any  # The actual default value (typed)
ConfigUIType = Literal["text", "number", "boolean", "select", "password"]


def _infer_ui_type(config_type: ConfigType, has_options: bool = False) -> ConfigUIType:
    """Infer UI input type from config type."""
    if has_options:
        return "select"
    mapping = {
        "str": "text",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "list": "text"
    }
    return mapping.get(config_type, "text")


# Complete configuration schema with all metadata
# Structure: {category_key: {name, description, settings: [{key, type, default, ...}]}}
CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    "application": {
        "name": "Application",
        "description": "Core application settings",
        "settings": [
            {
                "key": "LOG_LEVEL",
                "type": "str",
                "default": "INFO",
                "label": "Log Level",
                "ui_type": "select",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "description": "Logging verbosity level"
            },
            {
                "key": "ALLOWED_ORIGINS",
                "type": "list",
                "default": "*",
                "label": "Allowed CORS Origins",
                "ui_type": "text",
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
                "type": "int",
                "default": 5,
                "label": "Default Top K Results",
                "ui_type": "number",
                "min": 1,
                "max": 100,
                "description": "Default number of search results to return"
            },
            {
                "key": "MAX_TOKENS",
                "type": "int",
                "default": 500,
                "label": "Max Tokens",
                "ui_type": "number",
                "min": 100,
                "max": 4096,
                "description": "Maximum tokens for text generation"
            },
            {
                "key": "BATCH_SIZE",
                "type": "int",
                "default": 12,
                "label": "Batch Size",
                "ui_type": "number",
                "min": 1,
                "max": 128,
                "description": "Number of documents to process in parallel"
            },
            {
                "key": "WORKER_THREADS",
                "type": "int",
                "default": 8,
                "label": "Worker Threads",
                "ui_type": "number",
                "min": 1,
                "max": 32,
                "description": "Number of worker threads for processing"
            },
            {
                "key": "ENABLE_PIPELINE_INDEXING",
                "type": "bool",
                "default": True,
                "label": "Enable Pipeline Indexing",
                "ui_type": "boolean",
                "description": "Enable parallel pipeline indexing"
            },
            {
                "key": "MAX_CONCURRENT_BATCHES",
                "type": "int",
                "default": 3,
                "label": "Max Concurrent Batches",
                "ui_type": "number",
                "min": 1,
                "max": 10,
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
                "type": "str",
                "default": "gpu",
                "label": "Processing Mode",
                "ui_type": "select",
                "options": ["cpu", "gpu"],
                "description": "Use CPU or GPU for embeddings"
            },
            {
                "key": "COLPALI_CPU_URL",
                "type": "str",
                "default": "http://localhost:7001",
                "label": "CPU Service URL",
                "ui_type": "text",
                "description": "URL for CPU-based ColPali service"
            },
            {
                "key": "COLPALI_GPU_URL",
                "type": "str",
                "default": "http://localhost:7002",
                "label": "GPU Service URL",
                "ui_type": "text",
                "description": "URL for GPU-based ColPali service"
            },
            {
                "key": "COLPALI_API_BASE_URL",
                "type": "str",
                "default": "",
                "label": "API Base URL (Override)",
                "ui_type": "text",
                "description": "Override URL (leave empty for auto mode selection)"
            },
            {
                "key": "COLPALI_API_TIMEOUT",
                "type": "int",
                "default": 300,
                "label": "API Timeout (seconds)",
                "ui_type": "number",
                "min": 10,
                "max": 600,
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
                "type": "str",
                "default": "http://localhost:6333",
                "label": "Qdrant URL",
                "ui_type": "text",
                "description": "URL for Qdrant vector database"
            },
            {
                "key": "QDRANT_COLLECTION_NAME",
                "type": "str",
                "default": "documents",
                "label": "Collection Name",
                "ui_type": "text",
                "description": "Name of the Qdrant collection"
            },
            {
                "key": "QDRANT_SEARCH_LIMIT",
                "type": "int",
                "default": 20,
                "label": "Search Limit",
                "ui_type": "number",
                "min": 1,
                "max": 1000,
                "description": "Maximum results from vector search"
            },
            {
                "key": "QDRANT_PREFETCH_LIMIT",
                "type": "int",
                "default": 200,
                "label": "Prefetch Limit",
                "ui_type": "number",
                "min": 10,
                "max": 1000,
                "description": "Number of candidates to prefetch"
            },
            {
                "key": "QDRANT_ON_DISK",
                "type": "bool",
                "default": True,
                "label": "Store Vectors on Disk",
                "ui_type": "boolean",
                "description": "Store vectors on disk instead of RAM"
            },
            {
                "key": "QDRANT_ON_DISK_PAYLOAD",
                "type": "bool",
                "default": True,
                "label": "Store Payload on Disk",
                "ui_type": "boolean",
                "description": "Store payload data on disk"
            },
            {
                "key": "QDRANT_USE_BINARY",
                "type": "bool",
                "default": True,
                "label": "Use Binary Quantization",
                "ui_type": "boolean",
                "description": "Enable binary quantization for vectors"
            },
            {
                "key": "QDRANT_BINARY_ALWAYS_RAM",
                "type": "bool",
                "default": True,
                "label": "Keep Binary Vectors in RAM",
                "ui_type": "boolean",
                "description": "Always keep binary vectors in RAM"
            },
            {
                "key": "QDRANT_SEARCH_IGNORE_QUANT",
                "type": "bool",
                "default": False,
                "label": "Ignore Quantization in Search",
                "ui_type": "boolean",
                "description": "Disable quantization during search"
            },
            {
                "key": "QDRANT_SEARCH_RESCORE",
                "type": "bool",
                "default": True,
                "label": "Enable Rescoring",
                "ui_type": "boolean",
                "description": "Rescore results with full precision"
            },
            {
                "key": "QDRANT_SEARCH_OVERSAMPLING",
                "type": "float",
                "default": 2.0,
                "label": "Search Oversampling",
                "ui_type": "number",
                "min": 1.0,
                "max": 10.0,
                "step": 0.1,
                "description": "Oversampling factor for search"
            },
            {
                "key": "QDRANT_MEAN_POOLING_ENABLED",
                "type": "bool",
                "default": False,
                "label": "Enable Mean Pooling",
                "ui_type": "boolean",
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
                "type": "bool",
                "default": False,
                "label": "Enable MUVERA",
                "ui_type": "boolean",
                "description": "Enable MUVERA retrieval augmentation"
            },
            {
                "key": "MUVERA_K_SIM",
                "type": "int",
                "default": 6,
                "label": "K Similarity",
                "ui_type": "number",
                "min": 1,
                "max": 20,
                "description": "Number of similar vectors to consider"
            },
            {
                "key": "MUVERA_DIM_PROJ",
                "type": "int",
                "default": 32,
                "label": "Projection Dimension",
                "ui_type": "number",
                "min": 8,
                "max": 128,
                "description": "Dimensionality of projection space"
            },
            {
                "key": "MUVERA_R_REPS",
                "type": "int",
                "default": 20,
                "label": "Repetitions",
                "ui_type": "number",
                "min": 1,
                "max": 100,
                "description": "Number of repetitions"
            },
            {
                "key": "MUVERA_RANDOM_SEED",
                "type": "int",
                "default": 42,
                "label": "Random Seed",
                "ui_type": "number",
                "min": 0,
                "max": 9999,
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
                "type": "str",
                "default": "http://localhost:9000",
                "label": "MinIO URL",
                "ui_type": "text",
                "description": "Internal MinIO service URL"
            },
            {
                "key": "MINIO_PUBLIC_URL",
                "type": "str",
                "default": "http://localhost:9000",
                "label": "Public MinIO URL",
                "ui_type": "text",
                "description": "Public-facing MinIO URL"
            },
            {
                "key": "MINIO_ACCESS_KEY",
                "type": "str",
                "default": "minioadmin",
                "label": "Access Key",
                "ui_type": "password",
                "description": "MinIO access key (username)"
            },
            {
                "key": "MINIO_SECRET_KEY",
                "type": "str",
                "default": "minioadmin",
                "label": "Secret Key",
                "ui_type": "password",
                "description": "MinIO secret key (password)"
            },
            {
                "key": "MINIO_BUCKET_NAME",
                "type": "str",
                "default": "documents",
                "label": "Bucket Name",
                "ui_type": "text",
                "description": "Name of the storage bucket"
            },
            {
                "key": "MINIO_WORKERS",
                "type": "int",
                "default": 12,
                "label": "Worker Threads",
                "ui_type": "number",
                "min": 1,
                "max": 32,
                "description": "Number of concurrent upload workers"
            },
            {
                "key": "MINIO_RETRIES",
                "type": "int",
                "default": 3,
                "label": "Retry Attempts",
                "ui_type": "number",
                "min": 0,
                "max": 10,
                "description": "Number of retry attempts on failure"
            },
            {
                "key": "MINIO_FAIL_FAST",
                "type": "bool",
                "default": False,
                "label": "Fail Fast",
                "ui_type": "boolean",
                "description": "Stop immediately on first error"
            },
            {
                "key": "MINIO_PUBLIC_READ",
                "type": "bool",
                "default": True,
                "label": "Public Read Access",
                "ui_type": "boolean",
                "description": "Allow public read access to files"
            },
            {
                "key": "MINIO_IMAGE_FMT",
                "type": "str",
                "default": "JPEG",
                "label": "Image Format",
                "ui_type": "select",
                "options": ["JPEG", "PNG", "WEBP"],
                "description": "Image format for stored files"
            },
            {
                "key": "MINIO_IMAGE_QUALITY",
                "type": "int",
                "default": 75,
                "label": "Image Quality",
                "ui_type": "number",
                "min": 1,
                "max": 100,
                "description": "Image compression quality (1-100)"
            }
        ]
    }
}


def get_config_defaults() -> Dict[str, Tuple[ConfigType, Any]]:
    """
    Extract type information and defaults for config.py.
    
    Returns:
        Dict mapping config key to (type, default_value)
        Example: {"LOG_LEVEL": ("str", "INFO"), "BATCH_SIZE": ("int", 12)}
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
            "settings": []
        }
        
        for setting in category["settings"]:
            api_setting = {
                "key": setting["key"],
                "label": setting["label"],
                "type": setting.get("ui_type", _infer_ui_type(setting["type"], "options" in setting)),
                "default": str(setting["default"]),  # Convert to string for UI
                "description": setting["description"]
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
            
            api_schema[cat_key]["settings"].append(api_setting)
    
    return api_schema


def get_all_config_keys() -> List[str]:
    """Get list of all configuration keys."""
    keys = []
    for category in CONFIG_SCHEMA.values():
        for setting in category["settings"]:
            keys.append(setting["key"])
    return keys


def get_critical_keys() -> set:
    """
    Get set of config keys that require service invalidation on change.
    These are settings that affect service initialization.
    """
    return {
        "MUVERA_ENABLED",
        "QDRANT_COLLECTION_NAME",
        "QDRANT_MEAN_POOLING_ENABLED",
        "QDRANT_URL",
        "QDRANT_USE_BINARY",
        "QDRANT_ON_DISK"
    }
