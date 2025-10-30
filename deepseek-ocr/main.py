import ast
import logging
import os
import re
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel, Field
from transformers import AutoModel, AutoTokenizer


def _configure_logging() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level)
    return logging.getLogger("deepseek_ocr")


logger = _configure_logging()


def _parse_origins(raw: Optional[str]) -> List[str]:
    if not raw:
        return ["*"]
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or ["*"]


def _parse_bool(value: str, default: bool = False) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class ServiceSettings:
    """Runtime configuration loaded from environment variables."""

    model_name: str = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-OCR")
    hf_home: str = os.getenv("HF_HOME", "/models")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8200"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    default_base_size: int = int(os.getenv("BASE_SIZE", "1024"))
    default_image_size: int = int(os.getenv("IMAGE_SIZE", "640"))
    default_crop_mode: bool = _parse_bool(os.getenv("CROP_MODE", "true"), True)
    allowed_origins: List[str] = field(
        default_factory=lambda: _parse_origins(os.getenv("ALLOWED_ORIGINS", "*"))
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = ServiceSettings()


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is not None and hasattr(mps_backend, "is_available"):
        if mps_backend.is_available():  # type: ignore[attr-defined]
            return "mps"
    xpu_backend = getattr(torch.backends, "xpu", None)
    if xpu_backend is not None and hasattr(xpu_backend, "is_available"):
        if xpu_backend.is_available():  # type: ignore[attr-defined]
            return "xpu"
    return "cpu"


class OCRRuntime:
    """Encapsulates model and tokenizer lifecycle."""

    def __init__(self, svc_settings: ServiceSettings) -> None:
        self.settings = svc_settings
        self.device = _select_device()
        if self.device == "cpu":
            logger.warning(
                "DeepSeek OCR is running on CPU. Inference will be significantly slower."
            )
        self.dtype = torch.bfloat16 if self.device != "cpu" else torch.float32
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def load(self) -> None:
        Path(self.settings.hf_home).mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = self.settings.hf_home
        os.environ.pop("TRANSFORMERS_CACHE", None)

        logger.info(
            "Loading DeepSeek OCR model '%s' on device %s (dtype=%s)",
            self.settings.model_name,
            self.device,
            self.dtype,
        )

        tokenizer = AutoTokenizer.from_pretrained(
            self.settings.model_name,
            trust_remote_code=True,
        )

        model = (
            AutoModel.from_pretrained(
                self.settings.model_name,
                trust_remote_code=True,
                use_safetensors=True,
                attn_implementation="eager",
                torch_dtype=self.dtype,
            )
            .eval()
            .to(self.device)
        )

        self._ensure_pad_tokens(model, tokenizer)

        self._model = model
        self._tokenizer = tokenizer
        logger.info("DeepSeek OCR model loaded successfully.")

    def unload(self) -> None:
        logger.info("Unloading DeepSeek OCR model.")
        self._model = None
        self._tokenizer = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _ensure_pad_tokens(model: Any, tokenizer: Any) -> None:
        """Ensure compatible pad token configuration if possible."""
        try:
            if (
                getattr(tokenizer, "pad_token_id", None) is None
                and getattr(tokenizer, "eos_token_id", None) is not None
            ):
                tokenizer.pad_token = tokenizer.eos_token
            if (
                getattr(model.config, "pad_token_id", None) is None
                and getattr(tokenizer, "pad_token_id", None) is not None
            ):
                model.config.pad_token_id = tokenizer.pad_token_id
        except Exception:  # pragma: no cover - best effort only
            logger.debug("Pad token configuration skipped.", exc_info=True)

    def infer(
        self,
        *,
        prompt: str,
        image_path: str,
        base_size: int,
        image_size: int,
        crop_mode: bool,
        test_compress: bool,
        output_dir: str,
    ) -> Any:
        if not self.is_ready:
            raise RuntimeError("DeepSeek OCR model is not loaded.")

        model = cast(Any, self._model)
        tokenizer = cast(Any, self._tokenizer)

        return model.infer(
            tokenizer,
            prompt=prompt,
            image_file=image_path,
            output_path=output_dir,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            save_results=False,
            test_compress=test_compress,
            eval_mode=True,
        )


runtime = OCRRuntime(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load model on startup, release on shutdown."""
    try:
        runtime.load()
        app.state.runtime = runtime
        yield
    finally:
        runtime.unload()


app = FastAPI(
    title="DeepSeek OCR API",
    description="High-fidelity OCR powered by DeepSeek-OCR.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=(settings.allowed_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_prompt(
    *,
    mode: str,
    user_prompt: str,
    grounding: bool,
    find_term: Optional[str],
    schema: Optional[str],
    include_caption: bool,
) -> str:
    """Build prompt text for the selected OCR mode."""
    instructions: List[str] = ["<image>"]
    modes_requiring_grounding = {"find_ref", "layout_map", "pii_redact"}
    if grounding or mode in modes_requiring_grounding:
        instructions.append("<|grounding|>")

    prompt_text = ""
    if mode == "plain_ocr":
        prompt_text = "Transcribe the document faithfully."
    elif mode == "markdown":
        prompt_text = "Convert the document to Markdown."
    elif mode == "tables_csv":
        prompt_text = (
            "Extract every table and output comma separated values. "
            "Separate multiple tables with a line containing '---'."
        )
    elif mode == "tables_md":
        prompt_text = "Extract every table as GitHub-flavored Markdown tables."
    elif mode == "kv_json":
        schema_text = schema.strip() if schema else "{}"
        prompt_text = (
            "Extract key fields and return strict JSON only. "
            f"Use this schema and fill the values: {schema_text}"
        )
    elif mode == "figure_chart":
        prompt_text = (
            "Parse the figure. First extract numeric series as a two-column table (x,y). "
            "Then summarise the chart in two sentences. "
            "Output the table, a line containing '---', then the summary."
        )
    elif mode == "find_ref":
        key = (find_term or "").strip() or "Total"
        prompt_text = f"Locate <|ref|>{key}<|/ref|> within the document."
    elif mode == "layout_map":
        prompt_text = (
            "Return a JSON array of blocks with fields "
            '{"type":["title","paragraph","table","figure"],"box":[x1,y1,x2,y2]}. '
            "Do not include any text content."
        )
    elif mode == "pii_redact":
        prompt_text = (
            "Find all occurrences of emails, phone numbers, postal addresses, and IBANs. "
            'Return a JSON array of objects {"label","text","box":[x1,y1,x2,y2]}.'
        )
    elif mode == "multilingual":
        prompt_text = "Transcribe the document and preserve the original language."
    elif mode == "describe":
        prompt_text = "Describe the image focusing on key visual elements."
    elif mode == "freeform":
        prompt_text = user_prompt.strip() if user_prompt else "Transcribe the document."
    else:
        prompt_text = "Transcribe the document."

    if include_caption and mode != "describe":
        prompt_text = f"{prompt_text}\nThen add a concise description of the image."

    instructions.append(prompt_text)
    return "\n".join(instructions)


DET_BLOCK = re.compile(
    r"<\|ref\|>(?P<label>.*?)<\|/ref\|>\s*<\|det\|>\s*(?P<coords>\[.*?\])\s*<\|/det\|>",
    re.DOTALL,
)


def parse_detections(
    text: str, image_width: int, image_height: int
) -> List[Dict[str, Any]]:
    """Parse detection blocks from the model output into bounding boxes."""
    boxes: List[Dict[str, Any]] = []

    for match in DET_BLOCK.finditer(text):
        label = match.group("label").strip()
        coords_str = match.group("coords")
        try:
            parsed = ast.literal_eval(coords_str)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.debug("Failed to parse detection coordinates: %s", exc)
            continue

        if (
            isinstance(parsed, list)
            and len(parsed) == 4
            and all(isinstance(n, (int, float)) for n in parsed)
        ):
            coord_list: List[List[float]] = [parsed]  # single flattened box
        elif isinstance(parsed, list):
            coord_list = [
                box
                for box in parsed
                if isinstance(box, (list, tuple)) and len(box) >= 4
            ]
        else:
            logger.debug("Unsupported detection structure for label '%s'", label)
            continue

        for coords in coord_list:
            try:
                x1 = int(float(coords[0]) / 999 * image_width)
                y1 = int(float(coords[1]) / 999 * image_height)
                x2 = int(float(coords[2]) / 999 * image_width)
                y2 = int(float(coords[3]) / 999 * image_height)
            except Exception as exc:  # pragma: no cover - guard against bad data
                logger.debug("Failed to normalise detection coordinates: %s", exc)
                continue

            boxes.append({"label": label, "box": [x1, y1, x2, y2]})

    return boxes


def clean_grounding_text(text: str) -> str:
    """Remove grounding tags while preserving labels."""
    cleaned = re.sub(
        r"<\|ref\|>(.*?)<\|/ref\|>\s*<\|det\|>\s*\[.*?\]\s*<\|/det\|>",
        r"\1",
        text,
        flags=re.DOTALL,
    )
    cleaned = cleaned.replace("<|grounding|>", "")
    return cleaned.strip()


class BoundingBox(BaseModel):
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)


class OCRMetadata(BaseModel):
    mode: str
    grounding: bool
    base_size: int
    image_size: int
    crop_mode: bool
    include_caption: bool
    elapsed_ms: int


class OCRResult(BaseModel):
    success: bool = True
    text: str
    raw_text: str
    boxes: List[BoundingBox]
    image_dims: Dict[str, Optional[int]]
    metadata: OCRMetadata


def _read_runtime() -> OCRRuntime:
    runtime_instance = getattr(app.state, "runtime", None)
    if not isinstance(runtime_instance, OCRRuntime):
        raise HTTPException(status_code=503, detail="OCR runtime is not available.")
    if not runtime_instance.is_ready:
        raise HTTPException(status_code=503, detail="OCR model not loaded yet.")
    return runtime_instance


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "DeepSeek OCR API is running.", "docs": "/docs"}


@app.get("/health")
async def health() -> Dict[str, Any]:
    runtime_instance = getattr(app.state, "runtime", None)
    is_ready = (
        bool(runtime_instance.is_ready)
        if isinstance(runtime_instance, OCRRuntime)
        else False
    )
    return {
        "status": "ok" if is_ready else "initialising",
        "model_loaded": is_ready,
        "device": runtime.device,
    }


@app.get("/info")
async def info() -> Dict[str, Any]:
    return {
        "model_name": settings.model_name,
        "device": runtime.device,
        "dtype": str(runtime.dtype),
        "max_upload_size_mb": settings.max_upload_size_mb,
        "defaults": {
            "base_size": settings.default_base_size,
            "image_size": settings.default_image_size,
            "crop_mode": settings.default_crop_mode,
        },
    }


@app.post("/api/ocr", response_model=OCRResult)
async def ocr_inference(
    image: UploadFile = File(...),
    mode: str = Form("plain_ocr"),
    prompt: str = Form(""),
    grounding: bool = Form(False),
    include_caption: bool = Form(False),
    find_term: Optional[str] = Form(None),
    schema: Optional[str] = Form(None),
    base_size: int = Form(settings.default_base_size),
    image_size: int = Form(settings.default_image_size),
    crop_mode: bool = Form(settings.default_crop_mode),
    test_compress: bool = Form(False),
) -> OCRResult:
    runtime_instance = _read_runtime()

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Uploaded file exceeds maximum size of "
                f"{settings.max_upload_size_mb} MB."
            ),
        )

    prompt_text = build_prompt(
        mode=mode,
        user_prompt=prompt,
        grounding=grounding,
        find_term=find_term,
        schema=schema,
        include_caption=include_caption,
    )

    tmp_img_path: Optional[str] = None
    tmp_output_dir: Optional[str] = None
    orig_width: Optional[int] = None
    orig_height: Optional[int] = None

    start_time = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(content)
            tmp_img_path = tmp_file.name

        with Image.open(tmp_img_path) as pil_image:
            orig_width, orig_height = pil_image.size

        tmp_output_dir = tempfile.mkdtemp(prefix="dsocr_out_")
        result = runtime_instance.infer(
            prompt=prompt_text,
            image_path=tmp_img_path,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            test_compress=test_compress,
            output_dir=tmp_output_dir,
        )

        if isinstance(result, str):
            raw_text = result.strip()
        elif isinstance(result, dict) and "text" in result:
            raw_text = str(result["text"]).strip()
        elif isinstance(result, (list, tuple)):
            raw_text = "\n".join(map(str, result)).strip()
        else:
            raw_text = ""

        if not raw_text and tmp_output_dir:
            fallback_path = os.path.join(tmp_output_dir, "result.mmd")
            if os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as handle:
                    raw_text = handle.read().strip()

        if not raw_text:
            raw_text = "No text returned by model."

        boxes = (
            parse_detections(raw_text, orig_width or 1, orig_height or 1)
            if ("<|det|>" in raw_text or "<|ref|>" in raw_text)
            else []
        )

        display_text = (
            clean_grounding_text(raw_text)
            if ("<|ref|>" in raw_text or "<|grounding|>" in raw_text)
            else raw_text
        )

        if not display_text and boxes:
            display_text = ", ".join(box["label"] for box in boxes)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        response = OCRResult(
            text=display_text,
            raw_text=raw_text,
            boxes=[BoundingBox(**box) for box in boxes],
            image_dims={"w": orig_width, "h": orig_height},
            metadata=OCRMetadata(
                mode=mode,
                grounding=grounding
                or (mode in {"find_ref", "layout_map", "pii_redact"}),
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                include_caption=include_caption,
                elapsed_ms=elapsed_ms,
            ),
        )
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("OCR inference failed.")
        raise HTTPException(
            status_code=500, detail=f"{type(exc).__name__}: {exc}"
        ) from exc
    finally:
        if tmp_img_path:
            try:
                os.remove(tmp_img_path)
            except OSError:
                logger.debug("Failed to remove temporary image %s", tmp_img_path)
        if tmp_output_dir:
            shutil.rmtree(tmp_output_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
