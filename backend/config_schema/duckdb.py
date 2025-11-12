"""
Configuration schema for DuckDB Analytics.

DuckDB storage for OCR data analytics and exploration.
"""

from typing import Any, Dict

# Schema for DuckDB Analytics
SCHEMA: Dict[str, Any] = {
    "duckdb": {
        "description": "DuckDB storage for OCR data analytics and exploration.",
        "icon": "database",
        "name": "DuckDB Analytics",
        "order": 6,
        "settings": [
            {
                "critical": True,
                "default": False,
                "depends_on": {"key": "DEEPSEEK_OCR_ENABLED", "value": True},
                "description": "Store OCR results in DuckDB for analytics",
                "help_text": "When enabled, OCR results are stored in DuckDB database "
                "alongside MinIO storage. This enables SQL queries, "
                "full-text search, and analytics on OCR data. Dependent on "
                "DeepSeek OCR being enabled. DuckDB storage failures won't "
                "block the indexing pipeline.",
                "key": "DUCKDB_ENABLED",
                "label": "Enable DuckDB Storage",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "critical": True,
                "default": "http://localhost:8300",
                "depends_on": {"key": "DUCKDB_ENABLED", "value": True},
                "description": "URL of the DuckDB analytics service",
                "help_text": "HTTP endpoint for the DuckDB analytics microservice. The "
                "backend sends OCR data to this service for storage. "
                "Default port is 8300. Format: http://hostname:port. Must "
                "be accessible from the backend application.",
                "key": "DUCKDB_URL",
                "label": "DuckDB Service URL",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "critical": True,
                "default": "documents",
                "depends_on": {"key": "DUCKDB_ENABLED", "value": True},
                "description": "Logical name for the DuckDB database",
                "help_text": "Used to label and organize OCR analytics data within "
                "DuckDB. Keep this in sync with your Qdrant "
                "collection/minio bucket naming for clarity. Changing this "
                "value typically requires reinitialising DuckDB storage.",
                "key": "DUCKDB_DATABASE_NAME",
                "label": "DuckDB Database Name",
                "type": "str",
                "ui_hidden": True,
                "ui_type": "text",
            },
            {
                "critical": True,
                "default": 30,
                "depends_on": {"key": "DUCKDB_ENABLED", "value": True},
                "description": "Timeout for DuckDB API requests",
                "help_text": "Maximum time to wait for DuckDB API responses in seconds. "
                "Higher values (60-120) for large batches or slow networks. "
                "Lower values (10-30) for faster failure detection. Default "
                "30 seconds is suitable for most cases.",
                "key": "DUCKDB_API_TIMEOUT",
                "label": "API Timeout (seconds)",
                "max": 300,
                "min": 5,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
            {
                "default": 5,
                "depends_on": {"key": "DUCKDB_ENABLED", "value": True},
                "description": "Number of pages to batch before sending to DuckDB",
                "help_text": "OCR results are batched before sending to DuckDB for "
                "efficiency. Higher values (20-50) reduce network overhead "
                "but increase memory usage. Lower values (5-10) provide "
                "more frequent updates. Default 10 balances performance and "
                "responsiveness.",
                "key": "DUCKDB_BATCH_SIZE",
                "label": "Batch Size",
                "max": 100,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": 3,
                "depends_on": {"key": "DUCKDB_ENABLED", "value": True},
                "description": "Number of retry attempts on failure",
                "help_text": "Number of times to retry failed DuckDB storage operations. "
                "Higher values (5-10) improve resilience but may delay "
                "error reporting. Lower values (1-3) fail faster. Zero "
                "disables retries. Default 3 provides good balance.",
                "key": "DUCKDB_RETRY_ATTEMPTS",
                "label": "Retry Attempts",
                "max": 10,
                "min": 0,
                "type": "int",
                "ui_hidden": True,
                "ui_type": "number",
            },
        ],
    }
}
