"""
RAG Evaluator for generating answers using retrieved context.

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-4o-mini, etc.)
- Anthropic (Claude 3, etc.)
- Local models via Ollama/vLLM
"""

import asyncio
import base64
import logging
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image

from benchmarks.config import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG answer generation."""

    answer: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RAGEvaluator:
    """
    RAG evaluator for generating answers from retrieved context.

    Handles both text-based and vision-based (multimodal) RAG.
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: int = 60,
    ):
        """
        Initialize RAG evaluator.

        Args:
            provider: LLM provider to use
            model: Model name/ID
            api_key: OpenAI API key (if using OpenAI)
            anthropic_api_key: Anthropic API key (if using Anthropic)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.anthropic_api_key = anthropic_api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self._session = requests.Session()
        self._logger = logging.getLogger(__name__)

    async def generate_answer(
        self,
        query: str,
        context: str,
        images: Optional[List[Image.Image]] = None,
        image_urls: Optional[List[str]] = None,
    ) -> RAGResponse:
        """
        Generate an answer using the LLM with retrieved context.

        Args:
            query: User question
            context: Retrieved text context
            images: Optional list of PIL images for multimodal RAG
            image_urls: Optional list of image URLs for multimodal RAG

        Returns:
            RAGResponse with answer and metrics
        """
        start_time = time.perf_counter()

        try:
            if self.provider == LLMProvider.OPENAI:
                response = await self._call_openai(
                    query, context, images, image_urls
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(
                    query, context, images, image_urls
                )
            elif self.provider == LLMProvider.LOCAL:
                response = await self._call_local(query, context)
            else:
                return RAGResponse(
                    answer="",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=0,
                    error=f"Unknown provider: {self.provider}",
                )

            response.latency_ms = (time.perf_counter() - start_time) * 1000
            return response

        except Exception as e:
            self._logger.error(f"RAG generation failed: {e}", exc_info=True)
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                error=str(e),
            )

    async def _call_openai(
        self,
        query: str,
        context: str,
        images: Optional[List[Image.Image]],
        image_urls: Optional[List[str]],
    ) -> RAGResponse:
        """Call OpenAI API for answer generation."""
        if not self.api_key:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                error="OpenAI API key not provided",
            )

        # Build messages
        messages = []

        # System message
        system_prompt = self._build_system_prompt()
        messages.append({"role": "system", "content": system_prompt})

        # User message with context and query
        user_content = []

        # Add images if available (for vision models)
        if images or image_urls:
            if images:
                for img in images:
                    img_base64 = self._image_to_base64(img)
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                                "detail": "high",
                            },
                        }
                    )
            elif image_urls:
                for url in image_urls:
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": url, "detail": "high"},
                        }
                    )

        # Add text content
        user_text = self._build_user_prompt(query, context)
        user_content.append({"type": "text", "text": user_text})

        messages.append({"role": "user", "content": user_content})

        # Make API call
        response = await asyncio.to_thread(
            self._session.post,
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                error=f"OpenAI API error: {response.text}",
            )

        data = response.json()
        usage = data.get("usage", {})

        return RAGResponse(
            answer=data["choices"][0]["message"]["content"],
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=0,  # Will be set by caller
            raw_response=data,
        )

    async def _call_anthropic(
        self,
        query: str,
        context: str,
        images: Optional[List[Image.Image]],
        image_urls: Optional[List[str]],
    ) -> RAGResponse:
        """Call Anthropic API for answer generation."""
        if not self.anthropic_api_key:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                error="Anthropic API key not provided",
            )

        # Build content
        content = []

        # Add images if available
        if images:
            for img in images:
                img_base64 = self._image_to_base64(img)
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64,
                        },
                    }
                )

        # Add text
        user_text = self._build_user_prompt(query, context)
        content.append({"type": "text", "text": user_text})

        # Make API call
        response = await asyncio.to_thread(
            self._session.post,
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": self._build_system_prompt(),
                "messages": [{"role": "user", "content": content}],
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                error=f"Anthropic API error: {response.text}",
            )

        data = response.json()
        usage = data.get("usage", {})

        answer = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                answer += block.get("text", "")

        return RAGResponse(
            answer=answer,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            latency_ms=0,
            raw_response=data,
        )

    async def _call_local(
        self,
        query: str,
        context: str,
    ) -> RAGResponse:
        """Call local model (Ollama) for answer generation."""
        # Default to Ollama endpoint
        ollama_url = "http://localhost:11434/api/generate"

        prompt = f"{self._build_system_prompt()}\n\n{self._build_user_prompt(query, context)}"

        response = await asyncio.to_thread(
            self._session.post,
            ollama_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                error=f"Ollama API error: {response.text}",
            )

        data = response.json()

        return RAGResponse(
            answer=data.get("response", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=0,
            raw_response=data,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for RAG."""
        return """You are a helpful document question-answering assistant.
Your task is to answer questions based on the provided document context.

Instructions:
1. Answer the question directly and concisely
2. Only use information from the provided context
3. If the answer cannot be found in the context, say "I cannot find the answer in the provided context"
4. Do not make up information or hallucinate
5. Keep answers brief and to the point"""

    def _build_user_prompt(self, query: str, context: str) -> str:
        """Build user prompt with context and query."""
        if context and not context.startswith("[IMAGES:"):
            return f"""Context from retrieved documents:
---
{context}
---

Question: {query}

Answer:"""
        else:
            # For image-only context
            return f"""Based on the document images shown above, please answer the following question.

Question: {query}

Answer:"""

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string."""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def batch_generate(
        self,
        samples: List[Tuple[str, str]],  # List of (query, context) tuples
        batch_size: int = 10,
    ) -> List[RAGResponse]:
        """
        Generate answers for multiple samples.

        Args:
            samples: List of (query, context) tuples
            batch_size: Number of concurrent requests

        Returns:
            List of RAGResponse objects
        """
        results = []

        for i in range(0, len(samples), batch_size):
            batch = samples[i : i + batch_size]

            # Process batch concurrently
            tasks = [
                self.generate_answer(query, context) for query, context in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(
                        RAGResponse(
                            answer="",
                            input_tokens=0,
                            output_tokens=0,
                            latency_ms=0,
                            error=str(result),
                        )
                    )
                else:
                    results.append(result)

        return results
