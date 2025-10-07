"""
Runtime configuration manager that allows dynamic updates.

This module provides a thread-safe way to access and update configuration
values at runtime. Values can be updated via the API and will be immediately
reflected across the application.
"""

import os
from typing import Dict, Any
from threading import Lock


class RuntimeConfig:
    """Thread-safe runtime configuration manager."""
    
    def __init__(self):
        self._config: Dict[str, str] = {}
        self._lock = Lock()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load all environment variables into the config."""
        with self._lock:
            # Copy all environment variables
            self._config = dict(os.environ)
    
    def get(self, key: str, default: str = "") -> str:
        """Get a configuration value."""
        with self._lock:
            return self._config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get a configuration value as integer."""
        value = self.get(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a configuration value as float."""
        value = self.get(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def has(self, key: str) -> bool:
        """Return True if the key has been explicitly set."""
        with self._lock:
            return key in self._config


    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a configuration value as boolean."""
        value = self.get(key, str(default))
        return value.strip().lower() in ("1", "true", "yes", "on")
    
    def set(self, key: str, value: str):
        """Set a configuration value (both in memory and environment)."""
        with self._lock:
            self._config[key] = value
            os.environ[key] = value
    
    def update(self, updates: Dict[str, str]):
        """Update multiple configuration values."""
        with self._lock:
            for key, value in updates.items():
                self._config[key] = value
                os.environ[key] = value
    
    def get_all(self) -> Dict[str, str]:
        """Get a copy of all configuration values."""
        with self._lock:
            return self._config.copy()
    
    def reload_from_env(self):
        """Reload configuration from environment variables."""
        self._load_from_env()


# Global runtime configuration instance
runtime_config = RuntimeConfig()


def get_runtime_config() -> RuntimeConfig:
    """Get the global runtime configuration instance."""
    return runtime_config
