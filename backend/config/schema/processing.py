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
                "Lower values provide steadier progress feedback. "
                "Recommended: 2-4 for CPU/Apple Silicon, 4-8 for NVIDIA GPU.",
                "key": "BATCH_SIZE",
                "label": "Batch Size",
                "max": 128,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 1,
                "description": "Maximum batches processing simultaneously across all pipeline stages",
                "help_text": "Limits total in-flight batches to prevent memory overflow with slow OCR. "
                "1 = strict ordering (one batch at a time, slowest), "
                "2-4 = balanced (some parallelism with memory safety), "
                "8+ = maximum throughput (fast stages run far ahead). "
                "Recommended: 1 for large documents or slow OCR.",
                "key": "PIPELINE_MAX_IN_FLIGHT_BATCHES",
                "label": "Max In-Flight Batches",
                "max": 32,
                "min": 1,
                "type": "int",
                "ui_type": "number",
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
