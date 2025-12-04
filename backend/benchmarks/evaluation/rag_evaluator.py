"""
RAG Evaluator for generating answers using retrieved context.

Uses OpenAI (GPT-5, gpt-5-nano, etc.) for answer generation.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from benchmarks.llm import LLMClient
from benchmarks.utils.images import encode_image_base64


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
            temperature: Sampling temperature (unused, kept for interface compatibility)
            max_tokens: Maximum tokens in response (unused, kept for interface compatibility)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.timeout = timeout
        self._logger = logging.getLogger(__name__)
        self._llm_client = LLMClient(api_key=api_key, model=model, timeout=timeout)

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
        """Call OpenAI API for answer generation using shared LLM client."""
        system_prompt = self._build_system_prompt()
        user_text = self._build_user_prompt(query, context)
        prompt = f"{system_prompt}\n\n{user_text}"

        # Log what we're sending to the LLM
        img_info = ""
        if images:
            img_info = f", images={len(images)}"
        if image_urls:
            img_info += f", image_urls={len(image_urls)}"
        self._logger.debug(
            f'LLM input: query="{query}"{img_info}, context={len(context)} chars'
        )

        # Build image list for multimodal input
        all_images = []
        if images:
            for img in images:
                img_b64 = self._image_to_base64(img)
                all_images.append(f"data:image/png;base64,{img_b64}")
        if image_urls:
            all_images.extend(image_urls)

        # Use shared LLM client
        response = await self._llm_client.generate(
            prompt=prompt,
            images=all_images if all_images else None,
            reasoning_effort="low",
        )

        self._logger.debug(
            f"OpenAI response: {len(response.output_text)} chars, output_tokens={response.output_tokens}"
        )

        return RAGResponse(
            answer=response.output_text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_s=0,  # Will be set by caller
            raw_response=response.raw_response,
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
        return encode_image_base64(image)

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
