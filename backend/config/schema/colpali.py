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
                "before timing out. CPU systems or large documents may need "
                "higher values (300-600s). GPU systems with small batches can "
                "use lower values (60-120s). Increase if you see timeout "
                "errors during document processing.",
                "key": "COLPALI_API_TIMEOUT",
                "label": "API Timeout (seconds)",
                "max": 600,
                "min": 10,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": False,
                "description": "Show attention heatmaps on citation images",
                "help_text": "When enabled, search results include attention heatmaps "
                "that visualize which parts of the document are most relevant to "
                "your query. Heatmaps overlay the original image with bright spots "
                "indicating high attention areas. Useful for understanding model "
                "decisions but may increase response time.",
                "key": "COLPALI_SHOW_HEATMAPS",
                "label": "Show Retrieval Heatmaps",
                "type": "bool",
                "ui_type": "boolean",
            },
        ],
        "ui_hidden": False,
    }
}
