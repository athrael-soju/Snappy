import torch
import logging
from typing import List, Optional
from PIL import Image
import os

from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor

logger = logging.getLogger(__name__)


class ColPaliCore:
    """
    Core ColPali service for handling model loading and inference.
    Designed to run as a standalone service with GPU support.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize ColPali core service.
        
        Args:
            model_name: Name/path of the model to load
            device: Device to load model on
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "nomic-ai/colnomic-embed-multimodal-3b")
        self.device = device or self._get_best_device()
        self.model = None
        self.processor = None
        
        logger.info(f"Initializing ColPali core with model: {self.model_name}, device: {self.device}")
        self._load_model()
        self._load_processor()
    
    def _get_best_device(self) -> str:
        """Get the best available device"""
        if torch.cuda.is_available():
            return "cuda:0"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _load_model(self):
        """Load the ColPali model"""
        try:
            logger.info(f"Loading ColPali model: {self.model_name}")
            self.model = ColQwen2_5.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                device_map=self.device,
                attn_implementation=None
            ).eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to initialize ColPali model: {e}")
    
    def _load_processor(self):
        """Load the ColPali processor"""
        try:
            logger.info(f"Loading ColPali processor: {self.model_name}")
            self.processor = ColQwen2_5_Processor.from_pretrained(self.model_name)
            logger.info("Processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load processor: {e}")
            raise RuntimeError(f"Failed to initialize ColPali processor: {e}")
    
    def _get_patches(self, image_size):
        """Get number of patches for image"""
        return self.processor.get_n_patches(image_size, spatial_merge_size=self.model.spatial_merge_size)

    def encode_images_with_pooling(self, images: List[Image.Image], batch_size: int = 4) -> dict:
        """
        Encode images and create mean pooled representations - maintains original functionality.
        
        Args:
            images: List of PIL Images
            batch_size: Batch size for processing
            
        Returns:
            Dict containing original embeddings and pooled versions
        """
        if not images:
            raise ValueError("No images provided")
        
        try:
            with torch.no_grad():
                # Process images in batches
                original_batch = []
                pooled_by_rows_batch = []
                pooled_by_columns_batch = []
                
                for i in range(0, len(images), batch_size):
                    batch_images = images[i:i + batch_size]
                    
                    # Process batch
                    processed_images = self.processor.process_images(batch_images)
                    processed_images = {k: v.to(self.device) for k, v in processed_images.items()}
                    
                    # Get embeddings
                    image_embeddings = self.model(**processed_images)
                    
                    # Convert to lists for this batch
                    image_embeddings_list = image_embeddings.cpu().float().numpy().tolist()
                    original_batch.extend(image_embeddings_list)

                    # Mean pooling for each image in batch
                    for j, (image_embedding, tokenized_image, image) in enumerate(zip(
                        image_embeddings,
                        processed_images['input_ids'],
                        batch_images
                    )):
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
                
                logger.info(f"Encoded {len(images)} images with mean pooling")
                
                return {
                    "original": original_batch,
                    "mean_pooling_rows": pooled_by_rows_batch,
                    "mean_pooling_columns": pooled_by_columns_batch,
                    "shapes": {
                        "original": [len(original_batch), len(original_batch[0]) if original_batch else 0],
                        "mean_pooling_rows": [len(pooled_by_rows_batch), len(pooled_by_rows_batch[0]) if pooled_by_rows_batch else 0],
                        "mean_pooling_columns": [len(pooled_by_columns_batch), len(pooled_by_columns_batch[0]) if pooled_by_columns_batch else 0]
                    }
                }
                
        except Exception as e:
            logger.error(f"Error encoding images with pooling: {e}")
            raise RuntimeError(f"Failed to encode images with pooling: {e}")
    
    def encode_query(self, query: str, max_length: int = 50) -> dict:
        """
        Encode a text query to embedding and return serializable format.
        
        Args:
            query: Text query to encode
            max_length: Maximum sequence length
            
        Returns:
            Dictionary with embedding list and shape information
        """
        if not query or not query.strip():
            raise ValueError("Empty query provided")
        
        try:
            with torch.no_grad():
                # Process query
                processed_query = self.processor.process_queries([query])
                processed_query = {k: v.to(self.device) for k, v in processed_query.items()}
                
                # Get embedding
                embedding = self.model(**processed_query)
                logger.info(f"Encoded query to embedding of shape {embedding.shape}")
                
                # Convert to CPU and then to serializable format
                embedding_cpu = embedding.cpu()
                embedding_list = embedding_cpu.numpy().tolist()
                shape = list(embedding_cpu.shape)
                
                return {
                    "embedding": embedding_list,
                    "shape": shape
                }
                
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            raise RuntimeError(f"Failed to encode query: {e}")
    
    def get_device(self) -> str:
        """Get the device the model is loaded on"""
        return self.device
    
    def get_model_name(self) -> str:
        """Get the model name"""
        return self.model_name
    
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return self.model is not None and self.processor is not None
