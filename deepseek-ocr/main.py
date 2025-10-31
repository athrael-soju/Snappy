import ast
import base64
import logging
import os
import re
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel, Field
from transformers import AutoModel, AutoTokenizer
from transformers.utils.import_utils import is_flash_attn_2_available


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


MODEL_PROFILES: Dict[str, Dict[str, Any]] = {
    "gundam": {
        "label": "Gundam",
        "description": "1024 base with 640 crops (balanced quality and speed).",
        "base_size": 1024,
        "image_size": 640,
        "crop_mode": True,
        "aliases": ["gundam"],
    },
    "tiny": {
        "label": "Tiny",
        "description": "512 × 512 without cropping (fastest).",
        "base_size": 512,
        "image_size": 512,
        "crop_mode": False,
        "aliases": ["tiny"],
    },
    "small": {
        "label": "Small",
        "description": "640 × 640 without cropping (quick).",
        "base_size": 640,
        "image_size": 640,
        "crop_mode": False,
        "aliases": ["small"],
    },
    "base": {
        "label": "Base",
        "description": "1024 × 1024 without cropping (standard).",
        "base_size": 1024,
        "image_size": 1024,
        "crop_mode": False,
        "aliases": ["base"],
    },
    "large": {
        "label": "Large",
        "description": "1280 × 1280 without cropping (highest fidelity).",
        "base_size": 1280,
        "image_size": 1280,
        "crop_mode": False,
        "aliases": ["large"],
    },
}


def _build_profile_alias_map() -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for key, data in MODEL_PROFILES.items():
        alias_map[key.lower()] = key
        label = data.get("label")
        if label:
            alias_map[label.lower()] = key
        for alias in data.get("aliases", []):
            alias_map[alias.lower()] = key
    return alias_map


PROFILE_ALIAS_MAP = _build_profile_alias_map()
DEFAULT_PROFILE_KEY = "gundam"
ALLOWED_BASE_SIZES = tuple(
    sorted({int(data["base_size"]) for data in MODEL_PROFILES.values()})
)
ALLOWED_IMAGE_SIZES = tuple(
    sorted({int(data["image_size"]) for data in MODEL_PROFILES.values()})
)
DEFAULT_BASE_SIZE = int(MODEL_PROFILES[DEFAULT_PROFILE_KEY]["base_size"])
DEFAULT_IMAGE_SIZE = int(MODEL_PROFILES[DEFAULT_PROFILE_KEY]["image_size"])
MIN_BASE_SIZE = min(ALLOWED_BASE_SIZES)
MIN_IMAGE_SIZE = min(ALLOWED_IMAGE_SIZES)
DEFAULT_MODE = "plain_ocr"


TASK_PRESETS: Dict[str, Dict[str, Any]] = {
    "plain_ocr": {
        "label": "📝 Free OCR",
        "description": "Transcribe the document without additional formatting.",
        "requires_grounding": False,
        "aliases": ["free ocr", "📝 free ocr", "ocr", "plain_text", "plain text"],
    },
    "markdown": {
        "label": "📋 Markdown",
        "description": "Convert the document into structured Markdown.",
        "requires_grounding": True,
        "aliases": ["markdown", "📋 markdown"],
    },
    "tables_csv": {
        "label": "📊 Tables (CSV)",
        "description": "Extract every table as CSV text.",
        "requires_grounding": False,
        "aliases": ["tables_csv", "csv tables"],
    },
    "tables_md": {
        "label": "🧾 Tables (Markdown)",
        "description": "Extract tables using GitHub-flavoured Markdown.",
        "requires_grounding": False,
        "aliases": ["tables_md", "markdown tables"],
    },
    "kv_json": {
        "label": "🔐 Key-Value JSON",
        "description": "Fill a provided JSON schema with extracted values.",
        "requires_grounding": False,
        "aliases": ["kv_json", "kv json", "json"],
    },
    "figure_chart": {
        "label": "📈 Figure Summary",
        "description": "Extract numeric series and summarise charts.",
        "requires_grounding": False,
        "aliases": ["figure_chart", "figure", "chart"],
    },
    "find_ref": {
        "label": "📍 Locate",
        "description": "Locate specific references in the document.",
        "requires_grounding": True,
        "aliases": ["locate", "📍 locate", "find_ref"],
    },
    "layout_map": {
        "label": "🗺️ Layout Map",
        "description": "Return bounding boxes grouped by block type.",
        "requires_grounding": True,
        "aliases": ["layout_map", "layout"],
    },
    "pii_redact": {
        "label": "🔒 PII Redaction",
        "description": "Detect PII entities and return bounding boxes.",
        "requires_grounding": True,
        "aliases": ["pii_redact", "pii"],
    },
    "multilingual": {
        "label": "🌐 Multilingual OCR",
        "description": "Transcribe text preserving the detected language.",
        "requires_grounding": False,
        "aliases": ["multilingual"],
    },
    "describe": {
        "label": "🔍 Describe",
        "description": "Generate a natural language description of the image.",
        "requires_grounding": False,
        "aliases": ["describe", "🔍 describe"],
    },
    "freeform": {
        "label": "✏️ Custom Prompt",
        "description": "Use a custom instruction (add <|grounding|> to enable boxes).",
        "requires_grounding": False,
        "aliases": ["custom", "✏️ custom", "freeform"],
    },
}


def _build_task_alias_map() -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for key, data in TASK_PRESETS.items():
        alias_map[key.lower()] = key
        label = data.get("label")
        if label:
            alias_map[label.lower()] = key
        for alias in data.get("aliases", []):
            alias_map[alias.lower()] = key
    return alias_map


TASK_ALIAS_MAP = _build_task_alias_map()


def normalize_profile(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    key = name.strip().lower()
    return PROFILE_ALIAS_MAP.get(key, None)


def normalize_mode(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    key = name.strip().lower()
    mapped = TASK_ALIAS_MAP.get(key)
    if mapped:
        return mapped
    return None


def _sanitize_dimension(
    name: str,
    value: Optional[int],
    fallback: int,
    allowed: Optional[tuple[int, ...]] = None,
) -> int:
    """Validate dimension overrides; coerce placeholders to defaults and reject unsupported values."""
    allowed_set = set(allowed or ())
    if allowed_set:
        if fallback not in allowed_set:
            logger.warning(
                "Configured default %s (%s) is not in the allowed set %s. Using %s instead.",
                name,
                fallback,
                sorted(allowed_set),
                max(allowed_set),
            )
            fallback = max(allowed_set)
    if fallback <= 0:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: default {name} must be a positive integer.",
        )
    if value is None:
        return fallback
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        if isinstance(value, str) and value.strip().lower() in {"", "string"}:
            logger.debug(
                "Ignoring placeholder %s override '%s'; using fallback %s.",
                name,
                value,
                fallback,
            )
            return fallback
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} override '{value}'. Expected a positive integer.",
        ) from None
    if numeric <= 0:
        logger.debug(
            "Ignoring non-positive %s override (%s); using fallback %s.",
            name,
            numeric,
            fallback,
        )
        return fallback
    if allowed_set and numeric not in allowed_set:
        allowed_str = ", ".join(str(v) for v in sorted(allowed_set))
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be one of {{{allowed_str}}} (received {numeric}).",
        )
    return numeric


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
    default_profile: str = os.getenv(
        "DEEPSEEK_OCR_DEFAULT_PROFILE",
        os.getenv("DEFAULT_PROFILE", "gundam"),
    )
    enable_flash_attn: bool = _parse_bool(
        os.getenv(
            "DEEPSEEK_OCR_ENABLE_FLASH_ATTN",
            os.getenv("ENABLE_FLASH_ATTN", "true"),
        ),
        True,
    )
    default_return_markdown: bool = _parse_bool(
        os.getenv(
            "DEEPSEEK_OCR_RETURN_MARKDOWN",
            os.getenv("RETURN_MARKDOWN", "false"),
        ),
        False,
    )
    default_return_figures: bool = _parse_bool(
        os.getenv(
            "DEEPSEEK_OCR_RETURN_FIGURES",
            os.getenv("RETURN_FIGURES", "false"),
        ),
        False,
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def default_profile_key(self) -> Optional[str]:
        return normalize_profile(self.default_profile)

    def __post_init__(self) -> None:
        if self.default_base_size < MIN_BASE_SIZE:
            raise ValueError(
                f"BASE_SIZE must be at least {MIN_BASE_SIZE} (received {self.default_base_size})."
            )
        if self.default_image_size < MIN_IMAGE_SIZE:
            raise ValueError(
                f"IMAGE_SIZE must be at least {MIN_IMAGE_SIZE} (received {self.default_image_size})."
            )
        if self.default_image_size > self.default_base_size:
            raise ValueError(
                "IMAGE_SIZE must not exceed BASE_SIZE "
                f"(received base_size={self.default_base_size}, image_size={self.default_image_size})."
            )
        if self.default_base_size not in ALLOWED_BASE_SIZES:
            raise ValueError(
                f"BASE_SIZE must be one of {sorted(ALLOWED_BASE_SIZES)} "
                f"(received {self.default_base_size})."
            )
        if self.default_image_size not in ALLOWED_IMAGE_SIZES:
            raise ValueError(
                f"IMAGE_SIZE must be one of {sorted(ALLOWED_IMAGE_SIZES)} "
                f"(received {self.default_image_size})."
            )
        if self.default_profile and self.default_profile_key is None:
            raise ValueError(
                f"DEFAULT_PROFILE '{self.default_profile}' is not a recognised DeepSeek OCR profile."
            )


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
        self.flash_available: bool = False
        self.flash_enabled: bool = False
        self.attn_implementation: str = "eager"

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

        try:
            flash_available = bool(
                is_flash_attn_2_available() if self.device == "cuda" else False
            )
        except Exception:  # pragma: no cover - defensive guard
            flash_available = False

        flash_enabled = False
        attn_impl = "eager"

        if self.settings.enable_flash_attn and self.device != "cuda":
            logger.warning(
                "FlashAttention requested but device '%s' does not support it. Falling back to eager attention.",
                self.device,
            )
        elif self.settings.enable_flash_attn and flash_available:
            attn_impl = "flash_attention_2"
            flash_enabled = True
            logger.info("FlashAttention 2 detected; using flash_attention_2 kernels.")
        elif self.settings.enable_flash_attn and not flash_available:
            logger.warning(
                "FlashAttention requested but flash-attn kernels are unavailable. Falling back to eager attention."
            )
        elif not self.settings.enable_flash_attn and flash_available:
            logger.info("FlashAttention 2 is available but disabled via configuration.")

        self.flash_available = flash_available
        self.flash_enabled = flash_enabled
        self.attn_implementation = attn_impl

        tokenizer = AutoTokenizer.from_pretrained(
            self.settings.model_name,
            trust_remote_code=True,
        )

        model = (
            AutoModel.from_pretrained(
                self.settings.model_name,
                trust_remote_code=True,
                use_safetensors=True,
                attn_implementation=attn_impl,
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


def generate_figure_crops(
    image_path: Optional[str], boxes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate base64-encoded crops for boxes labelled as images."""
    if not image_path:
        return []

    figures: List[Dict[str, Any]] = []
    try:
        with Image.open(image_path) as source:
            for box in boxes:
                if box["label"].lower() != "image":
                    continue
                coords = box["box"]
                if len(coords) != 4:
                    continue
                x1, y1, x2, y2 = coords
                if x2 <= x1 or y2 <= y1:
                    continue
                crop = source.crop((x1, y1, x2, y2))
                buffer = BytesIO()
                crop.save(buffer, format="PNG")
                encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
                figures.append(
                    {
                        "index": len(figures) + 1,
                        "label": box["label"],
                        "box": coords,
                        "data_uri": f"data:image/png;base64,{encoded}",
                    }
                )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.debug("Failed to generate figure crops: %s", exc)
    return figures


def build_markdown(text: str, figures: List[Dict[str, Any]]) -> str:
    """Assemble a markdown string with optional figure embeds."""
    base = text.strip()
    if not figures:
        return base

    parts = [base] if base else []
    for figure in figures:
        label = figure["label"] or f"Figure {figure['index']}"
        parts.append(f"![Figure {figure['index']}: {label}]({figure['data_uri']})")
    return "\n\n".join(parts).strip()


def list_profile_presets() -> List[Dict[str, Any]]:
    """Expose profile presets in a serialisable structure."""
    payload: List[Dict[str, Any]] = []
    for key, data in MODEL_PROFILES.items():
        payload.append(
            {
                "key": key,
                "label": data.get("label", key.title()),
                "description": data.get("description"),
                "base_size": data.get("base_size"),
                "image_size": data.get("image_size"),
                "crop_mode": data.get("crop_mode"),
                "aliases": data.get("aliases", []),
            }
        )
    return payload


def list_task_presets() -> List[Dict[str, Any]]:
    """Expose task presets for API consumers."""
    payload: List[Dict[str, Any]] = []
    for key, data in TASK_PRESETS.items():
        payload.append(
            {
                "key": key,
                "label": data.get("label", key),
                "description": data.get("description"),
                "requires_grounding": data.get("requires_grounding", False),
                "aliases": data.get("aliases", []),
            }
        )
    return payload


class BoundingBox(BaseModel):
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)


class OCRFigure(BaseModel):
    index: int = Field(..., ge=1)
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)
    data_uri: str


class OCRMetadata(BaseModel):
    mode: str
    grounding: bool
    base_size: int
    image_size: int
    crop_mode: bool
    include_caption: bool
    elapsed_ms: int
    profile: Optional[str] = None
    attention: str


class OCRResult(BaseModel):
    success: bool = True
    text: str
    raw_text: str
    markdown: Optional[str] = None
    boxes: List[BoundingBox]
    figures: List[OCRFigure] = Field(default_factory=list)
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
        "flash_attention": {
            "requested": settings.enable_flash_attn,
            "available": bool(
                getattr(runtime_instance, "flash_available", False)
                if runtime_instance
                else False
            ),
            "enabled": bool(
                getattr(runtime_instance, "flash_enabled", False)
                if runtime_instance
                else False
            ),
            "implementation": (
                getattr(runtime_instance, "attn_implementation", "eager")
                if runtime_instance
                else "eager"
            ),
        },
    }


@app.get("/info")
async def info() -> Dict[str, Any]:
    runtime_instance = getattr(app.state, "runtime", None)
    profile_key = settings.default_profile_key or (
        "gundam" if "gundam" in MODEL_PROFILES else None
    )
    profile_label = MODEL_PROFILES[profile_key]["label"] if profile_key else None
    return {
        "model_name": settings.model_name,
        "device": runtime.device,
        "dtype": str(runtime.dtype),
        "max_upload_size_mb": settings.max_upload_size_mb,
        "defaults": {
            "base_size": settings.default_base_size,
            "image_size": settings.default_image_size,
            "crop_mode": settings.default_crop_mode,
            "profile": profile_key,
            "profile_label": profile_label,
            "return_markdown": settings.default_return_markdown,
            "return_figures": settings.default_return_figures,
        },
        "profiles": list_profile_presets(),
        "tasks": list_task_presets(),
        "flash_attention": {
            "requested": settings.enable_flash_attn,
            "available": bool(
                getattr(runtime_instance, "flash_available", False)
                if runtime_instance
                else False
            ),
            "enabled": bool(
                getattr(runtime_instance, "flash_enabled", False)
                if runtime_instance
                else False
            ),
            "implementation": (
                getattr(runtime_instance, "attn_implementation", "eager")
                if runtime_instance
                else "eager"
            ),
        },
    }


@app.get("/presets")
async def presets() -> Dict[str, Any]:
    """List available profile and task presets."""
    return {
        "profiles": list_profile_presets(),
        "tasks": list_task_presets(),
    }


@app.post("/api/ocr", response_model=OCRResult)
async def ocr_inference(
    image: UploadFile = File(...),
    mode: Optional[str] = Form(
        None,
        description="OCR mode/task (plain_ocr, markdown, locate, describe, etc.).",
    ),
    profile: Optional[str] = Form(
        None,
        description="Model profile preset (gundam, tiny, small, base, large).",
    ),
    prompt: str = Form(""),
    grounding: Optional[bool] = Form(
        None, description="Override grounding flag (defaults based on mode)."
    ),
    include_caption: bool = Form(False),
    find_term: Optional[str] = Form(None),
    schema: Optional[str] = Form(None),
    base_size: Optional[int] = Form(
        None, description="Override base size (falls back to profile/default)."
    ),
    image_size: Optional[int] = Form(
        None, description="Override image size (falls back to profile/default)."
    ),
    crop_mode: Optional[bool] = Form(
        None, description="Override crop mode (falls back to profile/default)."
    ),
    test_compress: bool = Form(False),
    return_markdown: Optional[bool] = Form(
        None, description="Return markdown output with embedded figures."
    ),
    return_figures: Optional[bool] = Form(
        None,
        description="Include base64-encoded figure crops in the response.",
    ),
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

    requested_mode = mode or DEFAULT_MODE
    normalized_mode = normalize_mode(requested_mode)
    if normalized_mode is None:
        if mode:
            logger.warning(
                "Unknown DeepSeek OCR mode '%s'; using default '%s'.",
                mode,
                DEFAULT_MODE,
            )
        resolved_mode = DEFAULT_MODE
    else:
        resolved_mode = normalized_mode
    task_meta = TASK_PRESETS.get(resolved_mode, {})

    normalized_profile = normalize_profile(profile) if profile else None
    if profile and normalized_profile is None:
        logger.warning(
            "Unknown DeepSeek OCR profile preset '%s'; using default profile '%s'.",
            profile,
            settings.default_profile_key or DEFAULT_PROFILE_KEY,
        )
        normalized_profile = settings.default_profile_key or DEFAULT_PROFILE_KEY

    profile_key = (
        normalized_profile or settings.default_profile_key or DEFAULT_PROFILE_KEY
    )
    profile_config = MODEL_PROFILES.get(profile_key) if profile_key else None

    default_base = (
        int(profile_config["base_size"])
        if profile_config
        else settings.default_base_size
    )
    default_image = (
        int(profile_config["image_size"])
        if profile_config
        else settings.default_image_size
    )
    if default_image > default_base:
        adjusted_image = max(
            (val for val in ALLOWED_IMAGE_SIZES if val <= default_base),
            default=default_base,
        )
        logger.warning(
            "Default image_size (%s) exceeds base_size (%s); using %s instead.",
            default_image,
            default_base,
            adjusted_image,
        )
        default_image = adjusted_image
    if default_base <= 0 or default_image <= 0:
        raise HTTPException(
            status_code=500,
            detail="DeepSeek OCR profile defaults must be positive integers.",
        )

    resolved_base_size = _sanitize_dimension(
        "base_size",
        base_size,
        default_base,
        ALLOWED_BASE_SIZES,
    )
    resolved_image_size = _sanitize_dimension(
        "image_size",
        image_size,
        default_image,
        ALLOWED_IMAGE_SIZES,
    )
    if resolved_image_size > resolved_base_size:
        logger.warning(
            "Requested image_size (%s) exceeds base_size (%s); reverting to profile defaults %s/%s.",
            resolved_image_size,
            resolved_base_size,
            default_base,
            default_image,
        )
        resolved_base_size = default_base
        resolved_image_size = (
            default_image if default_image <= default_base else default_base
        )
    resolved_crop_mode = (
        crop_mode
        if crop_mode is not None
        else (
            profile_config["crop_mode"]
            if profile_config
            else settings.default_crop_mode
        )
    )

    effective_grounding = (
        task_meta.get("requires_grounding", False) if grounding is None else grounding
    )

    include_markdown = (
        settings.default_return_markdown if return_markdown is None else return_markdown
    )
    include_figures = (
        settings.default_return_figures if return_figures is None else return_figures
    )
    if include_markdown:
        include_figures = True

    prompt_text = build_prompt(
        mode=resolved_mode,
        user_prompt=prompt,
        grounding=effective_grounding,
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
            base_size=resolved_base_size,
            image_size=resolved_image_size,
            crop_mode=resolved_crop_mode,
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

        figures_data: List[Dict[str, Any]] = []
        if (include_markdown or include_figures) and boxes:
            figures_data = generate_figure_crops(tmp_img_path, boxes)

        markdown_text = (
            build_markdown(display_text, figures_data) if include_markdown else None
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        response = OCRResult(
            text=display_text,
            raw_text=raw_text,
            markdown=markdown_text,
            boxes=[BoundingBox(**box) for box in boxes],
            figures=(
                [OCRFigure(**figure) for figure in figures_data]
                if include_figures
                else []
            ),
            image_dims={"w": orig_width, "h": orig_height},
            metadata=OCRMetadata(
                mode=resolved_mode,
                grounding=effective_grounding
                or (resolved_mode in {"find_ref", "layout_map", "pii_redact"}),
                base_size=resolved_base_size,
                image_size=resolved_image_size,
                crop_mode=resolved_crop_mode,
                include_caption=include_caption,
                elapsed_ms=elapsed_ms,
                profile=profile_key,
                attention=runtime_instance.attn_implementation,
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
