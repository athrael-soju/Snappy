from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import config
from api.dependencies import get_deepseek_client
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from services.deepseek_ocr import DeepSeekOCRError, DeepSeekOCRService

router = APIRouter(prefix="/ocr", tags=["ocr"])
logger = logging.getLogger(__name__)


class TaskName(str, Enum):
    plain_ocr = "plain_ocr"
    markdown = "markdown"
    tables_csv = "tables_csv"
    tables_md = "tables_md"
    kv_json = "kv_json"
    figure_chart = "figure_chart"
    find_ref = "find_ref"
    layout_map = "layout_map"
    pii_redact = "pii_redact"
    multilingual = "multilingual"
    describe = "describe"
    freeform = "freeform"


class ProfileName(str, Enum):
    gundam = "gundam"
    tiny = "tiny"
    small = "small"
    base = "base"
    large = "large"


class BaseSize(int, Enum):
    size_512 = 512
    size_640 = 640
    size_1024 = 1024
    size_1280 = 1280


class ImageSize(int, Enum):
    size_512 = 512
    size_640 = 640
    size_1024 = 1024
    size_1280 = 1280


TASK_KEYS: tuple[str, ...] = tuple(item.value for item in TaskName)
PROFILE_KEYS: tuple[str, ...] = tuple(item.value for item in ProfileName)
ALLOWED_BASE_SIZES: tuple[int, ...] = tuple(item.value for item in BaseSize)
ALLOWED_IMAGE_SIZES: tuple[int, ...] = tuple(item.value for item in ImageSize)
DEFAULT_MODE = TaskName.plain_ocr.value
DEFAULT_PROFILE = ProfileName.gundam.value
DEFAULT_BASE_SIZE = 1024
DEFAULT_IMAGE_SIZE = 640
DEFAULT_BASE_INDEX = (
    ALLOWED_BASE_SIZES.index(DEFAULT_BASE_SIZE)
    if DEFAULT_BASE_SIZE in ALLOWED_BASE_SIZES
    else 0
)
DEFAULT_IMAGE_INDEX = (
    ALLOWED_IMAGE_SIZES.index(DEFAULT_IMAGE_SIZE)
    if DEFAULT_IMAGE_SIZE in ALLOWED_IMAGE_SIZES
    else 0
)
MIN_BASE_SIZE = min(ALLOWED_BASE_SIZES)
MIN_IMAGE_SIZE = min(ALLOWED_IMAGE_SIZES)


def _coerce_config_int(value: Any, key: str, minimum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid configuration for %s (value=%r). Falling back to %s.",
            key,
            value,
            minimum,
        )
        return minimum
    if numeric < minimum:
        logger.warning(
            "%s is below the supported minimum (%s < %s). Using %s instead.",
            key,
            numeric,
            minimum,
            minimum,
        )
        return minimum
    return numeric


def _coerce_config_choice(
    value: Any, key: str, allowed: tuple[str, ...], default: str
) -> str:
    if value in allowed:
        return str(value)
    logger.warning(
        "%s '%s' is invalid. Falling back to '%s'.",
        key,
        value,
        default,
    )
    return default


def _coerce_config_int_choice(
    value: Any, key: str, allowed: tuple[int, ...], fallback_index: int = 0
) -> int:
    fallback = allowed[fallback_index]
    numeric = _coerce_config_int(value, key, allowed[0])
    if numeric not in allowed:
        logger.warning(
            "%s must be one of %s. Falling back to %s.",
            key,
            ", ".join(str(v) for v in allowed),
            fallback,
        )
        return fallback
    return numeric


class OCRBoundingBox(BaseModel):
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)


class OCRFigure(BaseModel):
    index: int
    label: str
    box: List[int] = Field(..., min_items=4, max_items=4)
    data_uri: str


class OCRMetadata(BaseModel):
    mode: str = Field(..., description="OCR mode used for the request.")
    grounding: bool = Field(
        ..., description="Whether grounding boxes were enabled for the request."
    )
    base_size: int = Field(
        ..., description="Base resize dimension passed to the model."
    )
    image_size: int = Field(
        ..., description="Image size parameter passed to the model."
    )
    crop_mode: bool = Field(..., description="Crop mode flag used during inference.")
    include_caption: bool = Field(..., description="Whether captions were requested.")
    elapsed_ms: Optional[int] = Field(
        None, description="Elapsed time reported by the OCR service in milliseconds."
    )
    profile: Optional[str] = Field(
        None, description="Profile preset applied to derive sizing defaults."
    )
    attention: str = Field(
        ..., description="Attention implementation used by the model."
    )


class OCRResponse(BaseModel):
    success: bool = True
    text: str
    raw_text: str
    markdown: Optional[str] = None
    boxes: List[OCRBoundingBox]
    figures: List[OCRFigure] = Field(default_factory=list)
    image_dims: Dict[str, Optional[int]]
    metadata: OCRMetadata


class OCRDefaults(BaseModel):
    mode: str
    prompt: str
    grounding: bool
    include_caption: bool
    base_size: int
    image_size: int
    crop_mode: bool
    test_compress: bool
    profile: Optional[str]
    return_markdown: bool
    return_figures: bool


class OCRProfilePreset(BaseModel):
    key: str
    label: str
    description: Optional[str] = None
    base_size: Optional[int] = None
    image_size: Optional[int] = None
    crop_mode: Optional[bool] = None
    aliases: List[str] = Field(default_factory=list)


class OCRTaskPreset(BaseModel):
    key: str
    label: str
    description: Optional[str] = None
    requires_grounding: bool = False
    aliases: List[str] = Field(default_factory=list)


class OCRPresets(BaseModel):
    profiles: List[OCRProfilePreset]
    tasks: List[OCRTaskPreset]


class OCRHealth(BaseModel):
    enabled: bool
    healthy: bool
    model_loaded: Optional[bool] = None
    device: Optional[str] = None


def _ensure_enabled() -> None:
    if not getattr(config, "DEEPSEEK_OCR_ENABLED", False):
        raise HTTPException(
            status_code=503, detail="DeepSeek OCR integration is disabled."
        )


def _get_defaults() -> OCRDefaults:
    default_mode = _coerce_config_choice(
        getattr(config, "DEEPSEEK_OCR_DEFAULT_MODE", DEFAULT_MODE),
        "DEEPSEEK_OCR_DEFAULT_MODE",
        TASK_KEYS,
        DEFAULT_MODE,
    )

    default_profile = _coerce_config_choice(
        getattr(config, "DEEPSEEK_OCR_DEFAULT_PROFILE", DEFAULT_PROFILE),
        "DEEPSEEK_OCR_DEFAULT_PROFILE",
        PROFILE_KEYS,
        DEFAULT_PROFILE,
    )

    fallback_base = ALLOWED_BASE_SIZES[DEFAULT_BASE_INDEX]
    base_size = _coerce_config_int_choice(
        getattr(config, "DEEPSEEK_OCR_DEFAULT_BASE_SIZE", fallback_base),
        "DEEPSEEK_OCR_DEFAULT_BASE_SIZE",
        ALLOWED_BASE_SIZES,
        DEFAULT_BASE_INDEX,
    )
    fallback_image = ALLOWED_IMAGE_SIZES[DEFAULT_IMAGE_INDEX]
    image_size = _coerce_config_int_choice(
        getattr(config, "DEEPSEEK_OCR_DEFAULT_IMAGE_SIZE", fallback_image),
        "DEEPSEEK_OCR_DEFAULT_IMAGE_SIZE",
        ALLOWED_IMAGE_SIZES,
        DEFAULT_IMAGE_INDEX,
    )
    if base_size < image_size:
        logger.warning(
            "DEEPSEEK_OCR default base/image sizes are inconsistent (%s < %s). "
            "Falling back to profile-aligned values %s/%s.",
            base_size,
            image_size,
            fallback_base,
            fallback_image,
        )
        base_size = fallback_base
        image_size = fallback_image if fallback_image <= base_size else base_size

    return OCRDefaults(
        mode=default_mode,
        prompt=getattr(config, "DEEPSEEK_OCR_DEFAULT_PROMPT", ""),
        grounding=getattr(config, "DEEPSEEK_OCR_DEFAULT_GROUNDING", False),
        include_caption=getattr(config, "DEEPSEEK_OCR_DEFAULT_INCLUDE_CAPTION", False),
        base_size=base_size,
        image_size=image_size,
        crop_mode=getattr(config, "DEEPSEEK_OCR_DEFAULT_CROP_MODE", False),
        test_compress=getattr(config, "DEEPSEEK_OCR_DEFAULT_TEST_COMPRESS", False),
        profile=default_profile,
        return_markdown=getattr(config, "DEEPSEEK_OCR_RETURN_MARKDOWN", False),
        return_figures=getattr(config, "DEEPSEEK_OCR_RETURN_FIGURES", False),
    )


@router.get("/defaults", response_model=OCRDefaults)
async def get_defaults() -> OCRDefaults:
    """Return the configured default values used when optional OCR fields are omitted."""
    _ensure_enabled()
    return _get_defaults()


@router.get("/health", response_model=OCRHealth)
async def health(
    service: DeepSeekOCRService = Depends(get_deepseek_client),
) -> OCRHealth:
    """Surface the health status of the DeepSeek OCR service."""
    if not getattr(config, "DEEPSEEK_OCR_ENABLED", False):
        return OCRHealth(enabled=False, healthy=False)

    healthy = service.health_check()
    info: Dict[str, Any] = {}

    if healthy:
        try:
            info = service.get_info()
        except Exception:  # pragma: no cover - info endpoint optional
            info = {}

    return OCRHealth(
        enabled=True,
        healthy=healthy,
        model_loaded=healthy,
        device=str(info.get("device", "")) or None,
    )


@router.get("/info")
async def info(
    service: DeepSeekOCRService = Depends(get_deepseek_client),
) -> Dict[str, Any]:
    """Expose metadata returned by the DeepSeek OCR service."""
    _ensure_enabled()
    return service.get_info()


@router.get("/presets", response_model=OCRPresets)
async def presets(
    service: DeepSeekOCRService = Depends(get_deepseek_client),
) -> OCRPresets:
    """Expose available profile and task presets from the OCR service."""
    _ensure_enabled()
    payload = service.get_presets()
    return OCRPresets.model_validate(payload)


@router.post("/infer", response_model=OCRResponse)
async def run_ocr(
    image: UploadFile = File(..., description="Image to process."),
    mode: Optional[TaskName] = Form(
        None,
        description="OCR mode / task preset.",
        example=DEFAULT_MODE,
    ),
    profile: Optional[ProfileName] = Form(
        None,
        description="Profile preset controlling default sizing.",
        example=DEFAULT_PROFILE,
    ),
    prompt: Optional[str] = Form(None, description="Custom prompt for freeform mode."),
    grounding: Optional[bool] = Form(
        None, description="Force grounding boxes regardless of selected mode."
    ),
    include_caption: Optional[bool] = Form(
        None, description="Request an additional descriptive caption."
    ),
    find_term: Optional[str] = Form(
        None, description="Term to highlight for 'find_ref' mode."
    ),
    kv_schema: Optional[str] = Form(
        None,
        alias="schema",
        description="JSON schema used by 'kv_json' mode. Provide raw JSON text.",
        example="",
    ),
    base_size: Optional[BaseSize] = Form(
        None,
        description=(
            "Base resize dimension passed to the OCR service "
            f"(allowed values: {', '.join(str(v) for v in ALLOWED_BASE_SIZES)})."
        ),
        example=DEFAULT_BASE_SIZE,
    ),
    image_size: Optional[ImageSize] = Form(
        None,
        description=(
            "Image input size passed to the OCR service "
            f"(allowed values: {', '.join(str(v) for v in ALLOWED_IMAGE_SIZES)})."
        ),
        example=DEFAULT_IMAGE_SIZE,
    ),
    crop_mode: Optional[bool] = Form(
        None, description="Enable crop mode during preprocessing."
    ),
    test_compress: Optional[bool] = Form(
        None, description="Run compression diagnostics without saving artifacts."
    ),
    return_markdown: Optional[bool] = Form(
        None,
        description="Return markdown-formatted output from the OCR service.",
        example=True,
    ),
    return_figures: Optional[bool] = Form(
        None,
        description="Include base64-encoded figure crops extracted by the OCR service.",
        example=True,
    ),
    service: DeepSeekOCRService = Depends(get_deepseek_client),
) -> OCRResponse:
    """Proxy OCR requests to the DeepSeek OCR service with Snappy defaults."""
    _ensure_enabled()

    payload = await image.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    defaults = _get_defaults()

    mode_value = mode.value if isinstance(mode, TaskName) else mode
    profile_value = profile.value if isinstance(profile, ProfileName) else profile
    base_size_value = defaults.base_size if base_size is None else int(base_size)
    image_size_value = defaults.image_size if image_size is None else int(image_size)

    try:
        result = service.perform_ocr(
            image_bytes=payload,
            filename=image.filename or "upload.bin",
            content_type=image.content_type,
            mode=mode_value or defaults.mode,
            prompt=prompt or defaults.prompt,
            grounding=defaults.grounding if grounding is None else grounding,
            include_caption=(
                defaults.include_caption if include_caption is None else include_caption
            ),
            find_term=find_term,
            schema=kv_schema,
            base_size=base_size_value,
            image_size=image_size_value,
            crop_mode=defaults.crop_mode if crop_mode is None else crop_mode,
            test_compress=(
                defaults.test_compress if test_compress is None else test_compress
            ),
            profile=profile_value or defaults.profile,
            return_markdown=(
                defaults.return_markdown if return_markdown is None else return_markdown
            ),
            return_figures=(
                defaults.return_figures if return_figures is None else return_figures
            ),
        )
    except DeepSeekOCRError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        return OCRResponse.model_validate(result)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek OCR returned an unexpected payload: {exc}",
        ) from exc
