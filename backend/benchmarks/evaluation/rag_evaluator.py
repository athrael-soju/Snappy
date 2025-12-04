"""
RAG Evaluator for generating answers using retrieved context.

Supports multiple LLM providers:
- OpenAI (GPT-5, gpt-5-nano, etc.)
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
from openai import OpenAI
from PIL import Image

from benchmarks.config import LLMProvider


@dataclass
class RAGResponse:
    """Response from RAG answer generation."""

    answer: str
    input_tokens: int
    output_tokens: int
    latency_s: float
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
        model: str = "gpt-5-nano",
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

        # Initialize OpenAI client (sync for Responses API)
        self._openai_client = OpenAI(api_key=api_key) if api_key else None

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
                response = await self._call_openai(query, context, images, image_urls)
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
                    latency_s=0,
                    error=f"Unknown provider: {self.provider}",
                )

            response.latency_s = time.perf_counter() - start_time
            return response

        except Exception as e:
            self._logger.error(f"RAG generation failed: {e}", exc_info=True)
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_s=time.perf_counter() - start_time,
                error=str(e),
            )

    async def _call_openai(
        self,
        query: str,
        context: str,
        images: Optional[List[Image.Image]],
        image_urls: Optional[List[str]],
    ) -> RAGResponse:
        """Call OpenAI API for answer generation using official SDK."""
        if not self._openai_client:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_s=0,
                error="OpenAI API key not provided",
            )

        try:
            system_prompt = self._build_system_prompt()
            user_text = self._build_user_prompt(query, context)

            # Log what we're sending to the LLM
            img_info = ""
            if images:
                img_info = f", images={len(images)}"
            if image_urls:
                img_info += f", image_urls={len(image_urls)}"
            self._logger.debug(
                f"LLM input: query=\"{query}\"{img_info}, context={len(context)} chars"
            )

            # Build input based on whether we have images
            if images or image_urls:
                # Multimodal input with images
                content = [{"type": "input_text", "text": f"{system_prompt}\n\n{user_text}"}]

                # Add PIL images as base64
                if images:
                    for img in images:
                        img_b64 = self._image_to_base64(img)
                        content.append({
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{img_b64}",
                        })

                # Add image URLs
                if image_urls:
                    for url in image_urls:
                        content.append({
                            "type": "input_image",
                            "image_url": url,
                        })

                api_input = [{"role": "user", "content": content}]
            else:
                # Text-only input (simple string)
                api_input = f"{system_prompt}\n\n{user_text}"

            # Make API call using OpenAI Responses API
            response = await asyncio.to_thread(
                self._openai_client.responses.create,
                model=self.model,
                input=api_input,
                reasoning={"effort": "low"},
            )

            answer = response.output_text or ""
            self._logger.debug(f"OpenAI response: {len(answer)} chars, output_tokens={response.usage.output_tokens if response.usage else 0}")
            if not answer and response.usage and response.usage.output_tokens > 0:
                self._logger.warning(f"Empty output_text despite {response.usage.output_tokens} tokens. Raw: {response}")

            return RAGResponse(
                answer=answer,
                input_tokens=response.usage.input_tokens if response.usage else 0,
                output_tokens=response.usage.output_tokens if response.usage else 0,
                latency_s=0,  # Will be set by caller
                raw_response={"output": answer, "id": response.id},
            )
        except Exception as e:
            return RAGResponse(
                answer="",
                input_tokens=0,
                output_tokens=0,
                latency_s=0,
                error=f"OpenAI API error: {str(e)}",
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
                latency_s=0,
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
                latency_s=0,
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
            latency_s=0,
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
                latency_s=0,
                error=f"Ollama API error: {response.text}",
            )

        data = response.json()

        return RAGResponse(
            answer=data.get("response", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_s=0,
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
            tasks = [self.generate_answer(query, context) for query, context in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(
                        RAGResponse(
                            answer="",
                            input_tokens=0,
                            output_tokens=0,
                            latency_s=0,
                            error=str(result),
                        )
                    )
                else:
                    results.append(result)

        return results
