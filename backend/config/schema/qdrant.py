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
                "default": "documents",
                "description": "Name of the Qdrant collection for document storage",
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
                "default": True,
                "description": "Enable binary quantization for 32x memory reduction",
                "help_text": "Binary quantization reduces memory usage by 32x while "
                "maintaining 95%+ accuracy. Highly recommended for production. "
                "When enabled, vectors are compressed to binary form in memory. "
                "Disable only for debugging or if you experience accuracy issues. "
                "Requires collection recreation to take effect.",
                "key": "QDRANT_USE_BINARY_QUANTIZATION",
                "label": "Enable Binary Quantization",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": True,
                "depends_on": {"key": "QDRANT_USE_BINARY_QUANTIZATION", "value": True},
                "description": "Keep binary vectors in RAM for faster search",
                "help_text": "When enabled, binary quantized vectors are kept in RAM "
                "instead of disk. This provides faster search performance at the "
                "cost of memory usage (still 32x less than uncompressed). "
                "Recommended for most deployments. Disable if running on very "
                "limited memory.",
                "key": "QDRANT_BINARY_ALWAYS_RAM",
                "label": "Binary Vectors in RAM",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": False,
                "description": "Enable mean pooling for two-stage re-ranking",
                "help_text": "Enables two-stage retrieval: prefetch with mean pooling, "
                "then re-rank with full multivector comparison. Improves accuracy "
                "but requires more compute.",
                "key": "QDRANT_MEAN_POOLING_ENABLED",
                "label": "Enable Mean Pooling & Re-ranking",
                "type": "bool",
                "ui_type": "boolean",
                "ui_confirm": True,
                "ui_confirm_message": "Changing this setting requires recreating your Qdrant collection. "
                "Existing collections will not have the required vector structures. "
                "Enable BEFORE indexing documents, or delete and recreate the collection after toggling.\n\n"
                "Continue?",
            },
            {
                "default": 200,
                "depends_on": {"key": "QDRANT_MEAN_POOLING_ENABLED", "value": True},
                "description": "Number of candidates to prefetch for re-ranking",
                "help_text": "When mean pooling is enabled, this many candidates are "
                "prefetched using mean pooling before re-ranking with full "
                "multivector comparison. Higher values improve recall but "
                "increase search latency. Recommended: 100-200 for most cases.",
                "key": "QDRANT_PREFETCH_LIMIT",
                "label": "Prefetch Limit",
                "max": 1000,
                "min": 10,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 10,
                "description": "Default number of search results to return",
                "help_text": "Default limit for search results when not specified in "
                "the request. Frontend typically overrides this with topK. "
                "Higher values return more results but increase response time.",
                "key": "QDRANT_SEARCH_LIMIT",
                "label": "Default Search Limit",
                "max": 100,
                "min": 1,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "default": True,
                "depends_on": {"key": "QDRANT_USE_BINARY_QUANTIZATION", "value": True},
                "description": "Rescore results with full precision after binary search",
                "help_text": "After searching with binary quantization, rescore top "
                "candidates using full-precision vectors. This ensures accuracy "
                "while maintaining speed benefits. Recommended to keep enabled.",
                "key": "QDRANT_SEARCH_RESCORE",
                "label": "Rescore After Binary Search",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
            {
                "default": 2.0,
                "depends_on": {"key": "QDRANT_USE_BINARY_QUANTIZATION", "value": True},
                "description": "Oversampling factor for binary quantization search",
                "help_text": "Retrieve more candidates than needed during binary search, "
                "then rescore. Higher values improve accuracy but increase "
                "latency. 2.0 means retrieve 2x results, then rescore to limit.",
                "key": "QDRANT_SEARCH_OVERSAMPLING",
                "label": "Search Oversampling Factor",
                "max": 5.0,
                "min": 1.0,
                "step": 0.1,
                "type": "float",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "default": False,
                "depends_on": {"key": "QDRANT_USE_BINARY_QUANTIZATION", "value": True},
                "description": "Skip quantization and use full precision vectors",
                "help_text": "When enabled, ignores binary quantization and searches "
                "using full precision vectors. Only use for debugging accuracy "
                "issues. Defeats the purpose of quantization.",
                "key": "QDRANT_SEARCH_IGNORE_QUANTIZATION",
                "label": "Ignore Quantization",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
        ],
    }
}
