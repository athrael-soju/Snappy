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
                "default": 20,
                "description": "Number of search results to return",
                "help_text": "Controls how many results to return from vector search. "
                "Higher values return more results but slightly slower. "
                "Typical range: 10-50 for good balance between relevance "
                "and performance.",
                "key": "QDRANT_SEARCH_LIMIT",
                "label": "Search Result Limit",
                "max": 100,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
        ],
    }
}
