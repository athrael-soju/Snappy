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
                "help_text": "Controls both batch granularity and parallelism across all pipeline stages "
                "(OCR, embedding, storage, upsert). Higher values process more pages simultaneously, "
                "improving throughput but requiring more GPU memory and delaying progress updates. "
                "Lower values provide more frequent progress feedback but slower overall processing. "
                "Recommended: 2 for 8GB GPU, 4 for 16GB GPU, 6-8 for 24GB+ GPU. "
                "Reduce to 1 if experiencing GPU memory errors.",
                "key": "BATCH_SIZE",
                "label": "Batch Size (Parallelism)",
                "max": 16,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
        ],
    }
}
