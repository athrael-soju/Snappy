import base64
import json
import logging
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

LOGGER = logging.getLogger(__name__)


class PaddleOCRService:
    """Client for interacting with the upstream PaddleOCR-VL service."""

    def __init__(self, base_url: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        session = requests.Session()
        # adapter = requests.adapters.HTTPAdapter(max_retries=3)
        # session.mount("http://", adapter)
        # session.mount("https://", adapter)
        self.session = session

    def layout_parsing(
        self,
        content: bytes,
        *,
        file_type: int = 1,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "file": base64.b64encode(content).decode("utf-8"),
            "fileType": file_type,
        }
        if options:
            payload.update(options)

        url = f"{self.base_url}/layout-parsing"
        response = self.session.post(url, json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PaddleOCR upstream error: {response.text}",
            )
        try:
            return response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail="Upstream PaddleOCR returned invalid JSON.",
            ) from exc

    def health_check(self) -> bool:
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False


class LayoutParsingResponse(BaseModel):
    lines: List[str] = Field(
        default_factory=list,
        description="Flattened list of recognised text segments.",
    )
    full_text: str = Field(
        "",
        description="Convenience aggregation (newline separated).",
    )
    raw: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw payload returned by PaddleOCR.",
    )


def extract_text(response_payload: Mapping[str, Any]) -> List[str]:
    result = response_payload.get("result", {})
    layout_items: Iterable[Mapping[str, Any]] = result.get("layoutParsingResults", [])
    collected: List[str] = []
    for item in layout_items:
        pruned = item.get("prunedResult", [])
        if isinstance(pruned, Sequence):
            source = pruned
        else:
            source = []
        for block in source:
            if not isinstance(block, Mapping):
                continue
            candidates: Iterable[str] = []
            if "text" in block and isinstance(block["text"], str):
                candidates = [block["text"]]
            elif "ocrResult" in block and isinstance(block["ocrResult"], Mapping):
                rows = block["ocrResult"].get("result", [])
                candidates = [
                    row.get("text", "")
                    for row in rows
                    if isinstance(row, Mapping) and isinstance(row.get("text"), str)
                ]
            elif "res" in block and isinstance(block["res"], Mapping):
                text_val = block["res"].get("text")
                if isinstance(text_val, str):
                    candidates = [text_val]
            for candidate in candidates:
                candidate = candidate.strip()
                if candidate:
                    collected.append(candidate)
    return collected


PADDLEOCR_UPSTREAM_URL = os.getenv(
    "PADDLEOCR_UPSTREAM_URL", "http://paddleocr-upstream:8118"
)
PADDLEOCR_API_TIMEOUT = int(os.getenv("PADDLEOCR_API_TIMEOUT", "120"))
ALLOW_ORIGINS = os.getenv("PADDLEOCR_ALLOW_ORIGINS", "*")

app = FastAPI(
    title="PaddleOCR-VL Proxy",
    version="1.0.0",
    description="Thin FastAPI proxy that forwards requests to the upstream PaddleOCR-VL server and adds an interactive OpenAPI UI.",
)

if ALLOW_ORIGINS:
    allow_origins = (
        ["*"]
        if ALLOW_ORIGINS.strip() == "*"
        else [o.strip() for o in ALLOW_ORIGINS.split(",")]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=(ALLOW_ORIGINS.strip() != "*"),
    )

service = PaddleOCRService(
    base_url=PADDLEOCR_UPSTREAM_URL, timeout=PADDLEOCR_API_TIMEOUT
)


@app.get("/health", tags=["meta"])
def health() -> Dict[str, bool]:
    return {"paddleocr_upstream": service.health_check()}


@app.post(
    "/layout-parsing",
    response_model=LayoutParsingResponse,
    tags=["ocr"],
    summary="Run PaddleOCR layout parsing",
)
async def layout_parsing(
    file: UploadFile = File(..., description="Image or PDF page to analyse."),
    file_type: int = Form(
        1, description="Upstream file type flag (default: 1 for images)."
    ),
    options: Optional[str] = Form(
        None,
        description="Optional JSON string with extra PaddleOCR parameters.",
    ),
) -> LayoutParsingResponse:
    payload = await file.read()
    if not payload:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )
    options_payload: Optional[Dict[str, Any]] = None
    if options:
        try:
            parsed = json.loads(options)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON for 'options': {exc}",
            ) from exc
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=400,
                detail="'options' must decode to a JSON object.",
            )
        options_payload = parsed

    try:
        raw = service.layout_parsing(
            payload,
            file_type=file_type,
            options=options_payload,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("PaddleOCR proxy request failed: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"PaddleOCR proxy request failed: {exc}"
        ) from exc
    lines = extract_text(raw)
    return LayoutParsingResponse(
        lines=lines,
        full_text="\n".join(lines),
        raw=raw,
    )
