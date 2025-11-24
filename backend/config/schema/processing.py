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
                "description": "Number of pages processed in parallel per batch",
                "help_text": "Controls batch granularity and GPU memory usage. "
                "Higher values process more pages simultaneously, improving GPU throughput but requiring more memory. "
                "Lower values use less GPU memory but may be slower. "
                "Recommended: 2 for 8GB GPU, 4 for 16GB GPU, 6-8 for 24GB+ GPU. "
                "Reduce to 1 if experiencing GPU memory errors.",
                "key": "BATCH_SIZE",
                "label": "Batch Size",
                "max": 16,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 1,
                "description": "Maximum batches processing simultaneously in the pipeline",
                "help_text": "Controls system memory usage and cancellation responsiveness. "
                "Higher values allow more batches to be queued, improving throughput but consuming more memory "
                "and making cancellation slower. Lower values keep memory usage bounded and allow fast cancellation. "
                "Set to 1 for lowest memory usage and immediate cancellation response. "
                "Set to 2-4 for better throughput if memory allows.",
                "key": "PIPELINE_MAX_IN_FLIGHT_BATCHES",
                "label": "Max In-Flight Batches",
                "max": 8,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
        ],
    }
}
