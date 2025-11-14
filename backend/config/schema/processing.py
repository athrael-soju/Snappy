"""
Configuration schema for Document Ingestion.

Controls batching and pipeline behaviour for document uploads.
"""

from typing import Any, Dict

# Schema for Document Ingestion
SCHEMA: Dict[str, Any] = {
    "ingestion": {
        "description": "Controls batching and pipeline behaviour for document uploads.",
        "icon": "hard-drive",
        "name": "Document Ingestion",
        "order": 2,
        "settings": [
            {
                "default": 4,
                "description": "Number of pages processed per batch",
                "help_text": "Higher values boost throughput but require more memory. "
                "Lower values provide steadier progress feedback and are "
                "safer on small machines.",
                "key": "BATCH_SIZE",
                "label": "Batch Size",
                "max": 128,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": True,
                "description": "Automatically optimize settings based on hardware",
                "help_text": "When enabled the system automatically chooses a safe "
                "level of concurrency based on your hardware and batch "
                "size. Disable only for debugging or very "
                "resource-constrained hosts.",
                "key": "ENABLE_AUTO_CONFIG_MODE",
                "label": "Enable Auto-Configuration",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": 15,
                "description": "Maximum seconds to wait for service restart during cancellation",
                "help_text": "When a job is cancelled, the system restarts ColPali and "
                "DeepSeek OCR services to stop ongoing processing. This "
                "controls how long to wait for each service to restart. "
                "Increase if services take longer to initialize on your "
                "hardware, decrease for faster cancellation response.",
                "key": "CANCELLATION_RESTART_TIMEOUT",
                "label": "Service Restart Timeout (seconds)",
                "max": 60,
                "min": 5,
                "type": "int",
                "ui_type": "number",
            },
        ],
    }
}
