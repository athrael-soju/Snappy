"""
Configuration schema for DeepSeek OCR.

Optical character recognition service for advanced text extraction.
"""

from typing import Any, Dict

# Schema for DeepSeek OCR
SCHEMA: Dict[str, Any] = {
    "deepseek_ocr": {
        "description": "Optical character recognition service for advanced text "
        "extraction.",
        "icon": "scan-text",
        "name": "DeepSeek OCR",
        "order": 3,
        "settings": [
            {
                "critical": True,
                "default": False,
                "description": "Toggle DeepSeek OCR integration for downstream "
                "workflows.",
                "help_text": "When enabled the backend initializes the DeepSeek "
                "OCR HTTP client so future features can submit page "
                "images for transcription. Disable if you do not run "
                "the DeepSeek OCR microservice.",
                "key": "DEEPSEEK_OCR_ENABLED",
                "label": "Enable DeepSeek OCR",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": "http://localhost:8200",
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Base URL for the DeepSeek OCR microservice.",
                "help_text": "Endpoint for the OCR service. Defaults to the local "
                "Docker compose deployment. Update when the service "
                "runs on a different host or port.",
                "key": "DEEPSEEK_OCR_URL",
                "label": "DeepSeek OCR URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "critical": True,
                "default": "Gundam",
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Default OCR processing mode for quality/speed "
                "tradeoff.",
                "help_text": "Controls image resolution and processing strategy. "
                "Gundam (1024+640 tiles, cropped): best balance. Tiny "
                "(512×512): fastest. Small (640×640): quick. Base "
                "(1024×1024): standard. Large (1280×1280): highest "
                "quality. Larger modes need more GPU memory and time.",
                "key": "DEEPSEEK_OCR_MODE",
                "label": "Default Processing Mode",
                "options": ["Gundam", "Tiny", "Small", "Base", "Large"],
                "type": "str",
                "ui_type": "select",
            },
            {
                "critical": True,
                "default": "markdown",
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Default OCR task type for document processing.",
                "help_text": "Markdown: structured output with formatting "
                "(preserves tables, lists, etc.). Plain OCR: simple "
                "text extraction without formatting. Locate: find "
                "specific text with bounding boxes. Describe: "
                "generate image descriptions. Custom: use custom "
                "prompts. The task type determines both the prompt "
                "sent to the model and which output format is used as "
                "the primary result.",
                "key": "DEEPSEEK_OCR_TASK",
                "label": "Default Task Type",
                "options": ["markdown", "plain_ocr", "locate", "describe", "custom"],
                "type": "str",
                "ui_type": "select",
            },
        ],
    }
}
