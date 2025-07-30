import torch

import gradio as gr
from gradio_pdf import PDF

from services.openai import query_openai
from pdf2image import convert_from_path

# Import the appropriate service based on environment variable
from config import STORAGE_TYPE, MODEL_NAME, MODEL_DEVICE, IN_MEMORY_THREADS, IN_MEMORY_NUM_IMAGES
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor

memory_store_service = None
qdrant_service = None

# Initialize model and processor
model = ColQwen2_5.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    device_map=MODEL_DEVICE,
    attn_implementation=None
).eval()
processor = ColQwen2_5_Processor.from_pretrained(MODEL_NAME)

if STORAGE_TYPE == "memory":
    from services.memory_store import MemoryStoreService
    memory_store_service = MemoryStoreService(model, processor)
elif STORAGE_TYPE == "qdrant":
    from services.qdrant_store import QdrantService
    qdrant_service = QdrantService(model, processor)
else:
    raise ValueError("Invalid storage type")


def search_wrapper(query: str, ds, images, k, api_key):
    """Wrapper function to select between in-memory and Qdrant search"""
    if STORAGE_TYPE == "memory":
        results = memory_store_service.search(query, ds, images, k)
    elif STORAGE_TYPE == "qdrant":
        results = qdrant_service.search(query, images, k)
    
    # Generate response from GPT-4.1-mini
    ai_response = query_openai(query, results, api_key)
    
    return results, ai_response


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
        images.extend(convert_from_path(f, thread_count=int(IN_MEMORY_THREADS)))

    if len(images) >= int(IN_MEMORY_NUM_IMAGES):
        raise ValueError(f"The number of images in the dataset should be less than {IN_MEMORY_NUM_IMAGES}.")
    return images


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ColPali: Efficient Document Retrieval with Vision Language Models (ColQwen2) 📚")
    gr.Markdown("""Demo to test ColQwen2 (ColPali) on PDF documents. 
    ColPali is model implemented from the [ColPali paper](https://arxiv.org/abs/2407.01449).

    This demo allows you to upload PDF files and search for the most relevant pages based on your query.
    Refresh the page if you change documents !

    ⚠️ This demo uses a model trained exclusively on A4 PDFs in portrait mode, containing english text. Performance is expected to drop for other page formats and languages.
    Other models will be released with better robustness towards different languages and document formats !
    """)
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## 1️⃣ Upload PDFs")
            file = PDF(label="PDF Document")
            print(file)

            convert_button = gr.Button("🔄 Index documents")
            message = gr.Textbox("Files not yet uploaded", label="Status")
            api_key = gr.Textbox(placeholder="Enter your OpenAI KEY here (optional)", label="API key")
            embeds = gr.State(value=[])
            imgs = gr.State(value=[])

        with gr.Column(scale=3):
            gr.Markdown("## 2️⃣ Search")
            query = gr.Textbox(placeholder="Enter your query here", label="Query")
            k = gr.Slider(minimum=1, maximum=10, step=1, label="Number of results", value=5)


    # Define the actions
    search_button = gr.Button("🔍 Search", variant="primary")
    output_gallery = gr.Gallery(label="Retrieved Documents", height=600, show_label=True)
    output_text = gr.Textbox(label="AI Response", placeholder="Generated response based on retrieved documents")

    convert_button.click(index_wrapper, inputs=[file, embeds], outputs=[message, embeds, imgs])
    search_button.click(search_wrapper, inputs=[query, embeds, imgs, k, api_key], outputs=[output_gallery, output_text])

if __name__ == "__main__":
    # Print which storage type is being used
    print(f"Using {STORAGE_TYPE} storage")
    demo.queue(max_size=5).launch(debug=True, mcp_server=False)