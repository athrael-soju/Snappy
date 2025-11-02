import asyncio
import json
import math
import os
import platform
import secrets
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from time import monotonic
from typing import Any, DefaultDict, Deque, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from PIL import Image

# Lazy import DeepSeek-OCR dependencies (only load when needed)
_torch = None
_transformers = None


def _get_torch():
    global _torch
    if _torch is None:
        try:
            import torch

            _torch = torch
        except ImportError:
            raise RuntimeError(
                "torch is not installed. Install with: pip install torch"
            )
    return _torch


def _get_transformers():
    global _transformers
    if _transformers is None:
        try:
            from transformers import AutoModel, AutoTokenizer

            _transformers = (AutoModel, AutoTokenizer)
        except ImportError:
            raise RuntimeError(
                "transformers is not installed. Install with: pip install transformers"
            )
    return _transformers


# Import llm_splitter (works as module or direct import)
try:
    from llm_splitter import call_llm_splitter
except ImportError:
    # Fallback for relative import
    try:
        from .llm_splitter import call_llm_splitter
    except ImportError:
        # If llm_splitter doesn't exist, define a stub
        async def call_llm_splitter(*args, **kwargs):
            raise NotImplementedError("llm_splitter not available")


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = float(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
# Allow API key to be optional for development (security risk in production!)
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dev-key-change-in-production")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
API_KEY_HEADER_NAME = "X-API-Key"
MAX_CHILD_LINES = 500
MAX_JSON_DEPTH = 4
MAX_JSON_STRING_LENGTH = 512
MAX_JSON_DICT_KEYS = 50
MAX_JSON_LIST_ITEMS = 100

# DeepSeek-OCR Model Configuration - Maximum Quality Settings for CPU/Spaces
MODEL_NAME = "deepseek-ai/DeepSeek-OCR"
# PIN MODEL REVISION to prevent auto-updates that break compatibility
MODEL_REVISION = os.getenv(
    "DEEPSEEK_MODEL_REVISION", "2c968b433af61a059311cbf8997765023806a24d"
)

# Detect Apple Silicon (M1/M2/M3/M4) - use MPS if available, otherwise CPU
IS_APPLE_SILICON = platform.machine() == "arm64"
USE_GPU = os.getenv("USE_GPU", "true").lower() == "true" and not IS_APPLE_SILICON
USE_MPS = IS_APPLE_SILICON
# Quality settings - Gundam preset recommended for CPU/Spaces
BASE_SIZE = int(os.getenv("DEEPSEEK_BASE_SIZE", "1024"))
IMAGE_SIZE = int(os.getenv("DEEPSEEK_IMAGE_SIZE", "640"))
CROP_MODE = os.getenv("DEEPSEEK_CROP_MODE", "true").lower() == "true"

app = FastAPI(
    title="DeepSeek-OCR API",
    description="OCR Service using DeepSeek-OCR for maximum quality text extraction",
    version="1.0.0",
)


# Add root endpoint for health check (compatible with HuggingFace Spaces)
@app.get("/")
async def root(__sign: Optional[str] = None):
    """
    Root endpoint - compatible with HuggingFace Spaces authentication.
    The __sign parameter is used by HuggingFace's proxy but can be ignored.
    """
    return {
        "service": "DeepSeek-OCR API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {"docs": "/docs", "ocr": "/ocr", "split": "/split"},
    }


# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize DeepSeek-OCR model
_ocr_model = None
_ocr_tokenizer = None
_model_lock = asyncio.Lock()

# Job management for async processing and cancellation
_jobs: dict[str, dict] = {}  # job_id -> {status, progress, result, error, cancelled}
_jobs_lock = asyncio.Lock()
_cancellation_tokens: dict[str, asyncio.Event] = {}  # job_id -> cancellation event

# Import cancel registry
try:
    from cancel_registry import (
        cancel_job,
        get_cancel_flag,
        is_cancelled,
        new_cancel_flag,
        remove_cancel_flag,
    )
except ImportError:
    # Fallback if cancel_registry not available
    def cancel_job(job_id: str):
        return False

    def get_cancel_flag(job_id: str):
        return _cancellation_tokens.get(job_id)

    def new_cancel_flag(job_id: str):
        return _cancellation_tokens.setdefault(job_id, asyncio.Event())

    def remove_cancel_flag(job_id: str):
        pass

    async def is_cancelled(job_id: str):
        return False


# StoppingCriteria for generation (if transformers supports it)
try:
    from transformers import StoppingCriteria, StoppingCriteriaList

    _STOPPING_CRITERIA_AVAILABLE = True
except ImportError:
    _STOPPING_CRITERIA_AVAILABLE = False
    StoppingCriteria = None
    StoppingCriteriaList = None


class CancelCriterion(StoppingCriteria):
    """Stopping criteria that checks a cancellation flag"""

    def __init__(self, cancel_flag: asyncio.Event):
        self.cancel_flag = cancel_flag

    def __call__(self, input_ids, scores, **kwargs):
        """Return True to stop generation immediately"""
        return self.cancel_flag.is_set()


def _download_and_patch_model_locally(model_id: str, revision: str) -> str:
    """
    Download DeepSeek-OCR to a local dir, patch for CPU:
      - remove hardcoded .cuda()
      - force float32 (strip .bfloat16() / .to(torch.bfloat16))

    Minimal patcher that avoids indentation issues by NOT touching autocast blocks.
    On CPU, torch.autocast is auto-disabled anyway, so we leave it alone.

    Return local path for from_pretrained(...).

    Per official HuggingFace discussions:
    - https://huggingface.co/deepseek-ai/DeepSeek-OCR/discussions/21 (CPU inference)
    - https://huggingface.co/deepseek-ai/DeepSeek-OCR/discussions/20 (BF16/FP32 issues)
    """
    import re

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise RuntimeError(
            "huggingface_hub is required. Install with: pip install huggingface_hub"
        )

    print(f"  📥 Downloading model (revision {revision[:8]})...")
    local_dir = snapshot_download(model_id, revision=revision)
    print(f"  ✅ Downloaded to: {local_dir}")
    local_dir = Path(local_dir)

    def patch_file(p: Path):
        """Minimal patch - only string replacements, no indentation changes"""
        txt0 = p.read_text(encoding="utf-8")
        txt = txt0

        # A) Remove hardcoded CUDA device moves (CPU-safe)
        txt = txt.replace(".unsqueeze(-1).cuda()", ".unsqueeze(-1)")
        txt = txt.replace("input_ids.unsqueeze(0).cuda()", "input_ids.unsqueeze(0)")
        txt = txt.replace(
            "(images_crop.cuda(), images_ori.cuda())", "(images_crop, images_ori)"
        )
        txt = txt.replace(
            "images_seq_mask = images_seq_mask.unsqueeze(0).cuda()",
            "images_seq_mask = images_seq_mask.unsqueeze(0)",
        )
        txt = txt.replace(
            "input_ids.unsqueeze(0).cuda().shape[1]", "input_ids.unsqueeze(0).shape[1]"
        )

        # B) Force FP32 (fix BF16 vs FP32), pattern-safe (no newlines/indentation changes)
        txt = re.sub(r"\.bfloat16\(\)", ".float()", txt)
        txt = re.sub(r"\.to\(\s*torch\.bfloat16\s*\)", ".to(torch.float32)", txt)
        txt = re.sub(
            r"\.to\(\s*dtype\s*=\s*torch\.bfloat16\s*\)",
            ".to(dtype=torch.float32)",
            txt,
        )

        # Note: We do NOT touch torch.autocast() blocks - on CPU they're auto-disabled
        # and modifying them risks breaking indentation/syntax

        # C) Ensure tensors and autocast honor the active device (GPU-safe)
        if "from contextlib import nullcontext" not in txt:
            txt = txt.replace(
                "import time\n",
                "import time\nfrom contextlib import nullcontext\n",
                1,
            )

        if "device = next(self.parameters()).device" not in txt:
            txt = txt.replace(
                "        os.makedirs(f'{output_path}/images', exist_ok=True)\n\n",
                "        os.makedirs(f'{output_path}/images', exist_ok=True)\n\n        device = next(self.parameters()).device\n\n",
                1,
            )

        txt = re.sub(
            r"image_transform\(([^)]+)\)\.to\(torch\.float32\)",
            r"image_transform(\1).to(device=device, dtype=torch.float32)",
            txt,
        )

        txt = re.sub(
            r"torch\.LongTensor\(tokenized_str\)(?!\.to\(device\))",
            "torch.LongTensor(tokenized_str).to(device)",
            txt,
        )

        txt = re.sub(
            r"torch\.tensor\(images_seq_mask, dtype=torch\.bool\)(?!, device=device)",
            "torch.tensor(images_seq_mask, dtype=torch.bool, device=device)",
            txt,
        )

        txt = txt.replace(
            "torch.zeros((1, 3, image_size, image_size))",
            "torch.zeros((1, 3, image_size, image_size), device=device)",
        )
        txt = txt.replace(
            "torch.zeros((1, 2), dtype=torch.long)",
            "torch.zeros((1, 2), dtype=torch.long, device=device)",
        )
        txt = txt.replace(
            "torch.zeros((1, 3, base_size, base_size))",
            "torch.zeros((1, 3, base_size, base_size), device=device)",
        )

        txt = re.sub(
            r"torch\.stack\(images_list, dim=0\)(?!\.to\(device\))",
            "torch.stack(images_list, dim=0).to(device)",
            txt,
        )

        txt = re.sub(
            r"torch\.tensor\(images_spatial_crop, dtype=torch\.long\)(?!, device=device)",
            "torch.tensor(images_spatial_crop, dtype=torch.long, device=device)",
            txt,
        )

        txt = re.sub(
            r"torch\.stack\(images_crop_list, dim=0\)(?!\.to\(device\))",
            "torch.stack(images_crop_list, dim=0).to(device)",
            txt,
        )

        if 'with torch.autocast("cuda", dtype=torch.bfloat16):' in txt:
            txt = txt.replace(
                '            with torch.autocast("cuda", dtype=torch.bfloat16):\n                with torch.no_grad():',
                '            autocast_ctx = (\n                torch.autocast(device.type, dtype=torch.bfloat16)\n                if device.type == "cuda"\n                else nullcontext()\n            )\n            with autocast_ctx:\n                with torch.no_grad():',
            )

        if txt != txt0:
            p.write_text(txt, encoding="utf-8")
            print(f"  ✅ Patched CPU/FP32: {p.name}")
        else:
            print(f"  ℹ️ Already CPU/FP32-safe: {p.name}")

    # Patch both files where they may appear
    targets = list(local_dir.rglob("modeling_deepseekocr.py")) + list(
        local_dir.rglob("deepencoder.py")
    )

    if not targets:
        raise RuntimeError("Could not find DeepSeek-OCR source files to patch")

    for f in targets:
        print(f"  🔍 Found file: {f.name}")
        patch_file(f)

    # Optional: compile check to catch syntax errors early
    try:
        import py_compile

        for f in targets:
            py_compile.compile(str(f), doraise=True)
        print(f"  ✅ Syntax check passed for {len(targets)} file(s)")
    except py_compile.PyCompileError as e:
        raise RuntimeError(f"Syntax check failed after patch: {e}")

    return str(local_dir)


async def get_ocr_model():
    """Lazy load DeepSeek-OCR model with compatibility patching"""
    global _ocr_model, _ocr_tokenizer
    if _ocr_model is None or _ocr_tokenizer is None:
        async with _model_lock:
            if _ocr_model is None or _ocr_tokenizer is None:
                # Lazy import dependencies
                AutoModel, AutoTokenizer = _get_transformers()
                torch = _get_torch()

                print(f"Loading DeepSeek-OCR model (MAXIMUM QUALITY): {MODEL_NAME}")
                print(f"  - Base size: {BASE_SIZE}")
                print(f"  - Image size: {IMAGE_SIZE}")
                print(f"  - Crop mode: {CROP_MODE}")

                # 1) Download & patch; 2) Load from local dir so our patch is used
                local_dir = _download_and_patch_model_locally(
                    MODEL_NAME, MODEL_REVISION
                )

                print("  - Loading tokenizer (local, pinned revision)...")
                _ocr_tokenizer = AutoTokenizer.from_pretrained(
                    local_dir,
                    trust_remote_code=True,
                    local_files_only=True,  # Load from local patched directory
                )
                print("  - Tokenizer loaded successfully")

                # Fix pad_token_id warning
                if _ocr_tokenizer.pad_token_id is None:
                    _ocr_tokenizer.pad_token = (
                        _ocr_tokenizer.eos_token or _ocr_tokenizer.unk_token
                    )

                # Load model with compatibility settings
                load_kwargs = {
                    "trust_remote_code": True,
                    "use_safetensors": True,
                    "attn_implementation": "eager",  # SDPA not supported by this arch
                }

                # Load from patched local directory
                _ocr_model = AutoModel.from_pretrained(
                    local_dir,
                    local_files_only=True,  # Load from local patched directory
                    **load_kwargs,
                ).eval()

                # Handle device placement (force FP32 on CPU/MPS)
                if USE_MPS and torch.backends.mps.is_available():
                    _ocr_model = _ocr_model.to("mps").to(dtype=torch.float32)
                    print("  - DeepSeek-OCR on MPS (float32)")
                elif USE_GPU and torch.cuda.is_available():
                    _ocr_model = _ocr_model.cuda().to(torch.bfloat16)
                    print("  - DeepSeek-OCR on CUDA (bf16)")
                else:
                    _ocr_model = _ocr_model.to(dtype=torch.float32)
                    print("  - DeepSeek-OCR on CPU (float32)")

                # Configure generation to silence warnings
                gc = _ocr_model.generation_config
                gc.do_sample = False  # Greedy decoding
                gc.temperature = 1.0  # Don't mix temperature=0 with do_sample=False
                if _ocr_tokenizer.pad_token_id is None:
                    _ocr_tokenizer.pad_token = (
                        _ocr_tokenizer.eos_token or _ocr_tokenizer.unk_token
                    )
                _ocr_model.generation_config.pad_token_id = _ocr_tokenizer.pad_token_id
                print(
                    "  - Generation config set (do_sample=False, temperature=1.0, pad_token_id set)"
                )
    return _ocr_model, _ocr_tokenizer


async def run_deepseek_ocr(
    image_path: str,
    prompt: str = "<image>\n<|grounding|>Convert the document to markdown with preserved layout.",
    use_grounding: bool = True,
    job_id: Optional[str] = None,
    progress_callback=None,
    detect_fields: bool = True,
) -> dict:
    """
    Run DeepSeek-OCR on an image file with advanced grounding support.
    Supports cancellation via job_id and progress updates via callback.

    If detect_fields=True, also runs locator queries to detect specific fields:
    - Recipe title
    - Ingredients list
    - Instructions/steps
    Returns additional 'field_boxes' with highlighted locations.
    """
    # Check for cancellation before starting
    if job_id:
        async with _jobs_lock:
            cancel_event = _cancellation_tokens.get(job_id)
            if cancel_event and cancel_event.is_set():
                raise asyncio.CancelledError(f"Job {job_id} was cancelled")

    model, tokenizer = await get_ocr_model()

    output_path = tempfile.mkdtemp()

    try:
        # Update progress: Preprocessing (0-10%)
        if progress_callback:
            await progress_callback(0.05, "Preprocessing image...")

        # OCR quality settings - Gundam preset recommended for CPU/Spaces
        torch = _get_torch()
        if USE_GPU and torch.cuda.is_available():
            # GPU: Use maximum quality (Large preset)
            actual_base_size = BASE_SIZE
            actual_image_size = IMAGE_SIZE
        else:
            # CPU/Spaces: Use Gundam preset (recommended for CPU to avoid OOM)
            actual_base_size = 1024
            actual_image_size = 640
            print(
                f"  - Using CPU-optimized quality: base_size={actual_base_size}, image_size={actual_image_size}"
            )

        # Check for cancellation before inference
        if job_id:
            async with _jobs_lock:
                cancel_event = _cancellation_tokens.get(job_id)
                if cancel_event and cancel_event.is_set():
                    raise asyncio.CancelledError(f"Job {job_id} was cancelled")

        # Update progress: Starting inference (10-90%)
        if progress_callback:
            await progress_callback(0.10, "Starting OCR inference...")

        # Use torch.inference_mode() to reduce overhead on CPU
        # Note: We can't interrupt inference mid-process, but we can check before/after
        torch = _get_torch()
        with torch.inference_mode():
            # Check cancellation one more time right before inference (critical point)
            if job_id:
                async with _jobs_lock:
                    cancel_event = _cancellation_tokens.get(job_id)
                    if cancel_event and cancel_event.is_set():
                        raise asyncio.CancelledError(f"Job {job_id} was cancelled")

            # Estimate inference takes ~80% of time (10-90%)
            # We'll update progress during post-processing
            # Note: This is a blocking call - once it starts, it runs to completion
            # The cancellation will be checked immediately after it returns
            result = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=image_path,
                output_path=output_path,
                base_size=actual_base_size,
                image_size=actual_image_size,
                crop_mode=CROP_MODE,
                save_results=False,
                test_compress=False,
            )

            # Check cancellation immediately after inference completes
            if job_id:
                async with _jobs_lock:
                    cancel_event = _cancellation_tokens.get(job_id)
                    if cancel_event and cancel_event.is_set():
                        raise asyncio.CancelledError(
                            f"Job {job_id} was cancelled during inference"
                        )

        # Check for cancellation after inference
        if job_id:
            async with _jobs_lock:
                cancel_event = _cancellation_tokens.get(job_id)
                if cancel_event and cancel_event.is_set():
                    raise asyncio.CancelledError(f"Job {job_id} was cancelled")

        # Update progress: Post-processing (90-95%)
        if progress_callback:
            await progress_callback(0.90, "Parsing OCR results...")

        # Parse result - DeepSeek-OCR returns structured markdown output
        raw_text = result if isinstance(result, str) else str(result)

        # Extract structured lines from raw text (before cleaning)
        # This parses grounding annotations to get bounding boxes
        lines = _parse_deepseek_output(raw_text)

        # Update progress: Cleaning output (95-98%)
        if progress_callback:
            await progress_callback(0.95, "Cleaning output...")

        # Convert to clean markdown (remove tags, keep text)
        clean_markdown = _deepseek_to_markdown(raw_text)

        # Detect specific fields using locator pattern if requested
        field_boxes = {}
        if detect_fields:
            if progress_callback:
                await progress_callback(0.96, "Detecting recipe fields...")

            # Define field detection prompts using locator pattern
            field_prompts = {
                "title": "<image>\nLocate <|ref|>Recipe title<|/ref|> in the image.",
                "ingredients": "<image>\nLocate <|ref|>Ingredients list<|/ref|> in the image.",
                "instructions": "<image>\nLocate <|ref|>Instructions or steps<|/ref|> in the image.",
                "quantity": "<image>\nLocate <|ref|>Total amount or servings<|/ref|> in the image.",
                "cooking_time": "<image>\nLocate <|ref|>Cooking time or prep time<|/ref|> in the image.",
            }

            torch = _get_torch()
            for field_name, locator_prompt in field_prompts.items():
                try:
                    # Check for cancellation
                    if job_id:
                        async with _jobs_lock:
                            cancel_event = _cancellation_tokens.get(job_id)
                            if cancel_event and cancel_event.is_set():
                                break

                    # Check cancellation right before each field detection
                    if job_id:
                        async with _jobs_lock:
                            cancel_event = _cancellation_tokens.get(job_id)
                            if cancel_event and cancel_event.is_set():
                                raise asyncio.CancelledError(
                                    f"Job {job_id} was cancelled during field detection"
                                )

                    # Run locator query for this field
                    with torch.inference_mode():
                        locator_result = model.infer(
                            tokenizer,
                            prompt=locator_prompt,
                            image_file=image_path,
                            output_path=output_path,
                            base_size=actual_base_size,
                            image_size=actual_image_size,
                            crop_mode=CROP_MODE,
                            save_results=False,
                            test_compress=False,
                        )

                    # Check cancellation immediately after locator inference
                    if job_id:
                        async with _jobs_lock:
                            cancel_event = _cancellation_tokens.get(job_id)
                            if cancel_event and cancel_event.is_set():
                                raise asyncio.CancelledError(
                                    f"Job {job_id} was cancelled after field detection"
                                )

                    # Parse locator boxes from result
                    locator_text = (
                        locator_result
                        if isinstance(locator_result, str)
                        else str(locator_result)
                    )
                    locator_boxes = _parse_locator_boxes(locator_text, field_name)
                    if locator_boxes:
                        field_boxes[field_name] = locator_boxes
                except Exception as e:
                    print(f"  ⚠️ Field detection for {field_name} failed: {e}")
                    continue  # Continue with other fields

        # Update progress: Done (100%)
        if progress_callback:
            await progress_callback(1.0, "Complete")

        return {
            "text": clean_markdown,  # Return clean markdown without tags
            "lines": lines,  # Structured lines with bounding boxes
            "field_boxes": (
                field_boxes if detect_fields else {}
            ),  # Field-specific highlight boxes
        }
    except Exception as e:
        print(f"DeepSeek-OCR error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}",
        )
    finally:
        # Cleanup temp directory
        try:
            import shutil

            if os.path.exists(output_path):
                shutil.rmtree(output_path)
        except:
            pass


def _parse_locator_boxes(locator_text: str, field_name: str) -> list:
    """
    Parse bounding boxes from locator pattern output.
    Locator returns: <|ref|>FIELD_NAME<|/ref|><|det|>[x1,y1,x2,y2]<|/det|>
    """
    import re

    boxes = []

    # Pattern: <|ref|>FIELD<|/ref|><|det|>[x1,y1,x2,y2]<|/det|>
    # Note: Locator uses [x1,y1,x2,y2] format (not [x,y,w,h])
    locator_pattern = re.compile(
        r"<\|ref\|>[^<]*<\|\/ref\|><\|det\|>\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]<\|\/det\|>",
        re.DOTALL,
    )

    for match in locator_pattern.finditer(locator_text):
        x1 = int(match.group(1))
        y1 = int(match.group(2))
        x2 = int(match.group(3))
        y2 = int(match.group(4))

        # Convert to [x0, y0, x1, y1] format (top-left to bottom-right)
        boxes.append(
            {"bbox": [x1, y1, x2, y2], "field": field_name, "confidence": 0.95}
        )

    return boxes


def _deepseek_to_markdown(s: str) -> str:
    """
    Convert DeepSeek-OCR tagged output to clean Markdown.
    Removes grounding tags (<|ref|>...</|ref|>) and bbox annotations (<|det|>[...]<|/det|>)
    while preserving the text content.
    """
    import re

    # Remove bbox annotations first
    det_pattern = re.compile(r"<\|det\|>\[[^\]]*\]<\|\/det\|>", re.DOTALL)
    s = det_pattern.sub("", s)

    # Remove ref tags
    ref_pattern = re.compile(r"<\|ref\|>.*?<\|\/ref\|>", re.DOTALL)
    s = ref_pattern.sub("", s)

    # Tidy multiple blank lines
    s = re.sub(r"\n{3,}", "\n\n", s).strip()

    return s


def _parse_deepseek_output(ocr_text: str) -> list:
    """
    Extract structured lines from DeepSeek-OCR markdown output.
    DeepSeek-OCR returns grounding annotations like:
    <|ref|>title<|/ref|><|det|>[[x,y,w,h]]<|/det|># Title

    We parse these annotations to extract precise bounding boxes.
    """
    import re

    lines = []

    # Pattern to match grounding annotations: <|ref|>TYPE<|/ref|><|det|>[[x,y,w,h]]<|/det|>CONTENT
    # Example: <|ref|>title<|/ref|><|det|>[[292, 29, 634, 54]]<|/det|># Taйский карри...
    grounding_pattern = re.compile(
        r"<\|ref\|>([^<]+)<\|\/ref\|><\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|\/det\|>(.*?)(?=<\|ref\||$)",
        re.DOTALL,
    )

    text_lines = ocr_text.split("\n")
    found_grounding = False

    # Try to parse grounding annotations first
    for line in text_lines:
        matches = list(grounding_pattern.finditer(line))
        if matches:
            found_grounding = True
            for match in matches:
                type_name = match.group(1).strip()
                x = int(match.group(2))
                y = int(match.group(3))
                w = int(match.group(4))  # Width
                h = int(match.group(5))  # Height
                content = match.group(6).strip()

                # Remove markdown formatting from content
                content = re.sub(r"^#+\s*", "", content)  # Remove headers
                content = re.sub(r"\*\*", "", content)  # Remove bold
                content = re.sub(r"\*", "", content)  # Remove italic
                content = content.strip()

                if content:
                    lines.append(
                        {
                            "bbox": [
                                x,
                                y,
                                x + w,
                                y + h,
                            ],  # Convert [x, y, w, h] to [x0, y0, x1, y1]
                            "text": content,
                            "conf": 0.95,
                            "type": type_name,  # title, text, sub_title, etc.
                        }
                    )

    # Fallback: if no grounding annotations found, parse markdown as before
    if not found_grounding:
        y_offset = 0
        line_height = 24

        for line_idx, line in enumerate(text_lines):
            stripped = line.strip()
            if not stripped:
                y_offset += line_height // 2
                continue

            # Remove grounding annotations if present (but use fallback positioning)
            stripped = re.sub(
                r"<\|ref\|>[^<]+<\|\/ref\|><\|det\|>\[\[.*?\]\]<\|\/det\|>",
                "",
                stripped,
            )
            stripped = stripped.strip()

            if not stripped:
                continue

            # Handle markdown tables (| separated)
            if "|" in stripped and stripped.count("|") >= 2:
                cells = [cell.strip() for cell in stripped.split("|") if cell.strip()]
                for cell_idx, cell in enumerate(cells):
                    if cell:
                        lines.append(
                            {
                                "bbox": [
                                    cell_idx * 200,
                                    y_offset,
                                    (cell_idx + 1) * 200,
                                    y_offset + line_height,
                                ],
                                "text": cell,
                                "conf": 0.95,
                            }
                        )
                y_offset += line_height
            # Handle markdown lists (-, *, 1., etc.)
            elif stripped.startswith(("-", "*", "+")) or (
                len(stripped) > 2 and stripped[1] == "."
            ):
                text = stripped.lstrip("-*+").lstrip("0123456789.").strip()
                if text:
                    lines.append(
                        {
                            "bbox": [40, y_offset, 1000, y_offset + line_height],
                            "text": text,
                            "conf": 0.95,
                        }
                    )
                    y_offset += line_height
            # Handle headers (# ## ###)
            elif stripped.startswith("#"):
                header_level = len(stripped) - len(stripped.lstrip("#"))
                text = stripped.lstrip("#").strip()
                if text:
                    header_height = line_height + (header_level * 4)
                    lines.append(
                        {
                            "bbox": [0, y_offset, 1000, y_offset + header_height],
                            "text": text,
                            "conf": 0.95,
                        }
                    )
                    y_offset += header_height
            # Regular text line
            else:
                estimated_width = min(len(stripped) * 8, 1000)
                lines.append(
                    {
                        "bbox": [0, y_offset, estimated_width, y_offset + line_height],
                        "text": stripped,
                        "conf": 0.95,
                    }
                )
                y_offset += line_height

    return lines


api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
_rate_limit_lock = asyncio.Lock()
_request_log: DefaultDict[str, Deque[float]] = defaultdict(deque)


def ensure_upload_is_safe(file: UploadFile) -> None:
    # Check content type from header
    content_type = (file.content_type or "").lower()

    # Also check file extension as fallback (browsers sometimes send application/octet-stream)
    filename = (file.filename or "").lower()
    extension = filename.split(".")[-1] if "." in filename else ""
    allowed_extensions = {"jpg", "jpeg", "png", "webp"}

    # Allow if content type matches OR extension matches
    content_type_valid = content_type in ALLOWED_CONTENT_TYPES
    extension_valid = extension in allowed_extensions

    if not content_type_valid and not extension_valid:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Content-Type: {content_type}, Extension: {extension}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds size limit",
        )


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    # Skip API key verification in development mode
    if not REQUIRE_API_KEY:
        return api_key or SERVICE_API_KEY
    # Enforce API key in production
    if not api_key or not secrets.compare_digest(api_key, SERVICE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key


async def enforce_rate_limit(
    request: Request, api_key: str = Depends(verify_api_key)
) -> None:
    if RATE_LIMIT_REQUESTS <= 0:
        return
    identifier = api_key or (request.client.host if request.client else "anonymous")
    now = monotonic()
    async with _rate_limit_lock:
        window = _request_log[identifier]
        while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
            window.popleft()
        if len(window) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        window.append(now)


def _decode_image(file: UploadFile):
    """Decode uploaded image file to PIL Image"""
    data = file.file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Save to temp file for DeepSeek-OCR
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

    try:
        img = Image.open(tmp_path).convert("RGB")
        return img, tmp_path
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to decode image: {str(e)}",
        )


async def load_img(file: UploadFile):
    ensure_upload_is_safe(file)
    file.file.seek(0)
    img, img_path = _decode_image(file)
    return img, img_path


def _parse_json_field(name: str, raw: str, expected_type: type) -> Any:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name} payload",
        ) from exc
    if not isinstance(value, expected_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} must be a {expected_type.__name__}",
        )
    return value


def _validate_safe_json(value: Any, name: str, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} is too deeply nested",
        )
    if isinstance(value, dict):
        if len(value) > MAX_JSON_DICT_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{name} has too many keys",
            )
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 64:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{name} contains an invalid key",
                )
            _validate_safe_json(item, f"{name}.{key}", depth + 1)
        return
    if isinstance(value, list):
        if len(value) > MAX_JSON_LIST_ITEMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{name} has too many entries",
            )
        for idx, item in enumerate(value):
            _validate_safe_json(item, f"{name}[{idx}]", depth + 1)
        return
    if isinstance(value, str):
        if len(value) > MAX_JSON_STRING_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{name} contains an oversized string",
            )
        if any(ord(ch) < 32 and ch not in (9, 10, 13) for ch in value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{name} contains control characters",
            )
        return
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{name} must contain finite numbers",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{name} contains an unsupported value type",
    )


def _sanitize_label(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} must be a string",
        )
    trimmed = value.strip()
    if not trimmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} cannot be empty",
        )
    if len(trimmed) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} is too long",
        )
    if any(ord(ch) < 32 for ch in trimmed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} contains invalid characters",
        )
    return trimmed


def _parse_parent_bbox(raw: str, width: int, height: int) -> list[float]:
    values = _parse_json_field("parent_bbox", raw, list)
    if len(values) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_bbox must have four values",
        )
    coords: list[float] = []
    for value in values:
        try:
            coord = float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="parent_bbox must contain numeric values",
            ) from exc
        if not math.isfinite(coord):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="parent_bbox must contain finite coordinates",
            )
        coords.append(coord)
    x1, y1, x2, y2 = coords
    if x2 <= x1 or y2 <= y1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_bbox coordinates are invalid",
        )
    if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_bbox is outside the image bounds",
        )
    return coords


def _parse_settings(raw: str) -> dict:
    settings = _parse_json_field("settings", raw, dict)
    if len(settings) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="settings payload is too large",
        )
    _validate_safe_json(settings, "settings")
    return settings


def _parse_rules(raw: str) -> list:
    rules = _parse_json_field("rules", raw, list)
    if len(rules) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rules payload is too large",
        )
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rules entries must be objects",
            )
        _validate_safe_json(rule, f"rules[{idx}]")
    return rules


@app.options("/ocr")
async def ocr_options():
    """Handle CORS preflight requests (required by HuggingFace Spaces)"""
    return {"message": "OK"}


@app.options("/api/predict")
async def predict_options():
    """Handle CORS preflight for HuggingFace Spaces auto-routing"""
    return {"message": "OK"}


@app.post("/ocr")
@app.post("/api/predict")  # HuggingFace Spaces may auto-route POST requests here
async def ocr_page(
    file: UploadFile,
    job_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    _: None = Depends(enforce_rate_limit),
):
    """OCR endpoint using DeepSeek-OCR - supports async job processing with SSE streaming"""
    # Import progress bus
    try:
        from progress_bus import bus
    except ImportError:
        # Fallback if progress_bus not available
        bus = None

    # Generate job_id if not provided
    if not job_id:
        if bus:
            job_id = bus.new_job()
        else:
            job_id = secrets.token_urlsafe(16)

    # Initialize job status (for polling compatibility)
    async with _jobs_lock:
        _jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "message": "Initializing...",
            "result": None,
            "error": None,
        }
        _cancellation_tokens[job_id] = asyncio.Event()

    # Start background task for async processing
    if background_tasks and bus:
        # Async mode: return job_id immediately, process in background
        background_tasks.add_task(run_ocr_job_async, job_id, file, bus)
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Job started - use /progress/{job_id} for SSE or /jobs/{job_id}/status for polling",
        }

    # Synchronous mode: process immediately
    img, img_path = await load_img(file)

    try:
        # Save PIL image to temporary file for DeepSeek-OCR
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            img.save(tmp_file, "JPEG", quality=95)
            tmp_img_path = tmp_file.name

        try:
            # Progress callback to update job status (async-safe)
            async def update_progress(progress: float, message: str):
                async with _jobs_lock:
                    if job_id in _jobs:
                        _jobs[job_id]["progress"] = progress
                        _jobs[job_id]["message"] = message

                # Also send to SSE bus if available
                if bus:
                    await bus.send(
                        job_id,
                        pct=progress * 100,
                        stage=message.lower().replace(" ", "_"),
                    )

            # Start OCR processing (can be cancelled)
            await update_progress(0.0, "Starting OCR...")

            # Check for cancellation before processing
            cancel_event = _cancellation_tokens.get(job_id)
            if cancel_event and cancel_event.is_set():
                async with _jobs_lock:
                    _jobs[job_id]["status"] = "cancelled"
                    _jobs[job_id]["message"] = "Job was cancelled"
                raise HTTPException(status_code=499, detail="Job was cancelled")

            # Use grounding prompt for better structure extraction
            result = await run_deepseek_ocr(
                tmp_img_path,
                prompt="<image>\n<|grounding|>Convert the document to markdown with preserved layout.",
                use_grounding=True,
                job_id=job_id,
                progress_callback=update_progress,
            )

            # Update job with result
            async with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "completed"
                    _jobs[job_id]["progress"] = 1.0
                    _jobs[job_id]["result"] = result
                    _jobs[job_id]["message"] = "Complete"

            # Finalize SSE stream if available
            if bus:
                await bus.finalize(job_id, pct=100, stage="done", **result)

            return {"job_id": job_id, **result}
        except asyncio.CancelledError as e:
            # Job was cancelled
            async with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "cancelled"
                    _jobs[job_id]["message"] = "Job was cancelled"
                _cancellation_tokens.pop(job_id, None)
                remove_cancel_flag(job_id)  # Cleanup cancel registry
            raise HTTPException(status_code=499, detail="Job was cancelled")
        except Exception as e:
            # Log the error and update job status
            error_msg = str(e)
            print(f"OCR processing error: {error_msg}")

            async with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "failed"
                    _jobs[job_id]["error"] = error_msg
                    _jobs[job_id]["message"] = f"Error: {error_msg}"

            # Check if it's a model loading issue
            if (
                "matplotlib" in error_msg
                or "torchvision" in error_msg
                or "ImportError" in error_msg
            ):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"OCR model dependencies missing: {error_msg}. Please install required packages.",
                )
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"OCR service temporarily unavailable: {error_msg}",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OCR processing failed: {error_msg}",
                )
        finally:
            if os.path.exists(tmp_img_path):
                os.unlink(tmp_img_path)
    finally:
        if os.path.exists(img_path):
            os.unlink(img_path)


async def run_ocr_job_async(job_id: str, file: UploadFile, bus):
    """Background task to run OCR job with SSE updates"""
    img_path = None
    tmp_img_path = None

    try:
        # Update progress: Decode (0-5%)
        await bus.send(job_id, pct=1, stage="queued")

        img, img_path = await load_img(file)
        await bus.send(job_id, pct=5, stage="decode")

        # Save PIL image to temporary file for DeepSeek-OCR
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            img.save(tmp_file, "JPEG", quality=95)
            tmp_img_path = tmp_file.name

        # Update progress: Preprocess (5-20%)
        async with _jobs_lock:
            if job_id not in _jobs:
                return  # Job was cancelled before starting
            _jobs[job_id]["progress"] = 0.05
            _jobs[job_id]["message"] = "Preprocessing image..."

        await bus.send(job_id, pct=20, stage="preprocess")

        # Progress callback that updates both job status and SSE
        async def update_progress(progress: float, message: str):
            # Update job status
            async with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["progress"] = progress
                    _jobs[job_id]["message"] = message

            # Send to SSE stream
            pct = progress * 100
            stage_map = {
                "preprocessing": "preprocess",
                "starting ocr inference": "encoding",
                "parsing ocr results": "postprocess",
                "cleaning output": "postprocess",
                "complete": "done",
            }
            stage = stage_map.get(message.lower(), message.lower().replace(" ", "_"))
            await bus.send(job_id, pct=pct, stage=stage, msg=message)

        # Check for cancellation
        async with _jobs_lock:
            cancel_event = _cancellation_tokens.get(job_id)
            if cancel_event and cancel_event.is_set():
                await bus.error(job_id, "Job was cancelled")
                return

        # Run OCR
        result = await run_deepseek_ocr(
            tmp_img_path,
            prompt="<image>\n<|grounding|>Convert the document to markdown with preserved layout.",
            use_grounding=True,
            job_id=job_id,
            progress_callback=update_progress,
        )

        # Update job status
        async with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["progress"] = 1.0
                _jobs[job_id]["result"] = result
                _jobs[job_id]["message"] = "Complete"

        # Finalize SSE stream
        await bus.finalize(job_id, pct=100, stage="done", **result)

    except asyncio.CancelledError:
        async with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "cancelled"
                _jobs[job_id]["message"] = "Job was cancelled"
        await bus.error(job_id, "Job was cancelled")
    except Exception as e:
        error_msg = str(e)
        async with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = error_msg
                _jobs[job_id]["message"] = f"Error: {error_msg}"
        await bus.error(job_id, error_msg)
    finally:
        # Cleanup temp files
        if tmp_img_path and os.path.exists(tmp_img_path):
            os.unlink(tmp_img_path)
        if img_path and os.path.exists(img_path):
            os.unlink(img_path)


@app.get("/progress/{job_id}")
async def get_progress_stream(job_id: str, request: Request):
    """SSE stream for real-time OCR progress updates with client disconnect detection"""
    try:
        from progress_bus import bus
    except ImportError:
        raise HTTPException(status_code=503, detail="SSE streaming not available")

    async def gen_with_disconnect_check():
        """Generator that checks for client disconnect and auto-cancels"""
        try:
            async for event in bus.stream(job_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    # Auto-cancel job on disconnect (optional but recommended)
                    cancel_job(job_id)
                    if job_id in _cancellation_tokens:
                        _cancellation_tokens[job_id].set()
                    async with _jobs_lock:
                        if job_id in _jobs:
                            _jobs[job_id]["status"] = "cancelled"
                            _jobs[job_id]["message"] = "Client disconnected"
                    break
                yield event
        except asyncio.CancelledError:
            # Stream was cancelled
            cancel_job(job_id)
            if job_id in _cancellation_tokens:
                _cancellation_tokens[job_id].set()

    return StreamingResponse(
        gen_with_disconnect_check(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status of an OCR job (polling endpoint)"""
    async with _jobs_lock:
        if job_id not in _jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        job = _jobs[job_id]
        return {
            "job_id": job_id,
            "status": job["status"],  # processing, completed, failed, cancelled
            "progress": job["progress"],  # 0.0 to 1.0
            "message": job["message"],
            "result": job.get("result"),
            "error": job.get("error"),
        }


@app.post("/jobs/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    """Cancel a running OCR job (cooperative cancellation with StoppingCriteria)"""
    async with _jobs_lock:
        if job_id not in _jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job = _jobs[job_id]

        # Already finished?
        if job["status"] in ("completed", "failed", "cancelled"):
            return {
                "ok": True,
                "message": f"Job already {job['status']}",
                "job_id": job_id,
            }

        # Set cancellation flag (use cancel_registry for consistency)
        cancel_job(job_id)
        if job_id in _cancellation_tokens:
            _cancellation_tokens[job_id].set()

        job["status"] = "cancelled"
        job["message"] = "Cancellation requested..."
        job["progress"] = job.get("progress", 0.0)

        # Send cancellation to SSE stream
        try:
            from progress_bus import bus

            await bus.error(job_id, "Job cancelled by user")
        except ImportError:
            pass

        return {"ok": True, "message": "Cancellation requested", "job_id": job_id}


@app.post("/split")
async def split(
    file: UploadFile,
    parent_bbox: str = Form(...),
    splitter: str = Form(...),
    schemaType: str = Form(...),
    settings: str = Form("{}"),
    rules: str = Form("[]"),
    _: None = Depends(enforce_rate_limit),
):
    """Split endpoint - uses DeepSeek-OCR for region extraction"""
    img, img_path = await load_img(file)
    try:
        width, height = img.size

        # Save image for DeepSeek-OCR
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            img.save(tmp_file, "JPEG", quality=95)
            tmp_img_path = tmp_file.name

        try:
            parent_box = _parse_parent_bbox(parent_bbox, width, height)
            x1, y1, x2, y2 = parent_box

            # Crop image to parent bbox
            crop_img = img.crop((int(x1), int(y1), int(x2), int(y2)))
            crop_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            crop_img.save(crop_path, "JPEG", quality=95)

            try:
                # Use DeepSeek-OCR with grounding prompt for better structured extraction
                prompt = "<image>\n<|grounding|>Convert the document region to markdown with preserved layout."
                ocr_result = await run_deepseek_ocr(
                    crop_path, prompt=prompt, use_grounding=True, detect_fields=False
                )

                # Parse OCR result to extract lines
                child_lines = ocr_result.get("lines", [])

                # Adjust bboxes to parent coordinate space
                for line in child_lines:
                    bbox = line["bbox"]
                    line["bbox"] = [
                        bbox[0] + x1,
                        bbox[1] + y1,
                        bbox[2] + x1,
                        bbox[3] + y1,
                    ]
                    line["blockType"] = "text"

                if len(child_lines) > MAX_CHILD_LINES:
                    child_lines = child_lines[:MAX_CHILD_LINES]

                sanitized_splitter = _sanitize_label("splitter", splitter)
                sanitized_schema = _sanitize_label("schemaType", schemaType)
                parsed_settings = _parse_settings(settings)
                parsed_rules = _parse_rules(rules)

                raw_text = "\n".join([l["text"] for l in child_lines])
                text_truncated = False
                if len(raw_text) > 5000:
                    raw_text = raw_text[:5000]
                    text_truncated = True

                llm_input = {
                    "schemaType": sanitized_schema,
                    "splitter": sanitized_splitter,
                    "page": {"width": width, "height": height},
                    "parentBox": parent_box,
                    "rawText": raw_text,
                    "ocrLines": child_lines,
                    "rawTextTruncated": text_truncated,
                    "ocrLinesTruncated": len(child_lines) >= MAX_CHILD_LINES,
                    "settings": parsed_settings,
                    "rules": parsed_rules,
                }

                try:
                    llm_result = await call_llm_splitter(llm_input)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=str(exc),
                    ) from exc
                return llm_result
            finally:
                if os.path.exists(crop_path):
                    os.unlink(crop_path)
        finally:
            if os.path.exists(tmp_img_path):
                os.unlink(tmp_img_path)
    finally:
        if os.path.exists(img_path):
            os.unlink(img_path)
