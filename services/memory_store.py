import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from pdf2image import convert_from_path

from config import IN_MEMORY_BATCH_SIZE, IN_MEMORY_THREADS, IN_MEMORY_NUM_IMAGES

class MemoryStoreService:
    def __init__(self, model, processor):
        self.model = model
        self.processor = processor
    
    def convert_files(self, files):
        images = []
        files = [files] if not isinstance(files, list) else files
        for f in files:
            images.extend(convert_from_path(f, thread_count=int(IN_MEMORY_THREADS)))

        if len(images) >= int(IN_MEMORY_NUM_IMAGES):
            raise ValueError(f"The number of images in the dataset should be less than {IN_MEMORY_NUM_IMAGES}.")
        return images

    def index_gpu(self, images, ds):
        """Index documents using in-memory approach"""
        device = next(self.model.parameters()).device
        
        # run inference - docs
        dataloader = DataLoader(
            images,
            batch_size=int(IN_MEMORY_BATCH_SIZE),
            shuffle=False,
            collate_fn=lambda x: self.processor.process_images(x).to(device),
        )

        for batch_doc in tqdm(dataloader):
            with torch.no_grad():
                batch_doc = {k: v.to(device) for k, v in batch_doc.items()}
                embeddings_doc = self.model(**batch_doc)
            ds.extend(list(torch.unbind(embeddings_doc.to("cpu"))))
        return f"Uploaded and converted {len(images)} pages"

    def search(self, query, ds, images, k):
        """Search using in-memory approach"""
        k = min(k, len(ds))
        device = next(self.model.parameters()).device
        
        qs = []
        with torch.no_grad():
            batch_query = self.processor.process_queries([query]).to(device)
            embeddings_query = self.model(**batch_query)
            qs.extend(list(torch.unbind(embeddings_query.to("cpu"))))

        scores = self.processor.score(qs, ds, device=device)
        top_k_indices = scores[0].topk(k).indices.tolist()

        results = []
        for idx in top_k_indices:
            results.append((images[idx], f"Page {idx}"))

        return results
