"""
Configuration schema for Local Filesystem Storage.

Configure how extracted page images are stored on the local filesystem.
"""

from typing import Any, Dict

# Schema for Local Filesystem Storage
SCHEMA: Dict[str, Any] = {
    "storage": {
        "description": "Configure how extracted page images are stored.",
        "icon": "hard-drive",
        "name": "Local Storage",
        "order": 5,
        "settings": [
            {
                "default": "/app/storage",
                "description": "Base directory for file storage",
                "help_text": "Absolute path where files will be stored. "
                "In Docker, this should match the mounted volume path. "
                "The directory will be created if it doesn't exist. "
                "Ensure the application has write permissions.",
                "key": "LOCAL_STORAGE_PATH",
                "label": "Storage Path",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": "http://localhost:8000/files",
                "description": "Public base URL for serving files",
                "help_text": "Base URL used to construct file URLs returned to clients. "
                "In production, use your backend domain "
                "(e.g., https://api.example.com/files). "
                "In Docker, use http://localhost:8000/files for external access.",
                "key": "LOCAL_STORAGE_PUBLIC_URL",
                "label": "Public URL Base",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": "documents",
                "description": "Name of the storage bucket (auto-derived when empty)",
                "help_text": "When left blank, the backend derives a bucket name "
                "by slugifying the Qdrant collection name. This is used as "
                "the top-level directory within the storage path.",
                "key": "LOCAL_STORAGE_BUCKET_NAME",
                "label": "Bucket Name",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
        ],
        "ui_hidden": True,
    }
}
