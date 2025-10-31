"""
Application settings configuration using Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application settings
    app_name: str = "PaddleOCR-VL Service"
    app_version: str = "1.0.0"
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    debug: bool = False

    # API settings
    api_v1_prefix: str = "/api/v1"

    # File upload settings
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: set = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"}

    # PaddleOCR-VL settings
    use_gpu: bool = True
    device: str = "gpu"  # 'gpu' or 'cpu'
    enable_mkldnn: bool = True  # Enable CPU acceleration

    # Processing settings
    max_concurrent_requests: int = 3  # Limit concurrent processing to avoid OOM

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # 'json' or 'text'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
