import os
from io import BytesIO
from typing import Any, List, Optional, Tuple, Union, cast

import torch
from colpali_engine.models import ColModernVBert, ColModernVBertProcessor
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel
from transformers.utils.import_utils import is_flash_attn_2_available

# Configuration for CPU parallelism
CPU_THREADS = int(
    os.getenv("CPU_THREADS", "4")
)  # Number of torch threads for CPU inference
ENABLE_CPU_MULTIPROCESSING = (
    os.getenv("ENABLE_CPU_MULTIPROCESSING", "false").lower() == "true"
)

# Hugging Face model identifier (overridable via environment variable)
MODEL_ID = os.getenv("COLPALI_MODEL_ID", "ModernVBERT/colmodernvbert-merged")
API_VERSION = os.getenv("COLPALI_API_VERSION", "0.1.0")

# Initialize FastAPI app
app = FastAPI(
    title="ColModernVBert Embedding API",
    description="API for generating embeddings from images and queries",
)

# Determine device
device = (
    "cuda:0"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

# Configure CPU threading for better performance
if device == "cpu":
    torch.set_num_threads(CPU_THREADS)
    torch.set_num_interop_threads(CPU_THREADS)
    print(f"CPU mode: Set torch threads to {CPU_THREADS}")

TORCH_DTYPE = torch.bfloat16 if device != "cpu" else torch.float32

# Load model and processor
model = cast(
    Any,
    ColModernVBert.from_pretrained(
        MODEL_ID,
        torch_dtype=TORCH_DTYPE,
        device_map=device,
        attn_implementation=(
            "flash_attention_2" if is_flash_attn_2_available() else None
        ),
        trust_remote_code=True,
    ).eval(),
)

_processor_loaded: Union[
    ColModernVBertProcessor, Tuple[ColModernVBertProcessor, dict[str, Any]]
] = ColModernVBertProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
if isinstance(_processor_loaded, tuple):
    processor = cast(Any, _processor_loaded[0])
else:
    processor = cast(Any, _processor_loaded)

print(f"ColModernVBert model loaded on device: {device}")
print(f"Model id: {MODEL_ID}")
print(f"Model dtype: {model.dtype}")
print(f"Flash Attention 2: {'enabled' if is_flash_attn_2_available() else 'disabled'}")


def _resolve_image_token_id() -> int:
    """Best-effort resolution of the image token id for the current processor."""
    if hasattr(processor, "image_token_id"):
        return int(processor.image_token_id)  # type: ignore[arg-type]

    image_token = getattr(processor, "image_token", None)
    if image_token is not None and hasattr(processor, "tokenizer"):
        token_id = processor.tokenizer.convert_tokens_to_ids(image_token)  # type: ignore[attr-defined]
        if token_id is not None:
            return int(token_id)

    raise AttributeError("Processor does not expose an image_token_id.")


IMAGE_TOKEN_ID = _resolve_image_token_id()


class QueryRequest(BaseModel):
    queries: Union[str, List[str]]


class QueryEmbeddingResponse(BaseModel):
    embeddings: List[List[List[float]]]


class Dimension(BaseModel):
    width: int
    height: int


class PatchResult(BaseModel):
    width: int
    height: int
    n_patches_x: Optional[int] = None
    n_patches_y: Optional[int] = None
    error: Optional[str] = None


class PatchRequest(BaseModel):
    dimensions: List[Dimension]


class PatchBatchResponse(BaseModel):
    results: List[PatchResult]


class ImageEmbeddingItem(BaseModel):
    # A single image's embeddings and the image-token boundaries
    embedding: List[List[float]]  # [sequence_length, hidden_dim]
    image_patch_start: int  # index where image tokens begin
    image_patch_len: int  # number of image tokens (should equal x_patches * y_patches)


class ImageEmbeddingBatchResponse(BaseModel):
    embeddings: List[ImageEmbeddingItem]


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Load PIL Image from bytes"""
    return Image.open(BytesIO(image_bytes)).convert("RGB")


def generate_query_embeddings(queries: List[str]) -> List[torch.Tensor]:
    """Generate embeddings for text queries"""
    device = model.device
    with torch.no_grad():
        batch_query = processor.process_queries(queries).to(device)
        query_embeddings = cast(torch.Tensor, model(**batch_query))  # [batch, seq, dim]
        # Unbind into per-sample tensors on CPU
        return list(torch.unbind(query_embeddings.to("cpu")))


def generate_image_embeddings_with_boundaries(
    images: List[Image.Image],
) -> List[ImageEmbeddingItem]:
    """Generate embeddings for images and expose image-token boundaries."""
    device = model.device
    with torch.no_grad():
        # Tokenize / encode images
        batch_images = processor.process_images(images).to(device)

        # Forward pass
        image_embeddings = cast(
            torch.Tensor, model(**batch_images)
        )  # [batch, seq, dim]
        image_embeddings = image_embeddings.to("cpu")

        # Expect token ids to be present, so we can find image-token spans
        if "input_ids" not in batch_images:
            raise RuntimeError(
                "Tokenizer output missing 'input_ids'; cannot compute image token boundaries."
            )

        input_ids = batch_images["input_ids"].to("cpu")  # [batch, seq]
        image_token_id = IMAGE_TOKEN_ID

        batch_items: List[ImageEmbeddingItem] = []
        batch_size = input_ids.shape[0]

        for i in range(batch_size):
            ids = input_ids[i]  # [seq]
            emb = image_embeddings[i]  # [seq, dim]

            mask = ids.eq(image_token_id)  # bool mask for image tokens
            indices = torch.nonzero(mask, as_tuple=False).squeeze(
                -1
            )  # [num_image_tokens] or []

            if indices.numel() == 0:
                # No image tokens found; return sentinel values
                start = -1
                length = 0
            else:
                start = int(indices[0].item())
                length = int(indices.numel())

                # Sanity: ensure all indices are contiguous (as expected for image patches)
                # If there are gaps, we still use [start:length] but this flags a potential tokenizer change.
                # We won't throw here to avoid breaking callers; they can validate further.
                start_idx = int(indices[0].item())
                token_count = int(indices.numel())
                contiguous = torch.arange(
                    start_idx,
                    start_idx + token_count,
                    device=indices.device,
                    dtype=indices.dtype,
                )
                if not torch.all(indices == contiguous):
                    # Non-contiguous; still report start and length, but you may want to log this server-side.
                    print(
                        "Warning: Non-contiguous image tokens found. This may indicate a tokenizer change."
                    )

            batch_items.append(
                ImageEmbeddingItem(
                    embedding=emb.tolist(),
                    image_patch_start=start,
                    image_patch_len=length,
                )
            )

        return batch_items


# API Endpoints


@app.get("/")
async def root():
    return {"message": "ColModernVBert Embedding API", "version": API_VERSION}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "device": str(model.device)}


@app.get("/info")
async def version():
    """Version endpoint"""
    spatial_merge_size = getattr(model, "spatial_merge_size", None)
    image_seq_len = getattr(processor, "image_seq_len", None)
    return {
        "version": API_VERSION,
        "model_id": MODEL_ID,
        "device": str(model.device),
        "dtype": str(model.dtype),
        "flash_attn": is_flash_attn_2_available(),
        "spatial_merge_size": spatial_merge_size,
        "dim": getattr(model, "dim", None),
        "image_token_id": IMAGE_TOKEN_ID,
        "image_seq_len": image_seq_len,
    }


@app.post(
    "/patches",
    response_model=PatchBatchResponse,
    response_model_exclude_none=True,
)
async def get_n_patches(
    request: PatchRequest = Body(
        ..., example={"dimensions": [{"width": 1024, "height": 768}]}
    )
):
    """Calculate number of patches for given image dimensions and spatial merge size

    Args:
        request: PatchRequest containing a list of dimensions with 'width' and 'height' keys
    """
    try:
        results = []
        spatial_merge_size = getattr(model, "spatial_merge_size", None)
        get_n_patches_fn = getattr(processor, "get_n_patches", None)
        supports_patches = callable(get_n_patches_fn) and spatial_merge_size is not None

        for dim in request.dimensions:
            try:
                if not supports_patches:
                    raise NotImplementedError(
                        "Patch estimation is not available for the current model."
                    )

                image_size = (dim.width, dim.height)
                n_patches_x, n_patches_y = processor.get_n_patches(  # type: ignore[call-arg]
                    image_size, spatial_merge_size=spatial_merge_size
                )
                results.append(
                    PatchResult(
                        width=dim.width,
                        height=dim.height,
                        n_patches_x=n_patches_x,
                        n_patches_y=n_patches_y,
                    )
                )
            except Exception as e:
                results.append(
                    PatchResult(
                        width=dim.width,
                        height=dim.height,
                        error=str(e),
                    )
                )
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing patch request: {str(e)}"
        )


@app.post("/embed/queries", response_model=QueryEmbeddingResponse)
async def embed_queries(request: QueryRequest):
    """Generate embeddings for text queries"""
    try:
        queries = (
            [request.queries] if isinstance(request.queries, str) else request.queries
        )
        if not queries:
            raise HTTPException(status_code=400, detail="No queries provided")

        embeddings_tensors = generate_query_embeddings(queries)
        embeddings_list = [embedding.tolist() for embedding in embeddings_tensors]
        return QueryEmbeddingResponse(embeddings=embeddings_list)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating query embeddings: {str(e)}"
        )


@app.post("/embed/images", response_model=ImageEmbeddingBatchResponse)
async def embed_images(files: List[UploadFile] = File(...)):
    """Generate embeddings for uploaded images + image-token boundaries."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No images provided")

        images: List[Image.Image] = []
        for file in files:
            content_type = file.content_type or ""
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not an image"
                )
            image_bytes = await file.read()
            images.append(load_image_from_bytes(image_bytes))

        items = generate_image_embeddings_with_boundaries(images)
        return ImageEmbeddingBatchResponse(embeddings=items)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating image embeddings: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7000, reload=True, workers=1)
