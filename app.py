import os
import base64
from io import BytesIO

import gradio as gr
from gradio_pdf import PDF
import torch

from pdf2image import convert_from_path
from PIL import Image
from torch.utils.data import DataLoader
from tqdm import tqdm

from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor

from services.openai import query_gpt4_1_mini



model = ColQwen2_5.from_pretrained(
        "nomic-ai/colnomic-embed-multimodal-3b",
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",  # or "mps" if on Apple Silicon
        attn_implementation=None
    ).eval()
processor = ColQwen2_5_Processor.from_pretrained("nomic-ai/colnomic-embed-multimodal-3b")


def search(query: str, ds, images, k, api_key):
    k = min(k, len(ds))
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if device != model.device:
        model.to(device)
        
    qs = []
    with torch.no_grad():
        batch_query = processor.process_queries([query]).to(model.device)
        embeddings_query = model(**batch_query)
        qs.extend(list(torch.unbind(embeddings_query.to("cpu"))))

    scores = processor.score(qs, ds, device=device)

    top_k_indices = scores[0].topk(k).indices.tolist()

    results = []
    for idx in top_k_indices:
        results.append((images[idx], f"Page {idx}"))

    # Generate response from GPT-4.1-mini
    ai_response = query_gpt4_1_mini(query, results, api_key)

    return results, ai_response


def index(files, ds):
    print("Converting files")
    images = convert_files(files)
    print(f"Files converted with {len(images)} images.")
    return index_gpu(images, ds)
    


def convert_files(files):
    images = []
    print(files)
    files = [files]
    for f in files:
        images.extend(convert_from_path(f, thread_count=4))

    if len(images) >= 500:
        raise gr.Error("The number of images in the dataset should be less than 500.")
    return images


def index_gpu(images, ds):
    """Example script to run inference with ColPali (ColQwen2)"""

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if device != model.device:
        model.to(device)
        
    # run inference - docs
    dataloader = DataLoader(
        images,
        batch_size=4,
        # num_workers=4,
        shuffle=False,
        collate_fn=lambda x: processor.process_images(x).to(model.device),
    )

    for batch_doc in tqdm(dataloader):
        with torch.no_grad():
            batch_doc = {k: v.to(device) for k, v in batch_doc.items()}
            embeddings_doc = model(**batch_doc)
        ds.extend(list(torch.unbind(embeddings_doc.to("cpu"))))
    return f"Uploaded and converted {len(images)} pages", ds, images



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
            # file = gr.File(file_types=["pdf"], file_count="multiple", label="Upload PDFs")
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

    convert_button.click(index, inputs=[file, embeds], outputs=[message, embeds, imgs])
    search_button.click(search, inputs=[query, embeds, imgs, k, api_key], outputs=[output_gallery, output_text])

if __name__ == "__main__":
    demo.queue(max_size=5).launch(debug=True, mcp_server=True)