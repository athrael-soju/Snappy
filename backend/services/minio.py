"""Backward compatibility shims for the legacy services package."""

from app.integrations.minio_client import MinioBucketStat, MinioClient

MinioService = MinioClient

__all__ = ["MinioService", "MinioClient", "MinioBucketStat"]
