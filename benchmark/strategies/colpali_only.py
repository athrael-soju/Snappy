"""
ColPali-only baseline strategy.

This strategy:
1. Uses ColPali to generate image and query embeddings
2. Returns the entire page as context (no region-level filtering)
3. Sends OCR content to the LLM for answer generation

This represents a VLM-based approach that identifies relevant pages
but doesn't provide sub-page localization.
"""

import io
import logging
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from ..config import BenchmarkConfig
from ..dataset import BenchmarkSample
from ..metrics import Timer, TimingMetrics, TokenMetrics
from .base import BaseStrategy, StrategyResult

logger = logging.getLogger(__name__)


class ColPaliOnlyStrategy(BaseStrategy):
    """
    ColPali-only baseline: Use VLM embeddings for page retrieval.

    This approach:
    - Uses ColPali's patch embeddings for semantic matching
    - Returns full page content (no sub-page localization)
    - Assumes ColPali has already identified the correct page

    Since we assume ColPali returns the correct result, we skip
    the actual retrieval step and just measure the downstream
    RAG performance using full page context.
    """

    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return "colpali_only"

    def process(
        self,
        sample: BenchmarkSample,
        image: Image.Image,
    ) -> StrategyResult:
        """
        Process a sample using ColPali-only approach.

        Steps:
        1. Generate ColPali embeddings (for timing comparison)
        2. Run OCR to get page content
        3. Return full page as context (no region filtering)
        4. Send to LLM for answer generation
        """
        result = StrategyResult()
        total_timer = Timer()

        try:
            with total_timer:
                # Step 1: Generate ColPali embeddings (for timing measurement)
                self._generate_embeddings(sample.query, image, result.timing)

                # Step 2: Run OCR to get page content
                ocr_result = self._run_ocr(image, result.timing)
                if not ocr_result:
                    result.error = "OCR returned no results"
                    return result

                # Step 3: Extract full page content (no region filtering)
                result.ocr_content = ocr_result.get("text", "") or ocr_result.get("markdown", "")

                # Create a single "full page" region (no sub-page localization)
                result.regions = [{
                    "content": result.ocr_content,
                    "bbox": [0, 0, image.width, image.height],  # Full page bbox
                    "label": "full_page",
                }]

                # Step 4: Generate answer with LLM using full page context
                context = result.ocr_content
                llm_response, llm_tokens = self._call_llm(
                    sample.query, context, result.timing
                )
                result.llm_response = llm_response
                result.tokens = llm_tokens

            result.timing.total_time_ms = total_timer.elapsed_ms

        except Exception as e:
            logger.error(f"Error in ColPali-only strategy: {e}", exc_info=True)
            result.error = str(e)

        return result

    def _generate_embeddings(
        self,
        query: str,
        image: Image.Image,
        timing: TimingMetrics,
    ) -> None:
        """Generate ColPali embeddings for query and image."""
        embedding_timer = Timer()

        try:
            with embedding_timer:
                # Generate query embeddings
                response = self._session.post(
                    f"{self.config.colpali_url}/embed/queries",
                    json={"queries": [query]},
                    timeout=60,
                )
                response.raise_for_status()

                # Generate image embeddings
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                files = [("files", ("image.png", img_buffer, "image/png"))]
                response = self._session.post(
                    f"{self.config.colpali_url}/embed/images",
                    files=files,
                    timeout=120,
                )
                response.raise_for_status()

        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")

        finally:
            timing.embedding_time_ms = embedding_timer.elapsed_ms

    def _run_ocr(
        self,
        image: Image.Image,
        timing: TimingMetrics,
    ) -> Optional[Dict[str, Any]]:
        """Run OCR on the image."""
        ocr_timer = Timer()

        try:
            with ocr_timer:
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                files = {"file": ("image.png", img_buffer, "image/png")}
                data = {
                    "mode": self.config.ocr_mode,
                    "task": self.config.ocr_task,
                    "include_grounding": str(self.config.ocr_include_grounding).lower(),
                    "include_images": "false",
                }

                response = self._session.post(
                    f"{self.config.ocr_url}/ocr/process-page",
                    files=files,
                    data=data,
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

        finally:
            timing.ocr_time_ms = ocr_timer.elapsed_ms

    def _call_llm(
        self,
        query: str,
        context: str,
        timing: TimingMetrics,
    ) -> tuple[str, TokenMetrics]:
        """Call LLM to generate answer."""
        llm_timer = Timer()
        tokens = TokenMetrics()

        try:
            with llm_timer:
                prompt = self._build_llm_prompt(query, context)
                tokens.input_tokens = self._count_tokens(prompt)

                response = self._session.post(
                    f"{self.config.llm_url}/v1/chat/completions",
                    json={
                        "model": self.config.llm_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.config.llm_temperature,
                        "max_tokens": self.config.llm_max_tokens,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()

                answer = result["choices"][0]["message"]["content"]

                usage = result.get("usage", {})
                tokens.input_tokens = usage.get("prompt_tokens", tokens.input_tokens)
                tokens.output_tokens = usage.get("completion_tokens", self._count_tokens(answer))
                tokens.total_tokens = tokens.input_tokens + tokens.output_tokens

                return answer, tokens

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Error: {e}", tokens

        finally:
            timing.llm_time_ms = llm_timer.elapsed_ms
