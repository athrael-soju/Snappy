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
            {
                "default": False,
                "description": "Enable streaming pipeline for faster ingestion",
                "help_text": "Streaming pipeline processes PDF pages immediately as they're "
                "rasterized instead of waiting for all pages to finish. This provides: "
                "• 3-6x faster ingestion for large documents "
                "• First results visible in ~10 seconds vs 60+ seconds "
                "• Progressive user feedback as pages complete "
                "• Better resource utilization (GPU, CPU, I/O all busy). "
                "Note: This is experimental. Disable if you encounter issues.",
                "key": "USE_STREAMING_PIPELINE",
                "label": "Use Streaming Pipeline (Experimental)",
                "type": "bool",
                "ui_type": "switch",
            },
        ],
    }
}
