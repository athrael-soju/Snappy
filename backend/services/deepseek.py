"""Backward compatibility shims for the legacy services package."""

from app.integrations.deepseek_client import DeepSeekOCRClient, DeepSeekOCRRequestError

DeepSeekOCRService = DeepSeekOCRClient

__all__ = ["DeepSeekOCRService", "DeepSeekOCRClient", "DeepSeekOCRRequestError"]
