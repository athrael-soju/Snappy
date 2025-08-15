import os
import io
import base64
import tempfile
from typing import Any, Dict, List, Optional
import uvicorn

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from pdf2image import convert_from_path

from clients.colpali import ColPaliClient
from clients.openai import OpenAIClient as OpenAI
from clients.qdrant import QdrantService
from clients.minio import MinioService
from util.labeling import compute_page_label
from config import (
    DEFAULT_TOP_K,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_SYSTEM_PROMPT,
    WORKER_THREADS,
)


# -------- Helpers --------


def _encode_pil_to_data_url(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _convert_pdf_paths_to_images(paths: List[str]) -> List[dict]:
    items: List[dict] = []
    for f in paths:
        try:
            pages = convert_from_path(f, thread_count=int(WORKER_THREADS))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to convert PDF {f}: {e}"
            )
        total = len(pages)
        try:
            size_bytes = os.path.getsize(f)
        except Exception:
            size_bytes = None
        filename = os.path.basename(str(f))
        for idx, img in enumerate(pages):
            w, h = (img.size[0], img.size[1]) if hasattr(img, "size") else (None, None)
            items.append(
                {
                    "image": img,
                    "filename": filename,
                    "file_size_bytes": size_bytes,
                    "pdf_page_index": idx + 1,  # 1-based
                    "total_pages": total,
                    "page_width_px": w,
                    "page_height_px": h,
                }
            )
    return items


# -------- Data models --------


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []
    k: Optional[int] = DEFAULT_TOP_K
    ai_enabled: Optional[bool] = True
    temperature: Optional[float] = OPENAI_TEMPERATURE
    model: Optional[str] = OPENAI_MODEL
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    images: List[Dict[str, Any]]


class SearchItem(BaseModel):
    image_url: Optional[str]
    label: Optional[str]
    payload: Dict[str, Any]
    score: Optional[float] = None


# -------- App / Services --------

api_client = ColPaliClient()

qdrant_service = None
qdrant_init_error: Optional[str] = None

minio_service = None
minio_init_error: Optional[str] = None

app = FastAPI(title="Vision RAG API", version="1.0.0")

# CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Routes --------


@app.get("/", tags=["meta"])
async def root():
    return {
        "name": "Vision RAG API",
        "endpoints": [
            "/health",
            "/search",
            "/chat",
            "/chat/stream",
            "/index",
            "/clear/*",
        ],
    }


@app.get("/health", tags=["meta"])
async def health():
    colpali_ok = False
    minio_ok = False
    qdrant_ok = False
    try:
        colpali_ok = bool(api_client.health_check())
    except Exception:
        colpali_ok = False
    try:
        msvc = get_minio_service()
        minio_ok = bool(msvc and msvc.health_check())
    except Exception:
        minio_ok = False
    try:
        qsvc = get_qdrant_service()
        qdrant_ok = bool(qsvc and qsvc.health_check())
    except Exception:
        qdrant_ok = False
    overall = colpali_ok and minio_ok and qdrant_ok
    response = {
        "status": "ok" if overall else "degraded",
        "colpali": colpali_ok,
        "minio": minio_ok,
        "qdrant": qdrant_ok,
    }
    if qdrant_init_error:
        response["qdrant_init_error"] = qdrant_init_error
    if minio_init_error:
        response["minio_init_error"] = minio_init_error
    return response


def get_qdrant_service() -> QdrantService:
    global qdrant_service, qdrant_init_error
    if qdrant_service is None:
        try:
            qdrant_service = QdrantService(api_client=api_client, minio_service=get_minio_service())
            qdrant_init_error = None
        except Exception as e:
            qdrant_service = None
            qdrant_init_error = str(e)
    return qdrant_service


def get_minio_service() -> MinioService:
    global minio_service, minio_init_error
    if minio_service is None:
        try:
            minio_service = MinioService()
            minio_init_error = None
        except Exception as e:
            minio_service = None
            minio_init_error = str(e)
    return minio_service


@app.get("/search", response_model=List[SearchItem], tags=["retrieval"])
async def search(
    q: str = Query(..., description="User query"),
    k: int = Query(DEFAULT_TOP_K, ge=1, le=50),
):
    svc = get_qdrant_service()
    if not svc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )
    items = svc.search_with_metadata(q, k=k)
    results: List[SearchItem] = []
    for it in items:
        payload = it.get("payload", {})
        label = compute_page_label(payload)
        image_url = payload.get("image_url")
        results.append(
            SearchItem(
                image_url=image_url,
                label=label,
                payload=payload,
                score=it.get("score"),
            )
        )
    return results


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest):
    # Retrieval first (with metadata)
    k = int(req.k or DEFAULT_TOP_K)
    svc = get_qdrant_service()
    if not svc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )
    items = svc.search_with_metadata(str(req.message), k=k)
    # Prepare image parts for multimodal
    image_parts = []
    for it in items[:k]:
        img = it.get("image")
        try:
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _encode_pil_to_data_url(img), "detail": "low"},
                }
            )
        except Exception:
            continue

    system_prompt = (req.system_prompt or OPENAI_SYSTEM_PROMPT).strip()

    # If AI disabled, return only retrieval results
    if not req.ai_enabled:
        images = [
            {
                "image_url": it.get("payload", {}).get("image_url"),
                "label": compute_page_label(it.get("payload", {})),
                "payload": it.get("payload", {}),
                "score": it.get("score"),
            }
            for it in items
        ]
        return ChatResponse(text="AI responses are disabled.", images=images)

    # Build chat
    chat_history = [m.dict() for m in (req.chat_history or [])]
    user_message_with_labels = "\n".join(
        [
            str(req.message),
            "",
            "[Retrieved pages]",
            "\n".join(
                [
                    f"{idx+1}) {compute_page_label(it.get('payload', {}))}"
                    for idx, it in enumerate(items[:k])
                ]
            ),
            "",
            "Cite pages using the labels above (do not infer by result order).",
        ]
    )

    messages = OpenAI.build_messages(
        chat_history=chat_history,
        system_prompt=system_prompt,
        user_message=user_message_with_labels,
        image_parts=image_parts,
    )

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Aggregate streamed content into final string
    text = ""
    try:
        for content in client.stream_chat(
            messages=messages,
            temperature=req.temperature,
            model=(req.model or OPENAI_MODEL),
        ):
            if content:
                text += content
    except Exception as e:
        if not text:
            raise HTTPException(status_code=500, detail=f"Streaming error: {e}")

    images = [
        {
            "image_url": it.get("payload", {}).get("image_url"),
            "label": compute_page_label(it.get("payload", {})),
            "payload": it.get("payload", {}),
            "score": it.get("score"),
        }
        for it in items
    ]
    return ChatResponse(text=text, images=images)


@app.post("/chat/stream", tags=["chat"])
async def chat_stream(req: ChatRequest):
    # Retrieval first (with metadata)
    k = int(req.k or DEFAULT_TOP_K)
    items = get_qdrant_service().search_with_metadata(str(req.message), k=k)

    image_parts = []
    for it in items[:k]:
        img = it.get("image")
        try:
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _encode_pil_to_data_url(img), "detail": "low"},
                }
            )
        except Exception:
            continue

    system_prompt = (req.system_prompt or OPENAI_SYSTEM_PROMPT).strip()

    if not req.ai_enabled:
        # Non-streaming JSON if AI disabled
        images = [
            {
                "image_url": it.get("payload", {}).get("image_url"),
                "label": compute_page_label(it.get("payload", {})),
                "payload": it.get("payload", {}),
                "score": it.get("score"),
            }
            for it in items
        ]
        return JSONResponse({"text": "AI responses are disabled.", "images": images})

    chat_history = [m.dict() for m in (req.chat_history or [])]
    user_message_with_labels = "\n".join(
        [
            str(req.message),
            "",
            "[Retrieved pages]",
            "\n".join(
                [
                    f"{idx+1}) {compute_page_label(it.get('payload', {}))}"
                    for idx, it in enumerate(items[:k])
                ]
            ),
            "",
            "Cite pages using the labels above (do not infer by result order).",
        ]
    )

    messages = OpenAI.build_messages(
        chat_history=chat_history,
        system_prompt=system_prompt,
        user_message=user_message_with_labels,
        image_parts=image_parts,
    )

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    def token_generator():
        try:
            for content in client.stream_chat(
                messages=messages,
                temperature=req.temperature,
                model=(req.model or OPENAI_MODEL),
            ):
                if content:
                    yield content
        except Exception as e:
            yield f"\n[Streaming error: {e}]"

    return StreamingResponse(token_generator(), media_type="text/plain")


@app.post("/index", tags=["indexing"])
async def index(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths: List[str] = []
    try:
        for uf in files:
            # Persist to a temporary file so pdf2image can read
            suffix = os.path.splitext(uf.filename or "")[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                data = await uf.read()
                tmp.write(data)
                temp_paths.append(tmp.name)

        images_with_meta = _convert_pdf_paths_to_images(temp_paths)
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )
        message = svc.index_documents(images_with_meta)
        return {"status": "ok", "message": message, "pages": len(images_with_meta)}
    finally:
        for p in temp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass


@app.post("/clear/qdrant", tags=["maintenance"])
async def clear_qdrant():
    try:
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )
        msg = svc.clear_collection()
        return {"status": "ok", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear/minio", tags=["maintenance"])
async def clear_minio():
    try:
        msvc = get_minio_service()
        if not msvc:
            raise HTTPException(
                status_code=503,
                detail=f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}",
            )
        res = msvc.clear_images()
        return {
            "status": "ok",
            "deleted": res.get("deleted"),
            "failed": res.get("failed"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear/all", tags=["maintenance"])
async def clear_all():
    try:
        # Clear Qdrant (if available)
        q_msg = ""
        svc = get_qdrant_service()
        if svc:
            try:
                q_msg = svc.clear_collection()
            except Exception as qe:
                q_msg = f"Qdrant clear failed: {qe}"
        else:
            q_msg = f"Qdrant unavailable: {qdrant_init_error or 'Dependency service is down'}"

        # Clear MinIO (independent of Qdrant)
        m_msg = ""
        msvc = get_minio_service()
        if msvc:
            try:
                res = msvc.clear_images()
                m_msg = f"Cleared MinIO images: deleted={res.get('deleted')}, failed={res.get('failed')}"
            except Exception as me:
                m_msg = f"MinIO clear failed: {me}"
        else:
            m_msg = (
                f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}"
            )

        return {"status": "ok", "message": f"{q_msg} {m_msg}".strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except Exception:
        raise ValueError("Invalid PORT")
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    uvicorn.run("fastapi_app:app", host=host, port=port, log_level=log_level, reload=True)
