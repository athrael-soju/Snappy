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
                "default": 180,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Request timeout for DeepSeek OCR API calls.",
                "help_text": "Maximum time to wait for OCR responses. Increase for "
                "longer documents or CPU-only deployments; decrease "
                "for fast GPU hosts to catch misconfigurations "
                "quickly. Default 180s (3min) balances speed and "
                "reliability.",
                "key": "DEEPSEEK_OCR_API_TIMEOUT",
                "label": "OCR API Timeout (seconds)",
                "max": 600,
                "min": 30,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "critical": True,
                "default": 4,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Maximum concurrent OCR requests per batch.",
                "help_text": "Number of parallel OCR processing threads. Higher "
                "values increase throughput but require more memory "
                "and GPU resources. Recommended: 4 for single GPU, "
                "8-16 for multi-GPU.",
                "key": "DEEPSEEK_OCR_MAX_WORKERS",
                "label": "OCR Worker Threads",
                "max": 16,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "critical": True,
                "default": 20,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "HTTP connection pool size for OCR requests.",
                "help_text": "Maximum number of HTTP connections to maintain. "
                "Should be >= (Max Workers × 3) to handle retries. "
                "Increase if you see connection pool warnings in "
                "logs.",
                "key": "DEEPSEEK_OCR_POOL_SIZE",
                "label": "HTTP Connection Pool Size",
                "max": 100,
                "min": 5,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
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
            {
                "default": "",
                "depends_on": {"key": "DEEPSEEK_OCR_TASK", "value": "locate"},
                "description": "Specific text to find when using 'locate' task.",
                "help_text": "Enter the text you want to locate in documents. The "
                "OCR service will find and return bounding boxes for "
                "all instances of this text. Only used when task type "
                "is 'locate'.",
                "key": "DEEPSEEK_OCR_LOCATE_TEXT",
                "label": "Text to Locate",
                "type": "str",
                "ui_indent_level": 1,
                "ui_type": "text",
            },
            {
                "default": "",
                "depends_on": {"key": "DEEPSEEK_OCR_TASK", "value": "custom"},
                "description": "Custom prompt when using 'custom' task type.",
                "help_text": "Enter a custom prompt for specialized OCR tasks. Use "
                "<|grounding|> tag for spatial information. Example: "
                "'<|grounding|>Extract all form fields and their "
                "values'. Only used when task type is 'custom'.",
                "key": "DEEPSEEK_OCR_CUSTOM_PROMPT",
                "label": "Custom Prompt",
                "type": "str",
                "ui_indent_level": 1,
                "ui_type": "text",
            },
            {
                "critical": True,
                "default": True,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Include bounding box information in OCR results.",
                "help_text": "When enabled, OCR results include spatial "
                "coordinates for detected text elements. Useful for "
                "layout analysis and precise text location. Disable "
                "to reduce response size if you only need extracted "
                "text.",
                "key": "DEEPSEEK_OCR_INCLUDE_GROUNDING",
                "label": "Include Visual Grounding",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": True,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Extract and embed images from documents.",
                "help_text": "When enabled, figures and images within documents "
                "are extracted and included as base64-encoded data in "
                "markdown output. Useful for preserving visual "
                "content. Disable to reduce processing time and "
                "response size for text-only extraction.",
                "key": "DEEPSEEK_OCR_INCLUDE_IMAGES",
                "label": "Extract Embedded Images",
                "type": "bool",
                "ui_hidden": True,
                "ui_type": "boolean",
            },
        ],
    }
}
