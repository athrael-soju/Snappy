"""
Configuration schema for Qdrant.

Qdrant vector store and retrieval settings
"""

from typing import Any, Dict

# Schema for Qdrant
SCHEMA: Dict[str, Any] = {
    "qdrant": {
        "description": "Qdrant vector store and retrieval settings",
        "icon": "database",
        "name": "Qdrant",
        "order": 4,
        "settings": [
            {
                "critical": True,
                "default": "http://localhost:6333",
                "description": "URL for Qdrant vector database",
                "help_text": "Connection endpoint for the Qdrant vector database "
                "service. Default port is 6333. Change if Qdrant runs on a "
                "different host or port. Format: http://hostname:port. "
                "Ensure the backend can reach this URL and that Qdrant is "
                "running.",
                "key": "QDRANT_URL",
                "label": "Qdrant URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": 5,
                "description": "Timeout for REST requests to Qdrant",
                "help_text": "Maximum time in seconds to wait when sending data to "
                "Qdrant over HTTP. Larger multi-vector batches may need "
                "higher values to avoid write timeouts. Increase if you see "
                "'WriteTimeout' errors during indexing.",
                "key": "QDRANT_HTTP_TIMEOUT",
                "label": "HTTP Timeout (seconds)",
                "max": 600,
                "min": 5,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "critical": True,
                "default": False,
                "description": "Use an embedded (in-memory) Qdrant instance",
                "help_text": "When enabled the backend starts an in-memory Qdrant "
                "instance (no external service required). Disable to "
                "connect to an external Qdrant deployment via QDRANT_URL.",
                "key": "QDRANT_EMBEDDED",
                "label": "Run Embedded",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": "documents",
                "description": "Name of the Qdrant collection (Also used for MinIO "
                "bucket)",
                "help_text": "Name of the Qdrant collection storing your document "
                "embeddings. Think of it as a database table. Changing this "
                "creates/uses a different collection. Useful for testing or "
                "separating data by environment (dev/staging/prod). "
                "Requires restart to take effect.",
                "key": "QDRANT_COLLECTION_NAME",
                "label": "Collection Name",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "critical": True,
                "default": 200,
                "depends_on": {"key": "QDRANT_MEAN_POOLING_ENABLED", "value": True},
                "description": "Number of candidates to prefetch",
                "help_text": "When mean pooling reranking is enabled, this many "
                "multivector candidates are prefetched before final "
                "ranking. Should be higher than SEARCH_LIMIT to ensure good "
                "recall. Higher values (200-1000) improve accuracy but slow "
                "queries. Has no effect when mean pooling is disabled.",
                "key": "QDRANT_PREFETCH_LIMIT",
                "label": "Prefetch Limit",
                "max": 1000,
                "min": 10,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "critical": True,
                "default": True,
                "description": "Store vectors on disk instead of RAM",
                "help_text": "Stores vector embeddings on disk rather than keeping them "
                "all in RAM. Enable (True) to save memory and support "
                "larger datasets. Disable (False) for maximum search speed "
                "with sufficient RAM. Disk storage uses memory-mapped "
                "files, offering good performance with lower memory usage. "
                "Recommended for most deployments.",
                "key": "QDRANT_ON_DISK",
                "label": "Store Vectors on Disk",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": True,
                "description": "Store payload data on disk",
                "help_text": "Stores document metadata (IDs, filenames, etc.) on disk "
                "instead of RAM. Similar to ON_DISK but for metadata. "
                "Enable (True) to reduce memory usage. Payload access is "
                "still fast via memory-mapped files. Recommended to keep "
                "enabled unless you need absolute maximum metadata "
                "retrieval speed.",
                "key": "QDRANT_ON_DISK_PAYLOAD",
                "label": "Store Payload on Disk",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": False,
                "description": "Enable binary quantization for vectors",
                "help_text": "Compresses vector embeddings to binary format (1-bit per "
                "dimension) reducing memory usage by 32x. Speeds up search "
                "while maintaining good accuracy. Enable for large "
                "datasets. Disable for maximum accuracy. When enabled, "
                "full-precision vectors are kept for rescoring. Recommended "
                "for production.",
                "key": "QDRANT_USE_BINARY",
                "label": "Use Binary Quantization",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": True,
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "description": "Always keep binary vectors in RAM",
                "help_text": "When binary quantization is enabled, keeps the compressed "
                "vectors in RAM for fastest search. Binary vectors are "
                "small (~32x smaller), so RAM usage is minimal. Disable "
                "only on extremely memory-constrained systems. Only applies "
                "when USE_BINARY is enabled.",
                "key": "QDRANT_BINARY_ALWAYS_RAM",
                "label": "Keep Binary Vectors in RAM",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": False,
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "description": "Disable quantization during search",
                "help_text": "Forces search to use full-precision vectors even when "
                "quantization is enabled. Slower but more accurate initial "
                "search. Only useful for debugging quantization issues. "
                "Keep disabled (False) for normal operation. When False, "
                "quantized vectors are used for fast initial search "
                "followed by rescoring.",
                "key": "QDRANT_SEARCH_IGNORE_QUANT",
                "label": "Ignore Quantization in Search",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": True,
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "description": "Rescore results with full precision",
                "help_text": "After initial search with quantized vectors, recalculates "
                "scores using full-precision vectors for better accuracy. "
                "Recommended to keep enabled (True). Slight performance "
                "cost but significantly improves result quality. Only "
                "relevant when using quantization.",
                "key": "QDRANT_SEARCH_RESCORE",
                "label": "Enable Rescoring",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": 2.0,
                "depends_on": {"key": "QDRANT_USE_BINARY", "value": True},
                "description": "Oversampling factor for search",
                "help_text": "Multiplier for initial search candidates when using "
                "quantization. Factor of 2.0 means searching 2x more "
                "candidates before rescoring. Higher values (3-5) improve "
                "recall but slower. Lower values (1-2) are faster. Balance "
                "between accuracy and speed. Only applies with quantization "
                "+ rescoring enabled.",
                "key": "QDRANT_SEARCH_OVERSAMPLING",
                "label": "Search Oversampling",
                "max": 10.0,
                "min": 1.0,
                "step": 0.1,
                "type": "float",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "critical": True,
                "default": False,
                "description": "Use mean pooling for embeddings",
                "help_text": "Aggregates multi-vector document embeddings into single "
                "vectors using mean pooling. Reduces storage and speeds up "
                "search but loses fine-grained information. Enable for "
                "memory-constrained systems or very large datasets. Disable "
                "(recommended) to preserve full multi-vector representation "
                "quality. Requires service restart.",
                "key": "QDRANT_MEAN_POOLING_ENABLED",
                "label": "Enable Mean Pooling",
                "type": "bool",
                "ui_type": "boolean",
            },
        ],
    }
}
