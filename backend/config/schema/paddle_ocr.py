"""
Configuration schema for PaddleOCR.

Optical character recognition service using PaddleOCR-VL-1.5 via vLLM.
"""

from typing import Any, Dict

# Schema for PaddleOCR
SCHEMA: Dict[str, Any] = {
    "paddle_ocr": {
        "description": "Optical character recognition service using PaddleOCR-VL for "
        "advanced text extraction.",
        "icon": "scan-text",
        "name": "PaddleOCR",
        "order": 3,
        "settings": [
            {
                "default": True,
                "description": "Toggle PaddleOCR integration for downstream "
                "workflows.",
                "help_text": "When enabled the backend initializes the PaddleOCR "
                "HTTP client for advanced text extraction. "
                "**Requires NVIDIA GPU** - disable if you don't have GPU "
                "or aren't running the PaddleOCR microservice.",
                "key": "PADDLE_OCR_ENABLED",
                "label": "Enable PaddleOCR",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": "http://localhost:8200",
                "depends_on": {"key": "PADDLE_OCR_ENABLED", "value": True},
                "description": "Base URL for the PaddleOCR vLLM service.",
                "help_text": "Endpoint for the OCR service. Defaults to the local "
                "Docker compose deployment. Update when the service "
                "runs on a different host or port.",
                "key": "PADDLE_OCR_URL",
                "label": "PaddleOCR URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "default": "OCR",
                "depends_on": {"key": "PADDLE_OCR_ENABLED", "value": True},
                "description": "Default OCR task type for document processing.",
                "help_text": "OCR: general text extraction with markdown formatting. "
                "Table Recognition: extract tables. "
                "Formula Recognition: extract mathematical formulas. "
                "Chart Recognition: extract chart data. "
                "Spotting: locate specific text in image. "
                "Seal Recognition: extract seal/stamp text.",
                "key": "PADDLE_OCR_TASK",
                "label": "Default Task Type",
                "options": [
                    "OCR",
                    "Table Recognition",
                    "Formula Recognition",
                    "Chart Recognition",
                    "Spotting",
                    "Seal Recognition",
                ],
                "type": "str",
                "ui_type": "select",
            },
            {
                "default": True,
                "depends_on": {"key": "PADDLE_OCR_ENABLED", "value": True},
                "description": "Enable image extraction and embedding in OCR results.",
                "help_text": "When enabled, the OCR service will extract image regions "
                "from the document and embed them in the markdown output. "
                "This is useful for preserving diagrams, charts, and photos within "
                "the extracted text. Disabling can improve performance "
                "and reduce memory usage if you only need text content.",
                "key": "PADDLE_OCR_INCLUDE_IMAGES",
                "label": "Include Images",
                "type": "bool",
                "ui_type": "boolean",
            },
        ],
    }
}
