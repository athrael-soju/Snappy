"""
Configuration schema for Core Application.

Core application settings
"""

from typing import Any, Dict

# Schema for Core Application
SCHEMA: Dict[str, Any] = {
    "application": {
        "description": "Core application settings",
        "icon": "settings",
        "name": "Core Application",
        "order": 1,
        "settings": [
            {
                "default": "INFO",
                "description": "Logging verbosity level",
                "help_text": "Controls the amount of detail in application logs. "
                "DEBUG shows all messages including detailed debugging "
                "info which is useful during development. INFO shows "
                "general informational messages about application "
                "flow. WARNING, ERROR, and CRITICAL show progressively "
                "fewer messages, only logging issues. Lower verbosity "
                "(ERROR/CRITICAL) improves performance but reduces "
                "troubleshooting capability.",
                "key": "LOG_LEVEL",
                "label": "Log Level",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "type": "str",
                "ui_type": "select",
            },
            {
                "default": "*",
                "description": "Comma-separated list of allowed origins, or * for "
                "all",
                "help_text": "Defines which web domains can access your API via "
                "cross-origin requests. Use '*' to allow all origins "
                "(development only - NOT recommended for production). "
                "In production, specify exact domains (e.g., "
                "'https://example.com,https://app.example.com') to "
                "prevent unauthorized access. This is a critical "
                "security setting that protects against cross-site "
                "request forgery.",
                "key": "ALLOWED_ORIGINS",
                "label": "Allowed CORS Origins",
                "type": "list",
                "ui_type": "text",
            },
            {
                "default": True,
                "description": "Automatically reload the API when files change",
                "help_text": "When enabled the development server watches for file "
                "changes and reloads automatically. This is convenient "
                "locally but should stay off in production to avoid "
                "the extra file-watcher overhead.",
                "key": "UVICORN_RELOAD",
                "label": "Enable Auto Reload",
                "type": "bool",
                "ui_type": "boolean",
            },
        ],
        "ui_hidden": True,
    }
}
