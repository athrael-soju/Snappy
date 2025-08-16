import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.models import ChatRequest, ChatResponse
from api.utils import encode_pil_to_data_url, format_page_labels
from clients.openai import OpenAIClient as OpenAI
from config import OPENAI_SYSTEM_PROMPT

router = APIRouter(prefix="", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Retrieval first (with metadata)
    k = int(req.k or 5)
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
                    "image_url": {"url": encode_pil_to_data_url(img), "detail": "low"},
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
                "label": it.get("label"),
                "payload": it.get("payload", {}),
                "score": it.get("score"),
            }
            for it in items
        ]
        return ChatResponse(text="AI responses are disabled.", images=images)

    # Build chat
    chat_history = [m.model_dump() for m in (req.chat_history or [])]
    user_message_with_labels = "\n".join(
        [
            str(req.message),
            "",
            "[Retrieved pages]",
            format_page_labels(items, k),
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
            messages=messages, temperature=req.temperature
        ):
            if content:
                text += content
    except Exception as e:
        if not text:
            raise HTTPException(status_code=500, detail=f"Streaming error: {e}")

    images = [
        {
            "image_url": it.get("payload", {}).get("image_url"),
            "label": it.get("label"),
            "payload": it.get("payload", {}),
            "score": it.get("score"),
        }
        for it in items
    ]
    return ChatResponse(text=text, images=images)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    # Retrieval first (with metadata)
    k = int(req.k or 5)
    svc = get_qdrant_service()
    if not svc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
        )
    items = svc.search_with_metadata(str(req.message), k=k)

    image_parts = []
    for it in items[:k]:
        img = it.get("image")
        try:
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": encode_pil_to_data_url(img), "detail": "low"},
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
                "label": it.get("label"),
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
            format_page_labels(items, k),
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
            ):
                if content:
                    yield content
        except Exception as e:
            yield f"\n[Streaming error: {e}]"

    return StreamingResponse(token_generator(), media_type="text/plain")
