"""
Configuration schema for Embedding Model.

ColPali embedding model configuration
"""

from typing import Any, Dict

# Schema for Embedding Model
SCHEMA: Dict[str, Any] = {
    "colpali": {
        "description": "ColPali embedding model configuration",
        "icon": "brain",
        "name": "Embedding Model",
        "order": 3,
        "settings": [
            {
                "default": "http://localhost:7000",
                "description": "URL for ColPali service",
                "help_text": "Endpoint for the embedding service. Format: "
                "http://hostname:port. Must be accessible from the backend "
                "application.",
                "key": "COLPALI_URL",
                "label": "ColPali Service URL",
                "type": "str",
                "ui_type": "text",
            },
            {
                "default": 300,
                "description": "Request timeout for ColPali API",
                "help_text": "Maximum time to wait for embedding generation requests "
                "before timing out. Large documents or CPU mode may need "
                "higher values (300-600s). GPU mode with small batches can "
                "use lower values (60-120s). Increase if you see timeout "
                "errors during document processing.",
                "key": "COLPALI_API_TIMEOUT",
                "label": "API Timeout (seconds)",
                "max": 600,
                "min": 10,
                "type": "int",
                "ui_type": "number",
            },
        ],
        "ui_hidden": True,
    }
}
