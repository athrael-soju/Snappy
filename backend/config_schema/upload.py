"""
Configuration schema for Uploads.

Control allowed file types and user upload limits.
"""

from typing import Any, Dict

# Schema for Uploads
SCHEMA: Dict[str, Any] = {
    "uploads": {
        "description": "Control allowed file types and user upload limits.",
        "icon": "upload",
        "name": "Uploads",
        "order": 2.5,
        "settings": [
            {
                "default": "pdf",
                "description": "File extensions accepted during upload.",
                "help_text": "Select which file types end users can upload. The "
                "pipeline currently supports PDF files; additional types "
                "can be enabled as support is added.",
                "key": "UPLOAD_ALLOWED_FILE_TYPES",
                "label": "Supported File Types",
                "options": ["pdf"],
                "type": "list",
                "ui_type": "multiselect",
            },
            {
                "default": 10,
                "description": "Reject individual files larger than this size.",
                "help_text": "Protect your service from oversized uploads. Accepts "
                "values between 1 MB and 200 MB. Default keeps uploads "
                "lightweight while balancing usability.",
                "key": "UPLOAD_MAX_FILE_SIZE_MB",
                "label": "Maximum Size Per File (MB)",
                "max": 200,
                "min": 1,
                "step": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 5,
                "description": "Limit how many files a user can submit at once.",
                "help_text": "Restrict batch submissions to prevent overload. Accepts "
                "1-20 files per request. Default allows modest batches "
                "without stressing the system.",
                "key": "UPLOAD_MAX_FILES",
                "label": "Maximum Files Per Upload",
                "max": 20,
                "min": 1,
                "step": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 4.0,
                "description": "Chunk size in MB for streaming uploads to disk.",
                "help_text": "Controls how uploaded files are split into chunks while "
                "streaming to disk. Larger values reduce overhead but "
                "increase peak memory usage. Accepts values between 0.5 MB "
                "and 16 MB. Default 4 MB balances throughput and resource "
                "usage.",
                "key": "UPLOAD_CHUNK_SIZE_MBYTES",
                "label": "Upload Chunk Size (MB)",
                "max": 16,
                "min": 0.5,
                "step": 0.5,
                "type": "float",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "default": 4,
                "description": "Maximum parallel workers for upload processing.",
                "help_text": "Controls parallelism during upload operations (duplicate "
                "checks, metadata extraction, etc.). Higher values speed up "
                "processing for multiple files but increase CPU and network "
                "usage. Accepts 1-8 workers. Default 4 balances performance "
                "and resource usage for typical I/O-bound operations.",
                "key": "UPLOAD_MAX_WORKERS",
                "label": "Upload Max Workers",
                "max": 8,
                "min": 1,
                "step": 1,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
        ],
    }
}
