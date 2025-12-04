"""
OCR-only baseline strategy.

This strategy:
1. Runs OCR on the document image to extract all regions
2. Returns ALL regions without any filtering
3. Sends all OCR content to the LLM for answer generation

This represents a traditional OCR-based approach without any
visual grounding or relevance filtering.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from ..config import BenchmarkConfig
from ..dataset import BenchmarkSample
from ..metrics import Timer, TimingMetrics, TokenMetrics
from .base import BaseStrategy, StrategyResult

logger = logging.getLogger(__name__)


class OCROnlyStrategy(BaseStrategy):
    """
    OCR-only baseline: Extract all text regions and send to LLM.

    This approach provides maximum recall but may include irrelevant
    content, leading to:
    - Higher token usage
    - Potentially lower precision
    - No spatial grounding of answers
    """

    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return "ocr_only"

    def process(
        self,
        sample: BenchmarkSample,
        image: Image.Image,
    ) -> StrategyResult:
        """
        Process a sample using OCR-only approach.

        Steps:
        1. Send image to OCR service
        2. Extract all regions with bounding boxes
        3. Build context from all OCR content
        4. Send to LLM for answer generation
        """
        result = StrategyResult()
        total_timer = Timer()

        try:
            with total_timer:
                # Step 1: Run OCR
                ocr_result = self._run_ocr(image, result.timing)
                if not ocr_result:
                    result.error = "OCR returned no results"
                    return result

                # Step 2: Extract regions
                result.regions = self._extract_regions(ocr_result)
                result.ocr_content = ocr_result.get("text", "") or ocr_result.get("markdown", "")

                # Step 3: Build context from ALL regions
                context = self._format_regions_as_context(result.regions)
                if not context:
                    context = result.ocr_content

                # Step 4: Generate answer with LLM
                llm_response, llm_tokens = self._call_llm(
                    sample.query, context, result.timing
                )
                result.llm_response = llm_response
                result.tokens = llm_tokens

            result.timing.total_time_ms = total_timer.elapsed_ms

        except Exception as e:
            logger.error(f"Error in OCR-only strategy: {e}", exc_info=True)
            result.error = str(e)

        return result

    def _run_ocr(
        self,
        image: Image.Image,
        timing: TimingMetrics,
    ) -> Optional[Dict[str, Any]]:
        """Run OCR on the image."""
        import io

        ocr_timer = Timer()

        try:
            with ocr_timer:
                # Prepare image for upload
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                # Call OCR service
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

    def _extract_regions(
        self,
        ocr_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract regions with bounding boxes from OCR result."""
        regions = []

        # Get bounding boxes from OCR result
        bounding_boxes = ocr_result.get("bounding_boxes", [])

        # The OCR result may have text associated with regions
        # or it might just be plain text extraction
        if bounding_boxes:
            for bbox in bounding_boxes:
                region = {
                    "content": bbox.get("label", ""),
                    "bbox": [bbox.get("x1", 0), bbox.get("y1", 0), bbox.get("x2", 0), bbox.get("y2", 0)],
                    "label": "text",
                }
                regions.append(region)
        else:
            # If no bounding boxes, create a single region with all text
            text = ocr_result.get("text", "") or ocr_result.get("markdown", "")
            if text:
                regions.append({
                    "content": text,
                    "bbox": [],  # No spatial information
                    "label": "full_page",
                })

        return regions

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

                # Estimate input tokens
                tokens.input_tokens = self._count_tokens(prompt)

                # Call LLM service
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

                # Extract response and token counts
                answer = result["choices"][0]["message"]["content"]

                # Get actual token counts if available
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
