import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import BATCH_SIZE
from .colpali_service import ColPaliService

class MemoryStoreService:
    def __init__(self, colpali_service: ColPaliService = None):
        """
        Initialize MemoryStoreService with ColPali service.
        
        Args:
            colpali_service: Instance of ColPaliService. If None, will create a new one.
        """
        if colpali_service is None:
            colpali_service = ColPaliService()
        
        self.colpali_service = colpali_service
        self.model = colpali_service.get_model()
        self.processor = colpali_service.get_processor()
    
    def index_gpu(self, images, ds):
        """Index documents using in-memory approach"""
        device = next(self.model.parameters()).device
        
        # run inference - docs
        dataloader = DataLoader(
            images,
            batch_size=int(BATCH_SIZE),
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
