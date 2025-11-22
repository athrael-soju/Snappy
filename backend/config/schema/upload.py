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
        ],
    }
}
