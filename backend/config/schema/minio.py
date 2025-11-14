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
                "default": 6,
                "description": "Number of concurrent upload workers (auto-sized)",
                "help_text": "The backend now sizes this automatically based on CPU "
                "cores and pipeline concurrency. Override via environment "
                "variables only when you need to cap or increase "
                "concurrency manually.",
                "key": "MINIO_WORKERS",
                "label": "Worker Threads",
                "max": 32,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 3,
                "description": "Number of retry attempts on failure (auto-sized)",
                "help_text": "The backend derives this from the chosen worker "
                "concurrency. Override via environment variables if you "
                "need stricter or more lenient retry behaviour.",
                "key": "MINIO_RETRIES",
                "label": "Retry Attempts",
                "max": 10,
                "min": 0,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "default": False,
                "description": "Stop immediately on first error",
                "help_text": "Advanced troubleshooting option. When left unset the "
                "backend keeps the resilient default (False); override "
                "only if you need to abort batches on the first failure.",
                "key": "MINIO_FAIL_FAST",
                "label": "Fail Fast",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
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
            {
                "default": "JPEG",
                "description": "Image format for stored files",
                "help_text": "Format for storing processed document images in MinIO. "
                "JPEG offers best compression with small quality loss "
                "(recommended). PNG is lossless but larger files. WEBP "
                "provides better compression than JPEG but may have "
                "compatibility issues with older systems. Choose based on "
                "storage space vs quality needs.",
                "key": "IMAGE_FORMAT",
                "label": "Image Format",
                "options": ["JPEG", "PNG", "WEBP"],
                "type": "str",
                "ui_hidden": True,
                "ui_type": "select",
            },
            {
                "default": 75,
                "description": "Image compression quality (1-100)",
                "help_text": "Compression quality for JPEG/WEBP images (1-100). Higher "
                "values (85-95) preserve more detail but larger files. "
                "Lower values (50-75) save storage but may reduce visual "
                "quality. Default 75 balances quality and file size well. "
                "Applied to MinIO uploads. PNG ignores this setting as "
                "it's lossless.",
                "key": "IMAGE_QUALITY",
                "label": "Image Quality",
                "max": 100,
                "min": 1,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
        ],
        "ui_hidden": True,
    }
}
