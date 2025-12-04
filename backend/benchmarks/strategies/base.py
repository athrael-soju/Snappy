"""
Base class for retrieval strategies.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PIL import Image


@dataclass
class RetrievalResult:
    """Result from a retrieval operation."""

    # Retrieved documents/pages
    retrieved_pages: List[int] = field(default_factory=list)
    retrieved_images: List[Image.Image] = field(default_factory=list)

    # Extracted context for RAG
    context_text: str = ""
    context_regions: List[Dict[str, Any]] = field(default_factory=list)

    # Retrieval scores
    scores: List[float] = field(default_factory=list)

    # Timing information (in seconds)
    retrieval_time_s: float = 0.0
    embedding_time_s: float = 0.0
    region_filtering_time_s: float = 0.0

    # Error information
    error: Optional[str] = None


class BaseRetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""

    def __init__(
        self,
        colpali_url: str = "http://localhost:7000",
        **kwargs,
    ):
        """
        Initialize retrieval strategy.

        Args:
            colpali_url: URL of ColPali embedding service
            **kwargs: Additional strategy-specific parameters
        """
        self.colpali_url = colpali_url
        self.kwargs = kwargs

        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return strategy name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return strategy description."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize strategy resources (clients, connections, etc.)

        Called once before retrieval operations begin.
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query text
            **kwargs: Additional retrieval parameters

        Returns:
            RetrievalResult with retrieved documents and context
        """
        pass

    async def cleanup(self) -> None:
        """
        Clean up strategy resources.

        Called after all retrieval operations are complete.
        """
        self._initialized = False
        self._logger.info(f"Strategy {self.name} cleaned up")

    def is_initialized(self) -> bool:
        """Check if strategy is initialized."""
        return self._initialized

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of required services.

        Returns:
            Dict mapping service name to health status
        """
        return {}

    def get_config(self) -> Dict[str, Any]:
        """Return current strategy configuration."""
        return {
            "name": self.name,
            "colpali_url": self.colpali_url,
            **self.kwargs,
        }
