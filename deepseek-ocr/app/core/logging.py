"""
Logging configuration for DeepSeek OCR service.
"""

import logging
import sys


def setup_logging() -> logging.Logger:
    """Configure and return application logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("deepseek_ocr")


logger = setup_logging()
