import os
import uuid
import numpy as np
import torch
from qdrant_client import QdrantClient, models
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from tqdm import tqdm


class QdrantService:
    def __init__(self):
        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "documents"
        
        # Initialize ColQwen model and processor
        self.model = ColQwen2_5.from_pretrained(
            "nomic-ai/colnomic-embed-multimodal-3b",
            torch_dtype=torch.bfloat16,
            device_map="cuda:0" if torch.cuda.is_available() else "cpu",
            attn_implementation=None
        ).eval()
        self.processor = ColQwen2_5_Processor.from_pretrained("nomic-ai/colnomic-embed-multimodal-3b")
        
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()
    
    def _create_collection_if_not_exists(self):
        """Create Qdrant collection for document storage"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "original": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        ),
                        hnsw_config=models.HnswConfigDiff(m=0)
                    ),
                    "mean_pooling_columns": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        )
                    ),
                    "mean_pooling_rows": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        )
                    )
                }
            )
        except Exception as e:
            # Collection likely already exists
            pass
    
    def _get_patches(self, image_size):
        """Get number of patches for image"""
        return self.processor.get_n_patches(image_size, spatial_merge_size=self.model.spatial_merge_size)
    
    def _embed_and_mean_pool_batch(self, image_batch):
        """Embed images and create mean pooled representations"""
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if device != self.model.device:
            self.model.to(device)
            
        # Embed
        with torch.no_grad():
            processed_images = self.processor.process_images(image_batch).to(self.model.device)
            image_embeddings = self.model(**processed_images)

        image_embeddings_batch = image_embeddings.cpu().float().numpy().tolist()

        # Mean pooling
        pooled_by_rows_batch = []
        pooled_by_columns_batch = []

        for image_embedding, tokenized_image, image in zip(image_embeddings,
                                                           processed_images.input_ids,
                                                           image_batch):
            x_patches, y_patches = self._get_patches(image.size)
            
            image_tokens_mask = (tokenized_image == self.processor.image_token_id)
            image_tokens = image_embedding[image_tokens_mask].view(x_patches, y_patches, self.model.dim)
            pooled_by_rows = torch.mean(image_tokens, dim=0)
            pooled_by_columns = torch.mean(image_tokens, dim=1)

            image_token_idxs = torch.nonzero(image_tokens_mask.int(), as_tuple=False)
            first_image_token_idx = image_token_idxs[0].cpu().item()
            last_image_token_idx = image_token_idxs[-1].cpu().item()

            prefix_tokens = image_embedding[:first_image_token_idx]
            postfix_tokens = image_embedding[last_image_token_idx + 1:]

            # Adding back prefix and postfix special tokens
            pooled_by_rows = torch.cat((prefix_tokens, pooled_by_rows, postfix_tokens), dim=0).cpu().float().numpy().tolist()
            pooled_by_columns = torch.cat((prefix_tokens, pooled_by_columns, postfix_tokens), dim=0).cpu().float().numpy().tolist()

            pooled_by_rows_batch.append(pooled_by_rows)
            pooled_by_columns_batch.append(pooled_by_columns)

        return image_embeddings_batch, pooled_by_rows_batch, pooled_by_columns_batch
    
    def index_documents(self, images):
        """Index documents in Qdrant"""
        batch_size = 1  # Based on available compute
        
        with tqdm(total=len(images), desc="Uploading progress") as pbar:
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                current_batch_size = len(batch)
                
                try:
                    original_batch, pooled_by_rows_batch, pooled_by_columns_batch = self._embed_and_mean_pool_batch(batch)
                except Exception as e:
                    print(f"Error during embed: {e}")
                    continue
                    
                try:
                    self.client.upload_collection(
                        collection_name=self.collection_name,
                        vectors={
                            "mean_pooling_columns": pooled_by_columns_batch,
                            "original": original_batch,
                            "mean_pooling_rows": pooled_by_rows_batch
                        },
                        payload=[
                            {
                                "index": j,
                                "page": f"Page {j}"
                            }
                            for j in range(i, i + current_batch_size)
                        ],
                        ids=[str(uuid.uuid4()) for _ in range(len(original_batch))]
                    )
                except Exception as e:
                    print(f"Error during upsert: {e}")
                    continue
                    
                # Update the progress bar
                pbar.update(current_batch_size)
        
        return f"Uploaded and converted {len(images)} pages"
    
    def _batch_embed_query(self, query_batch):
        """Embed query batch"""
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if device != self.model.device:
            self.model.to(device)
            
        with torch.no_grad():
            processed_queries = self.processor.process_queries(query_batch).to(self.model.device)
            query_embeddings_batch = self.model(**processed_queries)
        return query_embeddings_batch.cpu().float().numpy()
    
    def _reranking_search_batch(self, query_batch, search_limit=20, prefetch_limit=200):
        """Perform two-stage retrieval with multivectors"""
        search_queries = [
            models.QueryRequest(
                query=query,
                prefetch=[
                    models.Prefetch(
                        query=query,
                        limit=prefetch_limit,
                        using="mean_pooling_columns"
                    ),
                    models.Prefetch(
                        query=query,
                        limit=prefetch_limit,
                        using="mean_pooling_rows"
                    ),
                ],
                limit=search_limit,
                with_payload=True,
                with_vector=False,
                using="original"
            ) for query in query_batch
        ]
        return self.client.query_batch_points(
            collection_name=self.collection_name,
            requests=search_queries
        )
    
    def search(self, query, images, k):
        """Search for relevant documents using Qdrant"""
        query_embedding = self._batch_embed_query([query])
        search_results = self._reranking_search_batch(query_embedding)
        
        # Extract relevant results
        results = []
        if search_results and search_results[0].points:
            for i, point in enumerate(search_results[0].points[:k]):
                idx = point.payload.get('index', 0)
                if idx < len(images):
                    results.append((images[idx], f"Page {idx}"))
        
        return results