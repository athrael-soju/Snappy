# Refactoring: Move PP-DocLayoutV3 to Backend

## Overview

**Current Architecture (3 containers):**
- `paddle-ocr-vllm` — vLLM server for text generation (GPU)
- `paddle-ocr` — Pipeline service with PP-DocLayoutV3 (CPU)
- `backend` — Calls paddle-ocr via HTTP

**Target Architecture (2 containers):**
- `paddle-ocr-vllm` — vLLM server for text generation (GPU)
- `backend` — Runs PP-DocLayoutV3 locally, calls vLLM for text generation

---

## 1. Update Backend Dockerfile

**File:** `backend/Dockerfile`

Add system dependencies for PaddlePaddle (already done):

```dockerfile
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    curl \
    ffmpeg \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

---

## 2. Update Backend Requirements

**File:** `backend/requirements.txt`

Add (already done):

```
# PaddleOCR with PP-DocLayoutV3 for layout detection
paddlepaddle==3.2.1
paddleocr[doc-parser]>=3.4.0
safetensors
```

---

## 3. Rewrite OCR Client

**File:** `backend/clients/ocr/client.py`

Replace HTTP calls with direct SDK usage:

```python
"""Main OCR service using PaddleOCR SDK with vLLM backend."""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import config
from PIL import Image

if TYPE_CHECKING:
    from clients.local_storage import LocalStorageClient

logger = logging.getLogger(__name__)

# Global pipeline instance (initialized lazily)
_pipeline = None


def _get_pipeline():
    """Get or create PaddleOCRVL pipeline instance."""
    global _pipeline
    if _pipeline is None:
        from paddleocr import PaddleOCRVL

        vllm_url = getattr(config, "PADDLE_OCR_VLLM_URL", "http://paddle-ocr-vllm:8080/v1")
        logger.info(f"Initializing PaddleOCRVL with vLLM backend at {vllm_url}")

        _pipeline = PaddleOCRVL(
            vl_rec_backend="vllm-server",
            vl_rec_server_url=vllm_url,
            use_layout_detection=True,
            layout_detection_model_name="PP-DocLayoutV3",
        )
        logger.info("PaddleOCRVL pipeline initialized successfully")

    return _pipeline


class OcrClient:
    """Main service class for OCR operations using PaddleOCR SDK."""

    def __init__(
        self,
        storage_service: Optional["LocalStorageClient"] = None,
        enabled: Optional[bool] = None,
        include_images: Optional[bool] = None,
    ):
        """Initialize OCR service.

        Args:
            storage_service: Storage service for image storage
            enabled: Enable/disable OCR service
            include_images: Default image extraction
        """
        if storage_service is None:
            raise ValueError("Storage service is required for OcrClient")

        self.enabled = enabled if enabled is not None else bool(config.PADDLE_OCR_ENABLED)
        self.storage_service = storage_service
        self.default_include_images = (
            include_images
            if include_images is not None
            else getattr(config, "PADDLE_OCR_INCLUDE_IMAGES", True)
        )

        # Initialize subcomponents
        from domain.pipeline.image_processor import ImageProcessor
        from .processor import OcrProcessor

        self.image_processor = ImageProcessor(
            default_format=config.IMAGE_FORMAT,
            default_quality=config.IMAGE_QUALITY,
        )

        self.processor = OcrProcessor(
            ocr_service=self,
            image_processor=self.image_processor,
        )

        from domain.ocr_persistence import OcrStorageHandler

        self.storage = OcrStorageHandler(
            storage_service=self.storage_service,
            processor=self.processor,
        )

    def is_enabled(self) -> bool:
        """Return True when runtime configuration permits OCR usage."""
        return self.enabled

    def run_ocr(
        self,
        image_path: Path,
        *,
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR on an image file."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        image = Image.open(image_path).convert("RGB")
        return self._run_pipeline(image, include_images=include_images)

    def run_ocr_bytes(
        self,
        image_bytes: bytes,
        *,
        filename: str = "page.png",
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR given raw image bytes."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self._run_pipeline(image, include_images=include_images, image_bytes=image_bytes)

    def run_ocr_image(
        self,
        image: Image.Image,
        *,
        include_images: Optional[bool] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute OCR directly from a PIL image instance."""
        if not self.enabled:
            raise RuntimeError("PaddleOCR service is disabled by configuration.")

        return self._run_pipeline(image.convert("RGB"), include_images=include_images)

    def _run_pipeline(
        self,
        image: Image.Image,
        *,
        include_images: Optional[bool] = None,
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Run the PaddleOCR pipeline and parse results."""
        pipeline = _get_pipeline()
        results = pipeline.predict(image)

        if not results:
            return {
                "text": "",
                "markdown": "",
                "raw": "",
                "bounding_boxes": [],
                "regions": [],
                "crops": [],
            }

        result = results[0]
        return self._parse_results(
            result,
            image=image,
            include_images=include_images if include_images is not None else self.default_include_images,
            image_bytes=image_bytes,
        )

    def _parse_results(
        self,
        result,
        *,
        image: Image.Image,
        include_images: bool,
        image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Parse PaddleOCR pipeline results into standard format."""
        bounding_boxes = []
        figure_boxes = []

        # Extract layout detection results
        result_json = getattr(result, "json", {}) or {}
        if callable(result_json):
            result_json = result_json()

        layout_det_res = result_json.get("layout_det_res", {})

        for box in layout_det_res.get("boxes", []):
            coord = box.get("coordinate", [])
            if hasattr(coord, "tolist"):
                coord = coord.tolist()

            if len(coord) >= 4:
                bbox = {
                    "x1": int(coord[0]),
                    "y1": int(coord[1]),
                    "x2": int(coord[2]),
                    "y2": int(coord[3]),
                    "label": box.get("label", "text"),
                    "confidence": float(box.get("score", 1.0)),
                }
                bounding_boxes.append(bbox)

                if bbox["label"] in ("image", "figure", "chart", "diagram", "photo"):
                    figure_boxes.append(bbox)

        # Extract parsing results (regions with content)
        regions = []
        for block in result_json.get("parsing_res_list", []):
            bbox = block.get("block_bbox", [])
            if hasattr(bbox, "tolist"):
                bbox = bbox.tolist()

            region = {
                "label": block.get("block_label", "text"),
                "content": block.get("block_content", ""),
                "bbox": bbox,
            }
            if region["label"] in ("image", "figure", "chart", "diagram", "photo"):
                region["image_index"] = len([r for r in regions if r.get("image_index") is not None])
            regions.append(region)

        # Get markdown
        markdown = ""
        if hasattr(result, "markdown"):
            md = result.markdown
            if isinstance(md, dict):
                markdown = "\n\n".join(md.get("markdown_texts", []))
            else:
                markdown = str(md) if md else ""

        # Build text from regions
        text = "\n".join(r["content"] for r in regions if r.get("content"))

        # Extract figure crops if requested
        crops = []
        if include_images and figure_boxes:
            if image_bytes is None:
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()
            crops = self._extract_figure_crops(image_bytes, figure_boxes)

        return {
            "text": text,
            "markdown": markdown.strip() if markdown else text,
            "raw": str(result_json),
            "bounding_boxes": bounding_boxes,
            "regions": regions,
            "crops": crops,
        }

    def _extract_figure_crops(
        self,
        image_bytes: bytes,
        figure_boxes: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract figure regions from the original image as base64 crops."""
        crops = []

        try:
            original_image = Image.open(io.BytesIO(image_bytes))
            img_width, img_height = original_image.size

            for bbox in figure_boxes:
                try:
                    x1 = max(0, min(bbox["x1"], img_width))
                    y1 = max(0, min(bbox["y1"], img_height))
                    x2 = max(0, min(bbox["x2"], img_width))
                    y2 = max(0, min(bbox["y2"], img_height))

                    if (x2 - x1) < 10 or (y2 - y1) < 10:
                        continue

                    cropped = original_image.crop((x1, y1, x2, y2))
                    buffer = io.BytesIO()
                    cropped.save(buffer, format="PNG")
                    crop_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    crops.append(crop_b64)

                except Exception as crop_exc:
                    logger.warning(f"Failed to crop figure region: {crop_exc}")

        except Exception as exc:
            logger.warning(f"Failed to extract figure crops: {exc}")

        return crops

    def health_check(self) -> bool:
        """Check if OCR service is healthy."""
        if not self.enabled:
            return False
        try:
            _get_pipeline()
            return True
        except Exception as exc:
            logger.warning("PaddleOCR health check failed: %s", exc)
            return False

    def close(self):
        """No-op for SDK-based client."""
        pass
```

---

## 4. Update Config

**File:** `backend/config/application.py`

Change:

```python
# From:
PADDLE_OCR_URL = os.getenv("PADDLE_OCR_URL", "http://paddle-ocr:8200")

# To:
PADDLE_OCR_VLLM_URL = os.getenv("PADDLE_OCR_VLLM_URL", "http://paddle-ocr-vllm:8080/v1")
```

---

## 5. Update docker-compose.yml

**File:** `docker-compose.yml`

Remove the `paddle-ocr` service block entirely (lines 80-102).

Update backend to depend on paddle-ocr-vllm:

```yaml
backend:
  container_name: backend
  build:
    context: ./backend
    dockerfile: Dockerfile
  image: backend:latest
  ports:
    - "8000:8000"
  env_file:
    - ./backend/.env
  environment:
    - COLPALI_URL=http://colpali:7000
    - PADDLE_OCR_ENABLED=${PADDLE_OCR_ENABLED:-true}
    - PADDLE_OCR_VLLM_URL=http://paddle-ocr-vllm:8080/v1
    - QDRANT_URL=http://qdrant:6333
    - LOCAL_STORAGE_PATH=/app/storage
    - LOCAL_STORAGE_PUBLIC_URL=${LOCAL_STORAGE_PUBLIC_URL:-http://localhost:8000/files}
  volumes:
    - ./backend:/app
    - backend_cache:/root/.cache
    - snappy_storage:/app/storage
  networks:
    - snappy-network
  depends_on:
    qdrant:
      condition: service_healthy
    paddle-ocr-vllm:
      condition: service_healthy
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 6. Delete paddle-ocr Directory

```bash
rm -rf paddle-ocr/
```

---

## 7. Update .env Files

**File:** `backend/.env.example`

```bash
# PaddleOCR Configuration
PADDLE_OCR_ENABLED=true
PADDLE_OCR_VLLM_URL=http://localhost:8080/v1
PADDLE_OCR_INCLUDE_IMAGES=true
```

---

## Summary of Changes

| File | Action |
|------|--------|
| `backend/Dockerfile` | Add system deps (done) |
| `backend/requirements.txt` | Add paddlepaddle, paddleocr (done) |
| `backend/clients/ocr/client.py` | Rewrite to use SDK directly |
| `backend/config/application.py` | Change `PADDLE_OCR_URL` to `PADDLE_OCR_VLLM_URL` |
| `backend/.env.example` | Update env var names |
| `docker-compose.yml` | Remove paddle-ocr service, update backend deps |
| `paddle-ocr/` | Delete directory |

---

## Architecture Diagram

```
                    +-------------------+
                    |  paddle-ocr-vllm  |
                    |  (GPU Container)  |
                    |                   |
                    | PaddleOCR-VL-1.5  |
                    | via vLLM server   |
                    +--------^----------+
                             |
                             | HTTP /v1/chat/completions
                             |
+-------------------+        |
|     backend       |--------+
|  (CPU Container)  |
|                   |
| PP-DocLayoutV3    |  <-- Runs locally in backend
| (layout detection)|
|                   |
| PaddleOCR SDK     |
+-------------------+
```

The backend runs PP-DocLayoutV3 for layout detection locally (CPU), and calls the vLLM server for text generation (GPU).
