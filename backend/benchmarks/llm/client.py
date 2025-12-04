"""
Shared LLM client for benchmarks.

Provides a unified interface for OpenAI API calls used by RAGEvaluator and LLMJudge.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API call."""

    output_text: str
    input_tokens: int
    output_tokens: int
    response_id: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMClient:
    """
    Shared LLM client for benchmark evaluations.

    Wraps OpenAI Responses API with support for:
    - Text-only inputs
    - Multimodal inputs (text + images)
    - Structured JSON outputs
    """

    def __init__(
        self,
        api_key: str,
        model: str = "",
        timeout: int = 60,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (required)
            model: Model name/ID
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.timeout = timeout
        self._client = OpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        *,
        images: Optional[List[str]] = None,
        reasoning_effort: str = "low",
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: Text prompt
            images: Optional list of base64-encoded images or URLs
            reasoning_effort: Reasoning effort level ("low", "medium", "high")

        Returns:
            LLMResponse with output and usage metrics
        """
        # Build input based on whether we have images
        if images:
            content = [{"type": "input_text", "text": prompt}]
            for img in images:
                if img.startswith("data:") or img.startswith("http"):
                    content.append({"type": "input_image", "image_url": img})
                else:
                    # Assume base64 without data URI prefix
                    content.append(
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{img}",
                        }
                    )
            api_input = [{"role": "user", "content": content}]
        else:
            api_input = prompt

        response = await asyncio.to_thread(
            self._client.responses.create,
            model=self.model,
            input=api_input,
            reasoning={"effort": reasoning_effort},
        )

        return LLMResponse(
            output_text=response.output_text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            response_id=response.id,
            raw_response={"output": response.output_text, "id": response.id},
        )

    async def generate_structured(
        self,
        prompt: str,
        *,
        schema: Dict[str, Any],
        schema_name: str = "response",
        reasoning_effort: str = "low",
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response from the LLM.

        Args:
            prompt: Text prompt
            schema: JSON schema for the response
            schema_name: Name for the schema
            reasoning_effort: Reasoning effort level

        Returns:
            Parsed JSON response matching the schema
        """
        response = await asyncio.to_thread(
            self._client.responses.create,
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
            reasoning={"effort": reasoning_effort},
        )

        return json.loads(response.output_text)
