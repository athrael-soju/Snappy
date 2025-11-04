"""
OCR processing service for handling OCR requests.
"""

from io import BytesIO
from typing import Any, Dict, List

import fitz  # PyMuPDF
from app.core.config import settings
from app.services.model_service import model_service
from app.utils.image_processing import (
    clean_output,
    draw_bounding_boxes,
    embed_images,
    extract_grounding_references,
    image_to_base64,
)
from PIL import Image


class OCRProcessor:
    """Service for processing OCR requests."""

    def __init__(self):
        """Initialize OCR processor."""
        self.model_service = model_service

    def _build_prompt(self, task: str, custom_prompt: str = None) -> tuple[str, bool]:
        """
        Build prompt for the given task.

        Args:
            task: Task type
            custom_prompt: Custom prompt text

        Returns:
            Tuple of (prompt, has_grounding)
        """
        if task == "custom":
            if not custom_prompt:
                raise ValueError("Custom task requires a custom prompt")
            prompt = f"<image>\n{custom_prompt.strip()}"
            has_grounding = "<|grounding|>" in custom_prompt
        elif task == "locate":
            if not custom_prompt:
                raise ValueError("Locate task requires a custom prompt")
            prompt = (
                f"<image>\nLocate <|ref|>{custom_prompt.strip()}<|/ref|> in the image."
            )
            has_grounding = True
        else:
            task_config = settings.TASK_PROMPTS[task]
            prompt = task_config["prompt"]
            has_grounding = task_config["has_grounding"]

        return prompt, has_grounding

    def _extract_bounding_boxes(
        self,
        image: Image.Image,
        result: str,
        has_grounding: bool,
        include_grounding: bool,
        include_images: bool,
    ) -> tuple[Image.Image | None, List[Image.Image], List[Dict[str, Any]]]:
        """
        Extract bounding boxes and crops from OCR result.

        Returns:
            Tuple of (annotated_image, crops, bboxes)
        """
        img_out = None
        crops = []
        bboxes = []

        if has_grounding and include_grounding and "<|ref|>" in result:
            refs = extract_grounding_references(result)
            if refs:
                img_out, crops = draw_bounding_boxes(image, refs, include_images)

                # Convert bounding boxes to structured format
                img_w, img_h = image.size
                for ref in refs:
                    label = ref[1]
                    coords = eval(ref[2])
                    for box in coords:
                        bboxes.append(
                            {
                                "x1": int(box[0] / 999 * img_w),
                                "y1": int(box[1] / 999 * img_h),
                                "x2": int(box[2] / 999 * img_w),
                                "y2": int(box[3] / 999 * img_h),
                                "label": label,
                            }
                        )

        return img_out, crops, bboxes

    def process_image(
        self,
        image: Image.Image,
        mode: str,
        task: str,
        custom_prompt: str = None,
        include_grounding: bool = True,
        include_images: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a single image with DeepSeek OCR.

        Args:
            image: PIL Image to process
            mode: Processing mode (Gundam, Tiny, Small, Base, Large)
            task: Task type (markdown, plain_ocr, locate, describe, custom)
            custom_prompt: Custom prompt for custom/locate tasks
            include_grounding: Whether to extract bounding boxes
            include_images: Whether to extract and embed images

        Returns:
            Dictionary with OCR results
        """
        if image is None:
            raise ValueError("No image provided")

        # Build prompt
        prompt, has_grounding = self._build_prompt(task, custom_prompt)

        # Get model configuration
        config = settings.MODEL_CONFIGS[mode]

        # Run inference
        result = self.model_service.infer(
            image=image,
            prompt=prompt,
            base_size=config["base_size"],
            image_size=config["image_size"],
            crop_mode=config["crop_mode"],
        )

        if not result:
            raise ValueError("No text extracted from image")

        # Clean output
        cleaned = clean_output(result, False, False)
        markdown = clean_output(result, include_images, True)

        # Extract bounding boxes and crops
        img_out, crops, bboxes = self._extract_bounding_boxes(
            image, result, has_grounding, include_grounding, include_images
        )

        # Embed images in markdown
        if include_images:
            markdown = embed_images(markdown, crops)

        return {
            "text": cleaned,
            "markdown": markdown,
            "raw": result,
            "bounding_boxes": bboxes,
            "crops": [image_to_base64(crop) for crop in crops],
            "annotated_image": image_to_base64(img_out) if img_out else None,
        }

    def process_pdf(
        self,
        pdf_path: str,
        mode: str,
        task: str,
        custom_prompt: str = None,
        include_grounding: bool = True,
        include_images: bool = True,
    ) -> Dict[str, Any]:
        """
        Process all pages of a PDF document.

        Args:
            pdf_path: Path to PDF file
            mode: Processing mode
            task: Task type
            custom_prompt: Custom prompt for custom/locate tasks
            include_grounding: Whether to extract bounding boxes
            include_images: Whether to extract and embed images

        Returns:
            Dictionary with combined OCR results from all pages
        """
        doc = fitz.open(pdf_path)
        texts, markdowns, raws = [], [], []
        all_crops = []
        all_bboxes = []

        try:
            for i in range(len(doc)):
                page = doc.load_page(i)
                # Render at 300 DPI
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False
                )
                img = Image.open(BytesIO(pix.tobytes("png")))

                result = self.process_image(
                    img, mode, task, custom_prompt, include_grounding, include_images
                )

                if result["text"]:
                    texts.append(f"### Page {i + 1}\n\n{result['text']}")
                    markdowns.append(f"### Page {i + 1}\n\n{result['markdown']}")
                    raws.append(f"=== Page {i + 1} ===\n{result['raw']}")
                    all_crops.extend(result["crops"])
                    all_bboxes.extend(result["bounding_boxes"])

        finally:
            doc.close()

        return {
            "text": "\n\n---\n\n".join(texts) if texts else "No text in PDF",
            "markdown": (
                "\n\n---\n\n".join(markdowns) if markdowns else "No text in PDF"
            ),
            "raw": "\n\n".join(raws),
            "bounding_boxes": all_bboxes,
            "crops": all_crops,
            "annotated_image": None,  # Not applicable for multi-page PDFs
        }


# Global OCR processor instance
ocr_processor = OCRProcessor()
