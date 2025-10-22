"""
Configuration schema - Single source of truth for all configuration settings.

This module defines:
1. Default values for all settings
2. Type information (str, int, float, bool, list)
3. UI metadata for the configuration panel (labels, descriptions, validation)

Both config.py and the API router import from here to ensure consistency.
"""

from typing import Any, Dict, List, Literal, Tuple

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


# Complete configuration schema with all metadata
# Structure: {category_key: {name, description, icon, order, settings: [{key, type, default, ...}]}}
# Settings can have 'depends_on' to create parent-child relationships
CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    "application": {
        "order": 1,
        "icon": "settings",
        "ui_hidden": True,
        "name": "Core Application",
        "description": "Core application settings",
        "settings": [
            {
                "key": "LOG_LEVEL",
                "type": "str",
                "default": "INFO",
                "label": "Log Level",
                "ui_type": "select",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "description": "Logging verbosity level",
                "help_text": "Controls the amount of detail in application logs. DEBUG shows all messages including detailed debugging info which is useful during development. INFO shows general informational messages about application flow. WARNING, ERROR, and CRITICAL show progressively fewer messages, only logging issues. Lower verbosity (ERROR/CRITICAL) improves performance but reduces troubleshooting capability.",
            },
            {
                "key": "ALLOWED_ORIGINS",
                "type": "list",
                "default": "*",
                "label": "Allowed CORS Origins",
                "ui_type": "text",
                "description": "Comma-separated list of allowed origins, or * for all",
                "help_text": "Defines which web domains can access your API via cross-origin requests. Use '*' to allow all origins (development only - NOT recommended for production). In production, specify exact domains (e.g., 'https://example.com,https://app.example.com') to prevent unauthorized access. This is a critical security setting that protects against cross-site request forgery.",
            },
            {
                "key": "UVICORN_RELOAD",
                "type": "bool",
                "default": True,
                "label": "Enable Auto Reload",
                "ui_type": "boolean",
                "description": "Automatically reload the API when files change",
                "help_text": "When enabled the development server watches for file changes and reloads automatically. This is convenient locally but should stay off in production to avoid the extra file-watcher overhead.",
            },
        ],
    },
    "ingestion": {
        "order": 2,
        "icon": "hard-drive",
        "name": "Document Ingestion",
        "description": "Controls batching and pipeline behaviour for document uploads.",
        "settings": [
            {
                "key": "BATCH_SIZE",
                "type": "int",
                "default": 4,
                "label": "Batch Size",
                "ui_type": "number",
                "min": 1,
                "max": 128,
                "description": "Number of pages processed per batch",
                "help_text": "Higher values boost throughput but require more memory. Lower values provide steadier progress feedback and are safer on small machines.",
            },
            {
                "key": "ENABLE_PIPELINE_INDEXING",
                "type": "bool",
                "default": True,
                "label": "Enable Pipeline Indexing",
                "ui_type": "boolean",
                "description": "Overlap embedding, storage, and upserts",
                "help_text": "When enabled the system automatically chooses a safe level of concurrency based on your hardware and batch size. Disable only for debugging or very resource-constrained hosts.",
            },
        ],
    },
    "uploads": {
        "order": 2.5,
        "icon": "upload",
        "name": "Uploads",
        "description": "Control allowed file types and user upload limits.",
        "settings": [
            {
                "key": "UPLOAD_ALLOWED_FILE_TYPES",
                "type": "list",
                "default": "pdf",
                "label": "Supported File Types",
                "ui_type": "multiselect",
                "options": ["pdf"],
                "description": "File extensions accepted during upload.",
                "help_text": "Select which file types end users can upload. The pipeline currently supports PDF files; additional types can be enabled as support is added.",
            },
            {
                "key": "UPLOAD_MAX_FILE_SIZE_MB",
                "type": "int",
                "default": 10,
                "label": "Maximum Size Per File (MB)",
                "ui_type": "number",
                "min": 1,
                "max": 200,
                "step": 1,
                "description": "Reject individual files larger than this size.",
                "help_text": "Protect your service from oversized uploads. Accepts values between 1 MB and 200 MB. Default keeps uploads lightweight while balancing usability.",
            },
            {
                "key": "UPLOAD_MAX_FILES",
                "type": "int",
                "default": 5,
                "label": "Maximum Files Per Upload",
                "ui_type": "number",
                "min": 1,
                "max": 20,
                "step": 1,
                "description": "Limit how many files a user can submit at once.",
                "help_text": "Restrict batch submissions to prevent overload. Accepts 1-20 files per request. Default allows modest batches without stressing the system.",
            },
            {
                "key": "UPLOAD_CHUNK_SIZE_BYTES",
                "type": "int",
                "default": 4 * 1024 * 1024,
                "label": "Upload Chunk Size (bytes)",
                "ui_type": "number",
                "min": 64 * 1024,
                "max": 16 * 1024 * 1024,
                "step": 64 * 1024,
                "description": "Chunk size used when streaming uploads to disk.",
                "help_text": "Controls how uploaded files are split into chunks while streaming to disk. Larger values reduce overhead but increase peak memory usage. Accepts values between 64 KB and 16 MB. Default 4 MB balances throughput and resource usage.",
            },
        ],
    },
    "colpali": {
        "order": 3,
        "ui_hidden": True,
        "icon": "brain",
        "name": "Embedding Model",
        "description": "ColPali embedding model configuration",
        "settings": [
            {
                "key": "COLPALI_URL",
                "type": "str",
                "default": "http://localhost:7000",
                "label": "ColPali Service URL",
                "ui_type": "text",
                "description": "URL for ColPali service",
                "help_text": "Endpoint for the embedding service. Format: http://hostname:port. Must be accessible from the backend application.",
            },
            {
                "key": "COLPALI_API_TIMEOUT",
                "type": "int",
                "default": 300,
                "label": "API Timeout (seconds)",
                "ui_type": "number",
                "min": 10,
                "max": 600,
                "description": "Request timeout for ColPali API",
                "help_text": "Maximum time to wait for embedding generation requests before timing out. Large documents or CPU mode may need higher values (300-600s). GPU mode with small batches can use lower values (60-120s). Increase if you see timeout errors during document processing.",
            },
        ],
    },
    "qdrant": {
        "order": 4,
        "icon": "database",
        "name": "Vector Database",
        "description": "Qdrant vector store and retrieval settings",
        "settings": [
            {
                "key": "QDRANT_URL",
                "ui_hidden": True,
                "type": "str",
                "default": "http://localhost:6333",
                "label": "Qdrant URL",
                "ui_type": "text",
                "description": "URL for Qdrant vector database",
                "help_text": "Connection endpoint for the Qdrant vector database service. Default port is 6333. Change if Qdrant runs on a different host or port. Format: http://hostname:port. Ensure the backend can reach this URL and that Qdrant is running.",
            },
            {
                "key": "QDRANT_HTTP_TIMEOUT",
                "type": "int",
                "default": 5,
                "label": "HTTP Timeout (seconds)",
                "ui_type": "number",
                "min": 5,
                "max": 600,
                "description": "Timeout for REST requests to Qdrant",
                "help_text": "Maximum time in seconds to wait when sending data to Qdrant over HTTP. Larger multi-vector batches (especially with MUVERA enabled) may need higher values to avoid write timeouts. Increase if you see 'WriteTimeout' errors during indexing.",
            },
            {
                "key": "QDRANT_EMBEDDED",
                "type": "bool",
                "default": False,
                "label": "Run Embedded Qdrant",
                "ui_type": "boolean",
                "description": "Use an embedded (in-memory) Qdrant instance",
                "help_text": "When enabled the backend starts an in-memory Qdrant instance (no external service required). Disable to connect to an external Qdrant deployment via QDRANT_URL.",
            },
            {
                "key": "QDRANT_COLLECTION_NAME",
                "type": "str",
                "default": "documents",
                "label": "Collection Name",
                "ui_type": "text",
                "description": "Name of the Qdrant collection (Also used for MinIO bucket)",
                "help_text": "Name of the Qdrant collection storing your document embeddings. Think of it as a database table. Changing this creates/uses a different collection. Useful for testing or separating data by environment (dev/staging/prod). Requires restart to take effect.",
            },
            {
                "key": "QDRANT_PREFETCH_LIMIT",
                "type": "int",
                "default": 200,
                "label": "Prefetch Limit",
                "ui_type": "number",
                "min": 10,
                "max": 1000,
                "description": "Number of candidates to prefetch",
                "help_text": "When mean pooling reranking is enabled, this many multivector candidates are prefetched before final ranking. Should be higher than SEARCH_LIMIT to ensure good recall. Higher values (200-1000) improve accuracy but slow queries. Has no effect when mean pooling is disabled.",
                "depends_on": {"key": "QDRANT_MEAN_POOLING_ENABLED", "value": True},
            },
            {
                "key": "QDRANT_ON_DISK",
                "type": "bool",
                "default": True,
                "label": "Store Vectors on Disk",
                "ui_type": "boolean",
                "description": "Store vectors on disk instead of RAM",
                "help_text": "Stores vector embeddings on disk rather than keeping them all in RAM. Enable (True) to save memory and support larger datasets. Disable (False) for maximum search speed with sufficient RAM. Disk storage uses memory-mapped files, offering good performance with lower memory usage. Recommended for most deployments.",
            },
            {
                "key": "QDRANT_ON_DISK_PAYLOAD",
                "type": "bool",
                "default": True,
                "label": "Store Payload on Disk",
                "ui_type": "boolean",
                "description": "Store payload data on disk",
                "help_text": "Stores document metadata (IDs, filenames, etc.) on disk instead of RAM. Similar to ON_DISK but for metadata. Enable (True) to reduce memory usage. Payload access is still fast via memory-mapped files. Recommended to keep enabled unless you need absolute maximum metadata retrieval speed.",
            },
            {
                "key": "QDRANT_USE_BINARY",
                "type": "bool",
                "default": False,
                "label": "Use Binary Quantization",
                "ui_type": "boolean",
                "description": "Enable binary quantization for vectors",
                "help_text": "Compresses vector embeddings to binary format (1-bit per dimension) reducing memory usage by 32x. Speeds up search while maintaining good accuracy. Enable for large datasets. Disable for maximum accuracy. When enabled, full-precision vectors are kept for rescoring. Recommended for production.",
            },
            {
                "key": "QDRANT_BINARY_ALWAYS_RAM",
                "type": "bool",
                "default": True,
                "label": "Keep Binary Vectors in RAM",
                "ui_type": "boolean",
                "description": "Always keep binary vectors in RAM",
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "help_text": "When binary quantization is enabled, keeps the compressed vectors in RAM for fastest search. Binary vectors are small (~32x smaller), so RAM usage is minimal. Disable only on extremely memory-constrained systems. Only applies when USE_BINARY is enabled.",
            },
            {
                "key": "QDRANT_SEARCH_IGNORE_QUANT",
                "type": "bool",
                "default": False,
                "label": "Ignore Quantization in Search",
                "ui_type": "boolean",
                "description": "Disable quantization during search",
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "help_text": "Forces search to use full-precision vectors even when quantization is enabled. Slower but more accurate initial search. Only useful for debugging quantization issues. Keep disabled (False) for normal operation. When False, quantized vectors are used for fast initial search followed by rescoring.",
            },
            {
                "key": "QDRANT_SEARCH_RESCORE",
                "type": "bool",
                "default": True,
                "label": "Enable Rescoring",
                "ui_type": "boolean",
                "description": "Rescore results with full precision",
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "help_text": "After initial search with quantized vectors, recalculates scores using full-precision vectors for better accuracy. Recommended to keep enabled (True). Slight performance cost but significantly improves result quality. Only relevant when using quantization.",
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
                "description": "Oversampling factor for search",
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "help_text": "Multiplier for initial search candidates when using quantization. Factor of 2.0 means searching 2x more candidates before rescoring. Higher values (3-5) improve recall but slower. Lower values (1-2) are faster. Balance between accuracy and speed. Only applies with quantization + rescoring enabled.",
            },
            {
                "key": "QDRANT_MEAN_POOLING_ENABLED",
                "type": "bool",
                "default": False,
                "label": "Enable Mean Pooling",
                "ui_type": "boolean",
                "description": "Use mean pooling for embeddings",
                "help_text": "Aggregates multi-vector document embeddings into single vectors using mean pooling. Reduces storage and speeds up search but loses fine-grained information. Enable for memory-constrained systems or very large datasets. Disable (recommended) to preserve full multi-vector representation quality. Requires service restart.",
            },
            {
                "key": "MUVERA_ENABLED",
                "type": "bool",
                "default": False,
                "label": "Enable MUVERA",
                "ui_type": "boolean",
                "description": "Multi-Vector Embedding Retrieval Augmentation for faster initial retrieval",
                "help_text": "Advanced: Enables MUVERA (Multi-Vector Embedding Retrieval Augmentation) for faster initial document retrieval. Creates additional compressed representations for speed. Increases indexing time and storage but accelerates search. Experimental feature - test thoroughly before production use. Requires service restart.",
            },
            {
                "key": "MUVERA_K_SIM",
                "type": "int",
                "default": 6,
                "label": "K Similarity",
                "ui_type": "number",
                "min": 1,
                "max": 20,
                "description": "Number of similar vectors to consider",
                "depends_on": {"key": "MUVERA_ENABLED", "value": True},
                "help_text": "Number of similar document patches to aggregate during MUVERA search. Higher values (10-20) improve accuracy but slower. Lower values (3-6) are faster. Typically 6 provides good balance. Only used when MUVERA is enabled.",
            },
            {
                "key": "MUVERA_DIM_PROJ",
                "type": "int",
                "default": 32,
                "label": "Projection Dimension",
                "ui_type": "number",
                "min": 8,
                "max": 128,
                "description": "Dimensionality of projection space",
                "depends_on": {"key": "MUVERA_ENABLED", "value": True},
                "help_text": "Dimensionality of MUVERA's compressed representation space. Higher values (64-128) preserve more information but use more storage. Lower values (8-32) are more compact but may lose accuracy. Default 32 balances compression and quality. Only used when MUVERA is enabled.",
            },
            {
                "key": "MUVERA_R_REPS",
                "type": "int",
                "default": 20,
                "label": "Repetitions",
                "ui_type": "number",
                "min": 1,
                "max": 100,
                "description": "Number of repetitions",
                "help_text": "Number of random projection repetitions used by MUVERA for redundancy. More repetitions (20-50) improve recall but increase storage and search time. Fewer (5-10) save resources. Default 20 provides reliable performance. Only used when MUVERA is enabled.",
                "depends_on": {"key": "MUVERA_ENABLED", "value": True},
            },
            {
                "key": "MUVERA_RANDOM_SEED",
                "type": "int",
                "default": 42,
                "label": "Random Seed",
                "ui_type": "number",
                "min": 0,
                "max": 9999,
                "description": "Random seed for reproducibility",
                "depends_on": {"key": "MUVERA_ENABLED", "value": True},
                "help_text": "Seed for MUVERA's random number generator to ensure reproducible projections. Same seed produces same projections across runs. Change only if you need different projection patterns. Default 42 is fine for most uses. Only used when MUVERA is enabled.",
            },
        ],
    },
    "storage": {
        "order": 5,
        "icon": "hard-drive",
        "name": "Object Storage",
        "description": "Configure how extracted page images are stored.",
        "settings": [
            {
                "key": "MINIO_URL",
                "ui_hidden": True,
                "type": "str",
                "default": "http://localhost:9000",
                "label": "MinIO URL",
                "ui_type": "text",
                "description": "Internal MinIO service URL",
                "help_text": "Internal endpoint for the MinIO object storage service. Used by the backend to upload files. Default port is 9000. Change if MinIO runs on a different host or port. Format: http://hostname:port. Must be accessible from the backend application.",
            },
            {
                "key": "MINIO_PUBLIC_URL",
                "ui_hidden": True,
                "type": "str",
                "default": "http://localhost:9000",
                "label": "Public MinIO URL",
                "ui_type": "text",
                "description": "Public-facing MinIO URL",
                "help_text": "Public endpoint for accessing stored files from browsers/clients. Can differ from MINIO_URL if using a reverse proxy or load balancer. In production, use your domain (e.g., https://storage.example.com). In development, same as MINIO_URL is fine.",
            },
            {
                "key": "MINIO_ACCESS_KEY",
                "ui_hidden": True,
                "type": "str",
                "default": "minioadmin",
                "label": "Access Key",
                "ui_type": "password",
                "description": "MinIO access key (username)",
                "help_text": "MinIO access key (similar to username) for authentication. Default 'minioadmin' is for development only. In production, create a dedicated access key with appropriate permissions. Never use default credentials in production - security risk!",
            },
            {
                "key": "MINIO_SECRET_KEY",
                "ui_hidden": True,
                "type": "str",
                "default": "minioadmin",
                "label": "Secret Key",
                "ui_type": "password",
                "description": "MinIO secret key (password)",
                "help_text": "MinIO secret key (similar to password) for authentication. Default 'minioadmin' is for development only. In production, use a strong, randomly generated secret. Store securely in environment variables. Critical security setting - never expose publicly!",
            },
            {
                "key": "MINIO_BUCKET_NAME",
                "ui_hidden": True,
                "type": "str",
                "default": "",
                "label": "Bucket Name",
                "ui_type": "text",
                "description": "Name of the storage bucket (auto-derived when empty)",
                "help_text": "When left blank, the backend derives a MinIO bucket name by slugifying the Qdrant collection name. Override only if you need to target a specific existing bucket.",
            },
            {
                "key": "MINIO_WORKERS",
                "ui_hidden": False,
                "type": "int",
                "default": 12,
                "label": "Worker Threads",
                "ui_type": "number",
                "min": 1,
                "max": 32,
                "description": "Number of concurrent upload workers (auto-sized)",
                "help_text": "The backend now sizes this automatically based on CPU cores and pipeline concurrency. Override via environment variables only when you need to cap or increase concurrency manually.",
            },
            {
                "key": "MINIO_RETRIES",
                "ui_hidden": True,
                "type": "int",
                "default": 3,
                "label": "Retry Attempts",
                "ui_type": "number",
                "min": 0,
                "max": 10,
                "description": "Number of retry attempts on failure (auto-sized)",
                "help_text": "The backend derives this from the chosen worker concurrency. Override via environment variables if you need stricter or more lenient retry behaviour.",
            },
            {
                "key": "MINIO_FAIL_FAST",
                "ui_hidden": True,
                "type": "bool",
                "default": False,
                "label": "Fail Fast",
                "ui_type": "boolean",
                "description": "Stop immediately on first error",
                "help_text": "Advanced troubleshooting option. When left unset the backend keeps the resilient default (False); override only if you need to abort batches on the first failure.",
            },
            {
                "key": "MINIO_PUBLIC_READ",
                "ui_hidden": True,
                "type": "bool",
                "default": True,
                "label": "Public Read Access",
                "ui_type": "boolean",
                "description": "Allow public read access to files",
                "help_text": "Makes uploaded files publicly accessible without authentication. Enable (True) for public applications where anyone can view documents. Disable (False) for private/internal applications requiring access control. Consider your security requirements carefully.",
            },
            {
                "key": "IMAGE_FORMAT",
                "type": "str",
                "default": "JPEG",
                "label": "Image Format",
                "ui_type": "select",
                "options": ["JPEG", "PNG", "WEBP"],
                "description": "Image format for stored files",
                "help_text": "Format for storing processed document images in MinIO. JPEG offers best compression with small quality loss (recommended). PNG is lossless but larger files. WEBP provides better compression than JPEG but may have compatibility issues with older systems. Choose based on storage space vs quality needs.",
            },
            {
                "key": "IMAGE_QUALITY",
                "type": "int",
                "default": 75,
                "label": "Image Quality",
                "ui_type": "number",
                "min": 1,
                "max": 100,
                "description": "Image compression quality (1-100)",
                "help_text": "Compression quality for JPEG/WEBP images (1-100). Higher values (85-95) preserve more detail but larger files. Lower values (50-75) save storage but may reduce visual quality. Default 75 balances quality and file size well. Applied to MinIO uploads. PNG ignores this setting as it's lossless.",
            },
        ],
    },
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
        "QDRANT_EMBEDDED",
        "QDRANT_COLLECTION_NAME",
        "QDRANT_MEAN_POOLING_ENABLED",
        "QDRANT_URL",
        "QDRANT_USE_BINARY",
        "QDRANT_ON_DISK",
    }
