"""
Configuration schema for Object Storage.

Configure how extracted page images are stored.
"""

from typing import Any, Dict

# Schema for Object Storage
SCHEMA: Dict[str, Any] = {
    "storage": {
        "description": "Configure how extracted page images are stored.",
        "icon": "hard-drive",
        "name": "Object Storage",
        "order": 5,
        "settings": [
            {
                "default": "http://localhost:9000",
                "description": "Internal MinIO service URL",
                "help_text": "Internal endpoint for the MinIO object storage service. "
                "Used by the backend to upload files. Default port is "
                "9000. Change if MinIO runs on a different host or port. "
                "Format: http://hostname:port. Must be accessible from the "
                "backend application.",
                "key": "MINIO_URL",
                "label": "MinIO URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": "http://localhost:9000",
                "description": "Public-facing MinIO URL",
                "help_text": "Public endpoint for accessing stored files from "
                "browsers/clients. Can differ from MINIO_URL if using a "
                "reverse proxy or load balancer. In production, use your "
                "domain (e.g., https://storage.example.com). In "
                "development, same as MINIO_URL is fine.",
                "key": "MINIO_PUBLIC_URL",
                "label": "Public MinIO URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": "minioadmin",
                "description": "MinIO access key (username)",
                "help_text": "MinIO access key (similar to username) for "
                "authentication. Default 'minioadmin' is for development "
                "only. In production, create a dedicated access key with "
                "appropriate permissions. Never use default credentials in "
                "production - security risk!",
                "key": "MINIO_ACCESS_KEY",
                "label": "Access Key",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "password",
            },
            {
                "default": "minioadmin",
                "description": "MinIO secret key (password)",
                "help_text": "MinIO secret key (similar to password) for "
                "authentication. Default 'minioadmin' is for development "
                "only. In production, use a strong, randomly generated "
                "secret. Store securely in environment variables. Critical "
                "security setting - never expose publicly!",
                "key": "MINIO_SECRET_KEY",
                "label": "Secret Key",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "password",
            },
            {
                "default": "documents",
                "description": "Name of the storage bucket (auto-derived when empty)",
                "help_text": "When left blank, the backend derives a MinIO bucket name "
                "by slugifying the Qdrant collection name. Override only "
                "if you need to target a specific existing bucket.",
                "key": "MINIO_BUCKET_NAME",
                "label": "Bucket Name",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": True,
                "description": "Allow public read access to files",
                "help_text": "Makes uploaded files publicly accessible without "
                "authentication. Enable (True) for public applications "
                "where anyone can view documents. Disable (False) for "
                "private/internal applications requiring access control. "
                "Consider your security requirements carefully.",
                "key": "MINIO_PUBLIC_READ",
                "label": "Public Read Access",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
        ],
        "ui_hidden": True,
    }
}
