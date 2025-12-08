"""
Local model inference for benchmarks.

Allows testing different ColPali-style models without modifying the main service.
Supports ColQwen3 (via transformers) and ColModernVBert/ColPali (via colpali_engine).
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)


class LocalColPaliModel:
    """
    Local ColPali-style model for benchmark testing.

    Loads and runs inference directly without HTTP service.
    Supports:
    - ColQwen3 models (TomoroAI) via transformers AutoModel/AutoProcessor
    - ColModernVBert and ColPali via colpali_engine
    """

    def __init__(
        self,
        model_id: str,
        device: Optional[str] = None,
        torch_dtype: Optional[torch.dtype] = None,
    ):
        """
        Initialize local model.

        Args:
            model_id: HuggingFace model ID (e.g., "TomoroAI/tomoro-colqwen3-embed-4b")
            device: Device to load model on (auto-detected if None)
            torch_dtype: Torch dtype for model weights
        """
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.torch_dtype = torch_dtype or (torch.bfloat16 if torch.cuda.is_available() else torch.float32)

        self.model = None
        self.processor = None
        self.model_type = None  # Track which type of model was loaded

        self._load_model()

    def _load_model(self) -> None:
        """Load model and processor based on model ID."""
        logger.info(f"Loading local model: {self.model_id}")
        logger.info(f"Device: {self.device}, dtype: {self.torch_dtype}")

        # Determine model class from model ID
        model_id_lower = self.model_id.lower()

        if "tomoro" in model_id_lower or "colqwen3" in model_id_lower:
            # TomoroAI ColQwen3 models use transformers directly
            self._load_tomoro_colqwen()
        elif "colqwen2" in model_id_lower:
            # ColQwen2 from colpali_engine
            self._load_colqwen2()
        elif "modernvbert" in model_id_lower or "modernbert" in model_id_lower:
            self._load_colmodernvbert()
        elif "pali" in model_id_lower:
            self._load_colpali()
        else:
            # Default to transformers AutoModel for unknown models
            logger.warning(f"Unknown model type for {self.model_id}, trying AutoModel")
            self._load_tomoro_colqwen()

    def _load_tomoro_colqwen(self) -> None:
        """Load TomoroAI ColQwen3 model using transformers AutoModel/AutoProcessor."""
        from transformers import AutoModel, AutoProcessor

        self.processor = AutoProcessor.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            max_num_visual_tokens=5120,
        )

        self.model = AutoModel.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype,
            trust_remote_code=True,
            device_map=self.device,
        ).eval()

        self.model_type = "tomoro_colqwen"
        logger.info(f"Loaded TomoroAI ColQwen3 model: {self.model_id}")

    def _load_colqwen2(self) -> None:
        """Load ColQwen2 model from colpali_engine."""
        try:
            from colpali_engine.models import ColQwen2, ColQwen2Processor

            self.model = ColQwen2.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                device_map=self.device,
            ).eval()

            self.processor = ColQwen2Processor.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )

            self.model_type = "colpali_engine"
            logger.info(f"Loaded ColQwen2 model: {self.model_id}")

        except ImportError as e:
            raise ImportError(
                f"Failed to import ColQwen2 from colpali_engine: {e}. "
                "Install with: pip install colpali-engine"
            )

    def _load_colmodernvbert(self) -> None:
        """Load ColModernVBert model and processor."""
        try:
            from colpali_engine.models import ColModernVBert, ColModernVBertProcessor

            self.model = ColModernVBert.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                device_map=self.device,
            ).eval()

            self.processor = ColModernVBertProcessor.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )

            logger.info(f"Loaded ColModernVBert model: {self.model_id}")

        except ImportError as e:
            raise ImportError(
                f"Failed to import ColModernVBert from colpali_engine: {e}. "
                "Install with: pip install colpali-engine"
            )

    def _load_colpali(self) -> None:
        """Load original ColPali model and processor."""
        try:
            from colpali_engine.models import ColPali, ColPaliProcessor

            self.model = ColPali.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                device_map=self.device,
            ).eval()

            self.processor = ColPaliProcessor.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )

            logger.info(f"Loaded ColPali model: {self.model_id}")

        except ImportError as e:
            raise ImportError(
                f"Failed to import ColPali from colpali_engine: {e}. "
                "Install with: pip install colpali-engine"
            )

    def generate_interpretability_maps(
        self,
        query: str,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """
        Generate interpretability maps for a query-image pair.

        Args:
            query: Text query
            image: PIL Image

        Returns:
            Dictionary with similarity_maps in same format as HTTP service
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded")

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Route to appropriate method based on model type
        if self.model_type == "tomoro_colqwen":
            return self._generate_maps_tomoro(query, image)
        else:
            return self._generate_maps_colpali_engine(query, image)

    def _generate_maps_tomoro(
        self,
        query: str,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """Generate interpretability maps for TomoroAI ColQwen3 models."""
        # Process query using process_texts
        query_batch = self.processor.process_texts(texts=[query])
        query_batch = {k: v.to(self.device) for k, v in query_batch.items()}

        # Process image - TomoroAI uses processor() directly for images
        image_batch = self.processor(
            images=[image],
            padding="longest",
            return_tensors="pt",
        )

        # Extract grid dimensions before moving to device
        # image_grid_thw has shape (num_images, 3) with [T, H, W]
        # Note: H and W are PRE-merge dimensions. Actual patches = H*W / merge_size^2
        image_grid_thw = image_batch.get("image_grid_thw")

        # Get merge_size from processor (typically 2)
        merge_size = getattr(self.processor.image_processor, "merge_size", None) or \
                     getattr(self.processor.image_processor, "spatial_merge_size", 2)

        if image_grid_thw is not None:
            t, h, w = image_grid_thw[0].tolist()
            # Apply merge_size to get actual grid dimensions
            grid_h = int(h) // merge_size
            grid_w = int(w) // merge_size
            logger.info(
                f"Image grid: raw={int(h)}x{int(w)}, merge_size={merge_size}, "
                f"actual={grid_h}x{grid_w} patches (T={t})"
            )
        else:
            grid_h, grid_w = 32, 32  # Fallback
            logger.warning("No image_grid_thw found, using default 32x32")

        image_batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in image_batch.items()}

        # Generate embeddings
        with torch.no_grad():
            query_out = self.model(**query_batch)
            image_out = self.model(**image_batch)

        # Extract embeddings - TomoroAI returns .embeddings attribute
        query_embeddings = query_out.embeddings  # (1, num_tokens, dim)
        image_embeddings = image_out.embeddings  # (1, num_visual_tokens, dim)

        # The image embeddings include text tokens from the visual prompt:
        # <|im_start|>user\n<|vision_start|>[IMAGE_PATCHES]<|vision_end|>Describe...<|im_end|><|endoftext|>
        # We need to extract only the image patch embeddings.
        expected_patches = grid_h * grid_w
        num_total_tokens = image_embeddings.shape[1]

        # Find the image token positions using input_ids
        input_ids = image_batch.get("input_ids")
        if input_ids is not None:
            # Get the image token ID from model config
            image_token_id = getattr(self.model.config, "image_token_id", 151655)

            # Find positions where input_ids == image_token_id
            image_mask = (input_ids[0] == image_token_id)
            image_positions = torch.where(image_mask)[0]

            if len(image_positions) == expected_patches:
                # Extract only image patch embeddings
                image_embeddings = image_embeddings[:, image_positions, :]
                logger.info(
                    f"Extracted {len(image_positions)} image patches from {num_total_tokens} total tokens"
                )
            else:
                logger.warning(
                    f"Found {len(image_positions)} image tokens, expected {expected_patches}. "
                    f"Using all {num_total_tokens} tokens."
                )
        else:
            logger.warning("No input_ids found, using all embeddings")

        logger.info(
            f"Embeddings: query={query_embeddings.shape[1]} tokens, "
            f"image={image_embeddings.shape[1]} tokens, grid={grid_h}x{grid_w}"
        )

        # Compute per-token similarity
        similarity = torch.einsum(
            "bnd,bmd->bnm",
            query_embeddings,
            image_embeddings,
        )  # (1, num_tokens, num_patches)

        similarity = similarity.squeeze(0)  # (num_tokens, num_patches)

        # Get query tokens for labeling
        tokenizer = getattr(self.processor, 'tokenizer', None)
        if tokenizer:
            query_tokens = tokenizer.tokenize(query)
        else:
            # Fallback: just use indices
            query_tokens = [f"token_{i}" for i in range(similarity.shape[0])]

        return self._build_similarity_response(query, query_tokens, similarity, grid_h, grid_w)

    def _generate_maps_colpali_engine(
        self,
        query: str,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """Generate interpretability maps for colpali_engine models."""
        # Process inputs using colpali_engine API
        batch_images = self.processor.process_images([image]).to(self.device)
        batch_queries = self.processor.process_queries([query]).to(self.device)

        # Generate embeddings
        with torch.no_grad():
            image_embeddings = self.model(**batch_images)
            query_embeddings = self.model(**batch_queries)

        # Compute per-token similarity
        similarity = torch.einsum(
            "bnd,bmd->bnm",
            query_embeddings,
            image_embeddings,
        )

        similarity = similarity.squeeze(0)

        # Get query tokens
        query_tokens = self.processor.tokenizer.tokenize(query)

        # ColPali-engine models use fixed 32x32 grid
        return self._build_similarity_response(query, query_tokens, similarity, 32, 32)

    def _build_similarity_response(
        self,
        query: str,
        query_tokens: List[str],
        similarity: torch.Tensor,
        grid_h: int,
        grid_w: int,
    ) -> Dict[str, Any]:
        """Build the response dictionary from similarity tensor.

        Args:
            query: Original query string
            query_tokens: Tokenized query for labeling
            similarity: (num_tokens, num_patches) similarity tensor
            grid_h: Height of the patch grid
            grid_w: Width of the patch grid
        """
        expected_patches = grid_h * grid_w

        # Convert to float32 for numpy compatibility (bf16 not supported)
        similarity = similarity.float()

        # Build similarity maps
        similarity_maps = []

        for token_idx, token in enumerate(query_tokens):
            if token_idx >= similarity.shape[0]:
                break

            token_similarity = similarity[token_idx].cpu().numpy()

            # Reshape to 2D grid using provided dimensions
            if len(token_similarity) == expected_patches:
                # Exact match - direct reshape
                sim_map_2d = token_similarity.reshape(grid_h, grid_w)
            elif len(token_similarity) > expected_patches:
                # More patches than expected - truncate (shouldn't happen normally)
                logger.warning(f"Truncating {len(token_similarity)} patches to {expected_patches}")
                sim_map_2d = token_similarity[:expected_patches].reshape(grid_h, grid_w)
            else:
                # Fewer patches - pad with zeros
                logger.warning(f"Padding {len(token_similarity)} patches to {expected_patches}")
                padded = np.zeros(expected_patches)
                padded[:len(token_similarity)] = token_similarity
                sim_map_2d = padded.reshape(grid_h, grid_w)

            similarity_maps.append({
                "token": token,
                "token_index": token_idx,
                "similarity_map": sim_map_2d.tolist(),
            })

        return {
            "query": query,
            "num_query_tokens": len(query_tokens),
            "similarity_maps": similarity_maps,
            "grid_size": (grid_h, grid_w),
            "model_id": self.model_id,
        }

    def health_check(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.processor is not None


class LocalModelClient:
    """
    Client interface that matches BenchmarkColPaliClient API.

    Drop-in replacement for HTTP client when using local models.
    """

    def __init__(self, model: LocalColPaliModel):
        """
        Initialize client with local model.

        Args:
            model: Loaded local model instance
        """
        self.model = model

    def health_check(self) -> bool:
        """Check if model is ready."""
        return self.model.health_check()

    def generate_interpretability_maps(
        self,
        query: str,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """
        Generate interpretability maps.

        Args:
            query: Text query
            image: PIL Image

        Returns:
            Dictionary with similarity_maps
        """
        return self.model.generate_interpretability_maps(query, image)
