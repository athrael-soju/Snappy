"""
HuggingFace Spaces compatibility layer for FastAPI OCR service
This makes ocr_service.py work on HuggingFace Spaces

Import the FastAPI app from ocr_service.py
HuggingFace Spaces will run: uvicorn app:app --port 7860
"""

from ocr_service import app

# Export the app for HuggingFace Spaces
# The Dockerfile CMD runs: uvicorn app:app
__all__ = ["app"]
