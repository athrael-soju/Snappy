"""
Base class for benchmark strategies.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PIL import Image

from ..config import BenchmarkConfig
from ..dataset import BenchmarkSample
from ..metrics import TimingMetrics, TokenMetrics

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Result from a strategy execution."""

    # Predicted regions with bounding boxes
    regions: List[Dict[str, Any]] = field(default_factory=list)

    # LLM response
    llm_response: str = ""

    # Timing breakdown
    timing: TimingMetrics = field(default_factory=TimingMetrics)

    # Token usage
    tokens: TokenMetrics = field(default_factory=TokenMetrics)

    # Raw OCR content (for context building)
    ocr_content: str = ""

    # Any error that occurred
    error: Optional[str] = None


class BaseStrategy(ABC):
    """
    Abstract base class for benchmark strategies.

    Each strategy implements a different approach to:
    1. Process the document image (OCR, embeddings, etc.)
    2. Retrieve relevant regions for a query
    3. Generate an answer using an LLM
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name for identification."""
        pass

    @abstractmethod
    def process(
        self,
        sample: BenchmarkSample,
        image: Image.Image,
    ) -> StrategyResult:
        """
        Process a benchmark sample and return results.

        Args:
            sample: The benchmark sample containing query and ground truth
            image: The document image to process

        Returns:
            StrategyResult with regions, LLM response, timing, and token metrics
        """
        pass

    def _build_llm_prompt(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Build the prompt for the LLM.

        Args:
            query: The user's question
            context: The context (OCR content or region content)

        Returns:
            Formatted prompt string
        """
        return f"""Based on the following document content, answer the question.

Document content:
{context}

Question: {query}

Answer the question based only on the information provided in the document content. If the answer is not in the content, say "The answer is not found in the provided content."

Answer:"""

    def _format_regions_as_context(self, regions: List[Dict[str, Any]]) -> str:
        """
        Format regions into a context string for the LLM.

        Args:
            regions: List of region dictionaries with 'content' field

        Returns:
            Formatted context string
        """
        if not regions:
            return ""

        context_parts = []
        for i, region in enumerate(regions, 1):
            content = region.get("content", "")
            label = region.get("label", "region")
            relevance = region.get("relevance_score", None)

            if content:
                header = f"[{label.upper()}]"
                if relevance is not None:
                    header += f" (relevance: {relevance:.2f})"
                context_parts.append(f"{header}\n{content}")

        return "\n\n".join(context_parts)

    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.

        This is a simple estimation. For more accurate counts,
        use the tokenizer from the specific LLM being used.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token on average
        return len(text) // 4
