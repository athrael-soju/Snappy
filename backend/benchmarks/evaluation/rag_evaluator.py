"""
RAG Evaluator for generating answers using retrieved context.

Uses OpenAI (GPT-5, gpt-5-nano, etc.) for answer generation.
"""

import asyncio
import base64
import logging
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from PIL import Image


@dataclass
class RAGResponse:
    """Response from RAG answer generation."""

    answer: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    raw_response: Optional[Dict[str, Any]] = None


class RAGEvaluator:
    """
    RAG evaluator for generating answers from retrieved context.

    Handles both text-based and vision-based (multimodal) RAG.
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        api_key: str = "",
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: int = 60,
    ):
        """
        Initialize RAG evaluator.

        Args:
            model: Model name/ID
            api_key: OpenAI API key (required)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self._logger = logging.getLogger(__name__)
        self._openai_client = OpenAI(api_key=api_key)

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
        response = await self._call_openai(query, context, images, image_urls)
        response.latency_s = time.perf_counter() - start_time
        return response

    async def _call_openai(
        self,
        query: str,
        context: str,
        images: Optional[List[Image.Image]],
        image_urls: Optional[List[str]],
    ) -> RAGResponse:
        """Call OpenAI API for answer generation using official SDK."""
        system_prompt = self._build_system_prompt()
        user_text = self._build_user_prompt(query, context)

        # Log what we're sending to the LLM
        img_info = ""
        if images:
            img_info = f", images={len(images)}"
        if image_urls:
            img_info += f", image_urls={len(image_urls)}"
        self._logger.debug(
            f'LLM input: query="{query}"{img_info}, context={len(context)} chars'
        )

        # Build input based on whether we have images
        if images or image_urls:
            # Multimodal input with images
            content = [
                {"type": "input_text", "text": f"{system_prompt}\n\n{user_text}"}
            ]

            # Add PIL images as base64
            if images:
                for img in images:
                    img_b64 = self._image_to_base64(img)
                    content.append(
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{img_b64}",
                        }
                    )

            # Add image URLs
            if image_urls:
                for url in image_urls:
                    content.append(
                        {
                            "type": "input_image",
                            "image_url": url,
                        }
                    )

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

        answer = response.output_text
        self._logger.debug(
            f"OpenAI response: {len(answer)} chars, output_tokens={response.usage.output_tokens}"
        )

        return RAGResponse(
            answer=answer,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_s=0,  # Will be set by caller
            raw_response={"output": answer, "id": response.id},
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for RAG."""
        return """You are a document question-answering assistant. Answer questions based ONLY on the provided context.

IMPORTANT: Be extremely concise. Give just the answer with minimal words.

Examples of GOOD answers:
Q: What color is the header?
A: blue

Q: Which cells are shaded in the table?
A: B2, C4, D1

Q: List the authors in order.
A: Smith, Jones, Brown

Q: What percentage is shown for revenue growth?
A: 15.3%

Q: Which section mentions the deadline?
A: Section 3.2; paragraph 4

Examples of BAD answers (too verbose):
Q: What color is the header?
A: The header in the document appears to be blue in color.

Q: List the authors in order.
A: Based on the document, the authors listed are Smith, Jones, and Brown in that order.

Q: What percentage is shown for revenue growth?
A: According to the context provided, the revenue growth percentage shown is 15.3%.

If the answer is not in the context, respond: "Not found in context"
Do NOT explain your reasoning or add extra words."""

    def _build_user_prompt(self, query: str, context: str) -> str:
        """Build user prompt with context and query."""
        if context and not context.startswith("[IMAGES:"):
            return f"""Context:
{context}

Q: {query}
A:"""
        else:
            # For image-only context
            return f"""Q: {query}
A:"""

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
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results
