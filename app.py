import os
import io
import base64
import gradio as gr
from pdf2image import convert_from_path
from typing import Any, List, Optional, Sequence, Union

# OpenAI SDK (streaming)
try:
    from openai import OpenAI
except Exception:  # fallback for environments with old SDK
    OpenAI = None

# Client wrapper for OpenAI (preferred)
from clients.openai import OpenAIClient as OpenAI

# Your clients / config
from clients.colqwen import ColQwenAPIClient
from config import WORKER_THREADS
from ui import build_ui

# Initialize storage backend (Qdrant only)
from clients.qdrant import QdrantService

api_client = ColQwenAPIClient()
qdrant_service = QdrantService(api_client)


# -----------------------
# Core functions (unchanged behavior)
# -----------------------
def _retrieve_results(query: str, k: Union[int, str]) -> List[Any]:
    """Retrieve top-k page images for the query from Qdrant."""
    try:
        k = int(k)
        if k <= 0:
            k = 5
    except Exception:
        k = 5

    results = qdrant_service.search(query, k=k)
    return results


def _encode_pil_to_data_url(img) -> str:
    """Encode a PIL.Image to a data URL suitable for OpenAI vision input."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _build_openai_messages(
    chat_history: List[dict],
    system_prompt: str,
    user_message: str,
    image_parts: List[dict],
):
    """Construct OpenAI messages for a single turn (history ignored).

    - Intentionally ignores prior user/assistant turns.
    - Sends only the system prompt and the current user turn with optional image parts.
    """
    messages = [{"role": "system", "content": str(system_prompt)}]

    messages.append(
        {
            "role": "user",
            "content": (
                ([{"type": "text", "text": str(user_message)}] + image_parts)
                if image_parts
                else str(user_message)
            ),
        }
    )
    return messages


def on_chat_submit(
    message, chat_history, k, ai_enabled, temperature, system_prompt_input
):
    """Stream a reply from OpenAI using retrieved page images as multimodal context.

    Chat uses messages-format (list of dicts with 'role' and 'content').
    Accepts user-configurable AI settings: `temperature` and `system_prompt_input`.
    Yields tuples: (cleared_input, updated_chat, gallery_images)
    """
    # No-op on empty input
    if not message or not str(message).strip():
        yield gr.update(), chat_history, gr.update()
        return

    # If AI responses are disabled, only retrieve and show pages
    if not ai_enabled:
        results = _retrieve_results(message, k)
        updated_chat = list(chat_history or [])
        updated_chat.append({"role": "user", "content": str(message)})
        updated_chat.append(
            {
                "role": "assistant",
                "content": "AI responses are disabled. Enable them in the sidebar to get answers. Showing retrieved pages only.",
            }
        )
        yield "", updated_chat, results
        return

    # Initialize OpenAI client (wrapper handles SDK/key validation)
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        updated_chat = list(chat_history or [])
        updated_chat.append({"role": "user", "content": str(message)})
        updated_chat.append({"role": "assistant", "content": str(e)})
        yield "", updated_chat, gr.update()
        return

    # Retrieve images (top-k)
    results = _retrieve_results(message, k)

    # Show gallery and insert a temporary thinking bubble at the exact reply location
    updated_chat = list(chat_history or [])
    updated_chat.append({"role": "user", "content": str(message)})
    updated_chat.append({"role": "assistant", "content": "⏳ Generating…"})
    yield "", updated_chat, results

    # Build multimodal user content: text + top-k images
    image_parts = []
    for item in (results or [])[: int(k) if str(k).isdigit() else 5]:
        # Support either raw PIL images or (image, caption) tuples
        img = item[0] if isinstance(item, (tuple, list)) and item else item
        try:
            image_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _encode_pil_to_data_url(img), "detail": "low"},
                }
            )
        except Exception:
            # Skip any image that fails to encode
            continue

    default_system_prompt = (
        "You are a helpful PDF assistant. Use only the provided page images "
        "to answer the user's question. If the answer isn't contained in the pages, "
        "say you cannot find it. Be concise and always mention from which pages the answer is taken."
    )

    system_prompt = (
        str(system_prompt_input).strip()
        if system_prompt_input and str(system_prompt_input).strip()
        else default_system_prompt
    )

    messages = OpenAI.build_messages(chat_history, system_prompt, str(message), image_parts)

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    # client already initialized above

    # Coerce temperature
    try:
        temp = float(temperature)
    except Exception:
        temp = 0.7

    # Stream tokens via wrapper
    assistant_text = ""
    streamed_any = False
    try:
        for content in client.stream_chat(messages=messages, temperature=temp, model=model):
            if content:
                if not streamed_any:
                    assistant_text = content
                    updated_chat[-1] = {"role": "assistant", "content": assistant_text}
                    streamed_any = True
                else:
                    assistant_text += content
                    updated_chat[-1] = {"role": "assistant", "content": assistant_text}
                # Stream updated chat; gallery unchanged
                yield "", updated_chat, gr.update()
    except Exception as e:
        # Replace the thinking bubble with a single error message
        err_text = assistant_text or f"[Streaming error: {e}]"
        updated_chat[-1] = {"role": "assistant", "content": err_text}
        yield "", updated_chat, gr.update()


def index_wrapper(files, progress=gr.Progress(track_tqdm=True)):
    """Index documents in Qdrant with a progress bar.

    Gradio will track the internal tqdm in QdrantService.index_documents().
    """
    images_with_meta = convert_files(files)
    total = len(images_with_meta)
    # Optional initial progress message (tqdm will take over)
    try:
        progress(0, total=total, desc="Indexing pages…")
    except Exception:
        pass
    message = qdrant_service.index_documents(images_with_meta)
    return f"{message} (total: {total} pages)"


def convert_files(files):
    """Convert uploaded PDFs to page images and attach per-page metadata.

    Returns a list of dicts: { 'image': PIL.Image, 'filename': str,
    'file_size_bytes': int, 'pdf_page_index': int, 'total_pages': int,
    'page_width_px': int, 'page_height_px': int }
    """
    items: List[dict] = []
    file_list = [files] if not isinstance(files, list) else files
    for f in file_list:
        try:
            pages = convert_from_path(f, thread_count=int(WORKER_THREADS))
        except Exception:
            # Skip non-PDFs or conversion failures silently for now
            continue
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


# -----------------------
# UI
# -----------------------
demo = build_ui(on_chat_submit, index_wrapper)

# Entrypoint to run the Gradio app directly
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "7860"))
    except Exception:
        raise ValueError("Invalid port")
    demo.queue().launch(server_name=host, server_port=port)
