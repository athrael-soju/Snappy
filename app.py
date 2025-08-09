import gradio as gr
from gradio_pdf import PDF

from services.openai import OpenAIService
from services.colpali_service import ColPaliClient
from services.qdrant_store import QdrantService
from pdf2image import convert_from_path

# Import configuration
from config import WORKER_THREADS, COLPALI_SERVICE_URL

# Initialize services
colpali_client = ColPaliClient(base_url=COLPALI_SERVICE_URL)
openai_service = OpenAIService()
qdrant_service = QdrantService(colpali_client)


def search_wrapper(query: str, ds, images, k, api_key):
    """Search for relevant documents using Qdrant"""
    results = qdrant_service.search(query, k=k)
    ai_response = openai_service.query(query, results, api_key)
    return results, ai_response


def index_wrapper(files, ds):
    """Index documents using Qdrant"""
    images = convert_files(files)
    message = qdrant_service.index_documents(images)
    return message, ds, images


def convert_files(files):
    images = []
    files = [files] if not isinstance(files, list) else files
    for f in files:
        images.extend(convert_from_path(f, thread_count=int(WORKER_THREADS)))
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

    search_button = gr.Button("🔍 Search", variant="primary")
    output_gallery = gr.Gallery(label="Retrieved Documents", height=600, show_label=True)
    output_text = gr.Textbox(label="AI Response", placeholder="Generated response based on retrieved documents")

    convert_button.click(index_wrapper, inputs=[file, embeds], outputs=[message, embeds, imgs])
    search_button.click(search_wrapper, inputs=[query, embeds, imgs, k, api_key], outputs=[output_gallery, output_text])

if __name__ == "__main__":
    print("Using Qdrant storage with distributed ColPali service")
    
    print("OpenAI Service Info:")
    openai_info = openai_service.get_model_info()
    for key, value in openai_info.items():
        print(f"  {key}: {value}")
    
    demo.queue(max_size=5).launch(debug=True, mcp_server=False, server_name="127.0.0.1", server_port=7860)