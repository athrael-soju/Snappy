import os
import io
import base64
import gradio as gr
from gradio_pdf import PDF
from pdf2image import convert_from_path

# OpenAI SDK (streaming)
try:
    from openai import OpenAI
except Exception:  # fallback for environments with old SDK
    OpenAI = None

# Your services / config
from services.colqwen_api_client import ColQwenAPIClient
from config import STORAGE_TYPE, WORKER_THREADS, IN_MEMORY_NUM_IMAGES

# Storage backends (lazy-imported below based on STORAGE_TYPE)
memory_store_service = None
qdrant_service = None

# Initialize API client
api_client = ColQwenAPIClient()

if STORAGE_TYPE == "memory":
    from services.memory_store import MemoryStoreService

    memory_store_service = MemoryStoreService(api_client)
elif STORAGE_TYPE == "qdrant":
    from services.qdrant_store import QdrantService

    qdrant_service = QdrantService(api_client)
else:
    raise ValueError("Invalid storage type")


# -----------------------
# Core functions (unchanged behavior)
# -----------------------
def _retrieve_results(query: str, ds, images, k):
    """Retrieve top-k page images for the query from the selected store."""
    try:
        k = int(k)
    except Exception:
        k = 5

    if STORAGE_TYPE == "memory":
        results = memory_store_service.search(query, ds, images, k)
    elif STORAGE_TYPE == "qdrant":
        results = qdrant_service.search(query, k=k)
    else:
        results = []
    return results


def _encode_pil_to_data_url(img):
    """Encode a PIL.Image to a data URL suitable for OpenAI vision input."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def on_chat_submit(message, chat_history, ds, images, k, ai_enabled):
    """Stream a reply from OpenAI using retrieved page images as multimodal context.

    Yields tuples: (cleared_input, updated_chat, gallery_images)
    """
    # No-op on empty input
    if not message or not str(message).strip():
        yield gr.update(), chat_history, gr.update()
        return

    # If AI responses are disabled, only retrieve and show pages
    if not ai_enabled:
        results = _retrieve_results(message, ds, images, k)
        updated_chat = (chat_history or []) + [
            (
                message,
                "AI responses are disabled. Enable them in the sidebar to get answers. Showing retrieved pages only.",
            )
        ]
        yield "", updated_chat, results
        return

    # Resolve API key from environment only
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key or OpenAI is None:
        # Inform user about missing dependency or key
        err = (
            "OpenAI SDK not available or API key missing. "
            "Please install the 'openai' package and set OPENAI_API_KEY in your environment."
        )
        updated_chat = (chat_history or []) + [(message, err)]
        yield "", updated_chat, gr.update()
        return

    # Retrieve images (top-k)
    results = _retrieve_results(message, ds, images, k)

    # Prepend an empty assistant message to stream into
    updated_chat = (chat_history or []) + [(message, "")]  # assistant will stream here

    # Show retrieved images immediately
    yield "", updated_chat, results

    # Build multimodal user content: text + top-k images
    image_parts = []
    for img in (results or [])[: int(k) if str(k).isdigit() else 5]:
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

    system_prompt = (
        "You are a helpful PDF assistant. Use only the provided page images "
        "to answer the user's question. If the answer isn't contained in the pages, "
        "say you cannot find it. Be concise."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                ([{"type": "text", "text": str(message)}] + image_parts)
                if image_parts
                else str(message)
            ),
        },
    ]

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    # Stream tokens
    assistant_text = ""
    try:
        for chunk in client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        ):
            delta = chunk.choices[0].delta
            content = (
                getattr(delta, "content", None)
                if hasattr(delta, "content")
                else delta.get("content")
            )
            if content:
                assistant_text += content
                updated_chat[-1] = (message, assistant_text)
                # Stream updated chat; gallery unchanged
                yield "", updated_chat, gr.update()
    except Exception as e:
        assistant_text = assistant_text or f"[Streaming error: {e}]"
        updated_chat[-1] = (message, assistant_text)
        yield "", updated_chat, gr.update()


def index_wrapper(files, ds):
    """Wrapper function to select between in-memory and Qdrant indexing"""
    images = convert_files(files)
    if STORAGE_TYPE == "memory":
        message = memory_store_service.index_gpu(images, ds)
        return message, ds, images
    elif STORAGE_TYPE == "qdrant":
        message = qdrant_service.index_documents(images)
        return message, ds, images


def convert_files(files):
    images = []
    files = [files] if not isinstance(files, list) else files
    for f in files:
        images.extend(convert_from_path(f, thread_count=int(WORKER_THREADS)))

    if STORAGE_TYPE == "memory":
        if len(images) >= int(IN_MEMORY_NUM_IMAGES):
            raise ValueError(
                f"The number of images in the dataset should be less than {IN_MEMORY_NUM_IMAGES}."
            )
    return images


# -----------------------
# UI
# -----------------------
with gr.Blocks(
    theme=gr.themes.Soft(),
    fill_height=True,
    css="""
/* Examples container directly under chat, full width */
#examples {
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  border: 1px solid var(--border-color-primary);
  border-radius: 12px;
  background: var(--block-background-fill);  
}

/* Make inner layout responsive regardless of Gradio version markup */
#examples .grid,
#examples .examples,
#examples .gr-examples,
#examples > div {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}

/* Pill styling for each example item */
#examples .example,
#examples button,
#examples .gr-button,
#examples .sample,
#examples .border {
  border-radius: 999px;
  border: 1px solid var(--border-color-primary);
  background: var(--background-fill-primary);
  padding: 8px 12px;
  transition: border-color .2s ease, background .2s ease, transform .05s ease;
  cursor: pointer;
}

#examples .example:hover,
#examples button:hover,
#examples .gr-button:hover {
  border-color: var(--color-accent);
  background: var(--background-fill-secondary);
}

#examples .example:active,
#examples button:active,
#examples .gr-button:active {
  transform: translateY(1px);
}
""",
) as demo:
    # Title bar
    gr.Markdown(
        """
# ColPali (ColQwen2) — PDF Retrieval with VLMs
Alpha demo for efficient page-level retrieval and LLM-generated answers.
        """.strip()
    )

    # Collapsible sidebar (upload + indexing)
    with gr.Sidebar(open=True):
        gr.Markdown("### 📂 Upload & Index")
        gr.Markdown(
            "Upload one or more PDF files, then click **Index documents** to prep them for retrieval."
        )
        file = PDF(label="PDF documents", height=280)
        convert_button = gr.Button("🔄 Index documents", variant="secondary")
        message = gr.Textbox(
            value="Files not yet uploaded",
            label="Status",
            interactive=False,
            lines=2,
        )

        # Toggle AI responses (uses environment variable for key)
        ai_enabled = gr.Checkbox(value=True, label="Enable AI responses")

        # App states
        embeds = gr.State(value=[])
        imgs = gr.State(value=[])

        gr.Markdown("### 🔎 Retrieval Settings")
        # Move Top-k to sidebar
        k = gr.Dropdown(
            choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            value=5,
            label="Top-k results",
            interactive=True,
        )
        gr.Markdown("---")
        gr.Markdown(f"**Storage:** `{STORAGE_TYPE}`")

    # Main content
    with gr.Column():
        # Chatbot UI per Gradio guides
        chat = gr.Chatbot(
            label="Chat",
            height=400,
            show_label=False,
        )

        # Full-width input to match chat width
        msg = gr.Textbox(
            placeholder="Ask a question regarding your uploaded PDFs",
            label=None,
            lines=1,
            autofocus=True,
        )

        # Action buttons on their own row
        with gr.Row():
            send_btn = gr.Button("Send", variant="primary")
            clear_btn = gr.Button("Clear", variant="secondary")

        # Helpful examples (positioned right under chat, matching width)
        gr.Examples(
            examples=[
                ["Summarize the key points of this document."],
                ["Find the section discussing GDPR compliance."],
                ["Locate any references to revenue recognition policies."],
                ["Extract the main conclusions from the study."],
            ],
            inputs=[msg],
            elem_id="examples",
            label=None,
        )

        # Retrieved images for the LAST assistant answer
        with gr.Accordion("Retrieved Pages", open=False):
            output_gallery = gr.Gallery(
                label=None,
                height=600,
                show_label=False,
                columns=2,
                object_fit="contain",
            )


    # Wiring
    convert_button.click(
        index_wrapper, inputs=[file, embeds], outputs=[message, embeds, imgs]
    )

    # Chat submit (Enter in textbox)
    msg.submit(
        on_chat_submit,
        inputs=[msg, chat, embeds, imgs, k, ai_enabled],
        outputs=[msg, chat, output_gallery],
    )

    # Chat submit (Send button)
    send_btn.click(
        on_chat_submit,
        inputs=[msg, chat, embeds, imgs, k, ai_enabled],
        outputs=[msg, chat, output_gallery],
    )

    # Clear chat and gallery
    def _clear_chat():
        return [], []

    clear_btn.click(_clear_chat, outputs=[chat, output_gallery])

if __name__ == "__main__":
    print(f"Using {STORAGE_TYPE} storage")
    demo.queue(max_size=5).launch(debug=True, mcp_server=False)
