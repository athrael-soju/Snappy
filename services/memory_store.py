import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from pdf2image import convert_from_path


def convert_files(files):
    images = []
    files = [files] if not isinstance(files, list) else files
    for f in files:
        images.extend(convert_from_path(f, thread_count=4))

    if len(images) >= 500:
        raise ValueError("The number of images in the dataset should be less than 500.")
    return images


def index_gpu(images, ds):
    """Index documents using in-memory approach"""
    from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
    
    model = ColQwen2_5.from_pretrained(
        "nomic-ai/colnomic-embed-multimodal-3b",
        torch_dtype=torch.bfloat16,
        device_map="cuda:0" if torch.cuda.is_available() else "cpu",
        attn_implementation=None
    ).eval()
    processor = ColQwen2_5_Processor.from_pretrained("nomic-ai/colnomic-embed-multimodal-3b")
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if device != model.device:
        model.to(device)
        
    # run inference - docs
    dataloader = DataLoader(
        images,
        batch_size=4,
        shuffle=False,
        collate_fn=lambda x: processor.process_images(x).to(model.device),
    )

    for batch_doc in tqdm(dataloader):
        with torch.no_grad():
            batch_doc = {k: v.to(device) for k, v in batch_doc.items()}
            embeddings_doc = model(**batch_doc)
        ds.extend(list(torch.unbind(embeddings_doc.to("cpu"))))
    return f"Uploaded and converted {len(images)} pages"


def search(query, ds, images, k):
    """Search using in-memory approach"""
    k = min(k, len(ds))
    
    from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
    
    model = ColQwen2_5.from_pretrained(
        "nomic-ai/colnomic-embed-multimodal-3b",
        torch_dtype=torch.bfloat16,
        device_map="cuda:0" if torch.cuda.is_available() else "cpu",
        attn_implementation=None
    ).eval()
    processor = ColQwen2_5_Processor.from_pretrained("nomic-ai/colnomic-embed-multimodal-3b")
    
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

    return results
