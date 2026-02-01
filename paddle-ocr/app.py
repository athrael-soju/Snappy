"""
PaddleOCR Pipeline Service

Runs full PaddleOCR-VL with PP-DocLayoutV3 for structured output with labels.
Returns layout_det_res with bounding boxes and labels (image, text, table, etc.)
"""

import base64
import io
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PaddleOCR Pipeline Service", version="1.0.0")

# Global pipeline instance
_pipeline = None


class InferRequest(BaseModel):
    """Request for /v1/infer endpoint."""
    input: List[Dict[str, Any]]
    task: Optional[str] = "OCR"


class InferResponse(BaseModel):
    """Response from /v1/infer endpoint."""
    layout_det_res: Dict[str, Any]
    parsing_res_list: List[Dict[str, Any]]
    markdown: str
    text: str


def get_pipeline():
    """Get or create PaddleOCRVL pipeline instance."""
    global _pipeline
    if _pipeline is None:
        from paddleocr import PaddleOCRVL

        # Get vLLM server URL from environment
        vllm_url = os.environ.get("VLLM_SERVER_URL", "http://paddle-ocr-vllm:8080/v1")

        logger.info(f"Initializing PaddleOCRVL with vLLM backend at {vllm_url}")

        _pipeline = PaddleOCRVL(
            vl_rec_backend="vllm-server",
            vl_rec_server_url=vllm_url,
            use_layout_detection=True,
            layout_detection_model_name="PP-DocLayoutV3",
        )
        logger.info("PaddleOCRVL pipeline initialized successfully")

    return _pipeline


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup."""
    try:
        get_pipeline()
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        pipeline = get_pipeline()
        return {"status": "healthy", "pipeline_ready": pipeline is not None}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/v1/infer")
async def infer(request: InferRequest):
    """
    Run OCR inference with layout detection.

    Returns structured output with labels and bounding boxes.
    """
    try:
        pipeline = get_pipeline()

        # Extract image from request
        if not request.input:
            raise HTTPException(status_code=400, detail="No input provided")

        image_input = request.input[0]
        image_url = image_input.get("url", "")

        # Decode base64 image
        if image_url.startswith("data:image"):
            # Extract base64 data
            _, b64_data = image_url.split(",", 1)
            image_bytes = base64.b64decode(b64_data)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        else:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Run pipeline
        logger.info(f"Running OCR with task: {request.task}")
        results = pipeline.predict(image)

        # Process results
        if not results:
            return {
                "layout_det_res": {"boxes": []},
                "parsing_res_list": [],
                "markdown": "",
                "text": "",
            }

        result = results[0]

        # Extract layout detection results
        layout_det_res = {"boxes": []}
        if hasattr(result, "json") and "layout_det_res" in result.json:
            layout_det_res = result.json["layout_det_res"]
        elif hasattr(result, "_result") and "layout_det_res" in result._result:
            layout_det_res = result._result["layout_det_res"]

        # Convert numpy arrays to lists for JSON serialization
        boxes = []
        for box in layout_det_res.get("boxes", []):
            coord = box.get("coordinate", [])
            if hasattr(coord, "tolist"):
                coord = coord.tolist()
            boxes.append({
                "cls_id": int(box.get("cls_id", 0)),
                "label": box.get("label", "text"),
                "score": float(box.get("score", 1.0)),
                "coordinate": coord,
            })

        # Extract parsing results
        parsing_res_list = []
        if hasattr(result, "json") and "parsing_res_list" in result.json:
            for block in result.json["parsing_res_list"]:
                bbox = block.get("block_bbox", [])
                if hasattr(bbox, "tolist"):
                    bbox = bbox.tolist()
                parsing_res_list.append({
                    "block_id": block.get("block_id", 0),
                    "block_label": block.get("block_label", "text"),
                    "block_bbox": bbox,
                    "block_content": block.get("block_content", ""),
                    "block_order": block.get("block_order"),
                })

        # Get markdown and text
        markdown = ""
        if hasattr(result, "markdown"):
            md = result.markdown
            if isinstance(md, dict):
                markdown = "\n\n".join(md.get("markdown_texts", []))
            else:
                markdown = str(md)

        text = ""
        for block in parsing_res_list:
            if block.get("block_content"):
                text += block["block_content"] + "\n"

        return {
            "layout_det_res": {"boxes": boxes},
            "parsing_res_list": parsing_res_list,
            "markdown": markdown.strip(),
            "text": text.strip(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr")
async def ocr_multipart(
    image: UploadFile = File(...),
    task: str = Form("OCR"),
):
    """
    Alternative OCR endpoint accepting multipart form data.

    For backwards compatibility with existing clients.
    """
    try:
        # Read image
        image_bytes = await image.read()
        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        # Determine content type
        content_type = image.content_type or "image/png"
        image_url = f"data:{content_type};base64,{b64_data}"

        # Create request and call infer
        request = InferRequest(
            input=[{"type": "image_url", "url": image_url}],
            task=task,
        )
        return await infer(request)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
