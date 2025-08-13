import os
import gradio as gr
from gradio_pdf import PDF
from pdf2image import convert_from_path

# Your services / config
from services.openai import query_openai
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
def search_wrapper(query: str, ds, images, k, api_key):
    """Wrapper function to select between in-memory and Qdrant search"""
    # k may come from a Dropdown; ensure int
    try:
        k = int(k)
    except Exception:
        k = 5

    if STORAGE_TYPE == "memory":
        results = memory_store_service.search(query, ds, images, k)
    elif STORAGE_TYPE == "qdrant":
        results = qdrant_service.search(query, k=k)

    # api_key is a password input; never print/log it
    ai_response = query_openai(query, results, api_key)
    return ai_response, results


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
with gr.Blocks(theme=gr.themes.Soft(), fill_height=True) as demo:
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

        # Obfuscated API key (never shown or echoed)
        api_key = gr.Textbox(
            placeholder="Enter your OpenAI API key (optional)",
            label="API key",
            type="password",
        )

        # App states
        embeds = gr.State(value=[])
        imgs = gr.State(value=[])

        gr.Markdown("---")
        gr.Markdown(
            f"**Storage:** `{STORAGE_TYPE}`  \n"
            "Works best on A4 portrait, English PDFs."
        )

    # Main content
    with gr.Column():
        # Search input row
        query = gr.Textbox(
            placeholder="Ask a question about your PDFs…",
            label="Query",
            lines=2,
        )

        with gr.Row():
            # Simple dropdown for number of results
            k = gr.Dropdown(
                choices=[1,2,3,4,5,6,7,8,9,10],
                value=5,
                label="Number of results",
                interactive=True,
            )
            search_button = gr.Button("🔍 Search", variant="primary")

        # AI response ABOVE image results
        output_text = gr.Textbox(
            label="AI Response",
            placeholder="Answer synthesized from retrieved pages will appear here.",
            lines=10,
        )

        # Image results inside a retractable container (initially closed)
        with gr.Accordion("Retrieved Pages", open=False):
            output_gallery = gr.Gallery(
                label=None,
                height=600,
                show_label=False,
                columns=2,
                object_fit="contain",
            )

        # Helpful examples
        gr.Markdown("**Try an example:**")
        gr.Examples(
            examples=[
                ["Summarize the key points of this document."],
                ["Find the section discussing GDPR compliance."],
                ["What are the payment terms stated in the contract?"],
                ["Locate any references to revenue recognition policies."],
                ["Extract the main conclusions from the study."],
            ],
            inputs=[query],
        )

    # Wiring
    convert_button.click(
        index_wrapper, inputs=[file, embeds], outputs=[message, embeds, imgs]
    )

    # Note: output order changed to (AI response, results) per requirement
    search_button.click(
        search_wrapper,
        inputs=[query, embeds, imgs, k, api_key],
        outputs=[output_text, output_gallery],
    )

if __name__ == "__main__":
    print(f"Using {STORAGE_TYPE} storage")
    demo.queue(max_size=5).launch(debug=True, mcp_server=False)
