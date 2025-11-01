import inspect
import math
import os
from io import BytesIO
from typing import Any, List, Optional, Tuple, Union, cast

import torch
from colpali_engine.models import ColModernVBert, ColModernVBertProcessor
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
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
API_VERSION = os.getenv("COLPALI_API_VERSION", "0.0.2")

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
    image_patch_indices: List[int]  # explicit positions of every image token


class ImageEmbeddingBatchResponse(BaseModel):
    embeddings: List[ImageEmbeddingItem]


class HeatmapResponse(BaseModel):
    image_width: int
    image_height: int
    grid_rows: int
    grid_columns: int
    aggregate: str
    min_score: float
    max_score: float
    heatmap: List[List[float]]


def _compute_patch_grid(patch_len: int) -> Tuple[int, int]:
    """Derive a rectangular patch grid given the flattened token count."""
    if patch_len <= 0:
        raise ValueError("Patch length must be positive to compute a grid.")
    root = int(math.isqrt(patch_len))
    if root * root == patch_len:
        return root, root
    # Fall back to finding the closest factor pair (rows, cols).
    for rows in range(root, 0, -1):
        if patch_len % rows == 0:
            return rows, patch_len // rows
    # As a last resort, treat the sequence as a single row.
    return 1, patch_len


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
            indices = torch.nonzero(mask, as_tuple=True)[0]  # [num_image_tokens] or []
            indices_list = indices.view(-1).tolist() if indices.numel() > 0 else []

            if not indices_list:
                # No image tokens found; return sentinel values
                start = -1
                length = 0
            else:
                start = int(indices_list[0])
                length = len(indices_list)

            batch_items.append(
                ImageEmbeddingItem(
                    embedding=emb.tolist(),
                    image_patch_start=start,
                    image_patch_len=length,
                    image_patch_indices=[int(idx) for idx in indices_list],
                )
            )

        return batch_items


def generate_similarity_heatmap(
    query: str,
    image: Image.Image,
    aggregate: str = "max",
) -> HeatmapResponse:
    """Compute a similarity heatmap between a text query and an image."""
    import torch
    import torch.nn.functional as F

    aggregate_mode = aggregate.lower() if aggregate else "max"
    if aggregate_mode not in {"max", "mean", "sum"}:
        aggregate_mode = "max"

    query_embeddings = generate_query_embeddings([query])
    if not query_embeddings:
        raise ValueError("Failed to generate query embeddings.")
    query_tensor = query_embeddings[0].to(torch.float32)  # [q_tokens, dim]

    items = generate_image_embeddings_with_boundaries([image])
    if not items:
        raise ValueError("Failed to generate image embeddings.")

    item = items[0]
    patch_indices = item.image_patch_indices
    if not patch_indices:
        raise ValueError("Image embeddings did not include patch indices.")

    image_tensor = torch.tensor(item.embedding, dtype=torch.float32)  # [seq, dim]
    patch_tensor = image_tensor[torch.tensor(patch_indices, dtype=torch.long)]
    patch_len = patch_tensor.shape[0]
    rows, cols = _compute_patch_grid(patch_len)

    # Normalize embeddings before similarity.
    query_norm = F.normalize(query_tensor, dim=-1)
    patch_norm = F.normalize(patch_tensor, dim=-1)

    similarity = torch.matmul(query_norm, patch_norm.T)  # [q_tokens, patch_len]

    if aggregate_mode == "mean":
        aggregated = similarity.mean(dim=0)
    elif aggregate_mode == "sum":
        aggregated = similarity.sum(dim=0)
    else:
        aggregated = similarity.max(dim=0).values

    min_score = float(aggregated.min().item())
    max_score = float(aggregated.max().item())
    denom = max_score - min_score
    if denom <= 1e-12:
        normalized = torch.zeros_like(aggregated)
    else:
        normalized = (aggregated - min_score) / denom

    heatmap = normalized.view(rows, cols).tolist()

    return HeatmapResponse(
        image_width=image.width,
        image_height=image.height,
        grid_rows=rows,
        grid_columns=cols,
        aggregate=aggregate_mode,
        min_score=min_score,
        max_score=max_score,
        heatmap=heatmap,
    )


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
        get_n_patches_fn = getattr(processor, "get_n_patches", None)
        supports_patches = callable(get_n_patches_fn)
        call_kwargs: dict[str, Any] = {}
        unsupported_reason: Optional[str] = None

        if supports_patches:
            try:
                if get_n_patches_fn is not None:
                    signature = inspect.signature(get_n_patches_fn)
                else:
                    signature = None
            except (TypeError, ValueError):
                signature = None

            if signature is not None:
                for name, param in signature.parameters.items():
                    if name == "image_size":
                        continue

                    value: Any = None
                    if name in {"patch_size", "spatial_merge_size"}:
                        value = getattr(model, "spatial_merge_size", None)
                    elif hasattr(processor, name):
                        value = getattr(processor, name)
                    elif hasattr(model, name):
                        value = getattr(model, name)

                    if value is None:
                        if param.default is inspect._empty:
                            supports_patches = False
                            unsupported_reason = f"Required parameter '{name}' is not provided by the current model."
                            break
                        continue

                    call_kwargs[name] = value

            if supports_patches and signature is None:
                # Unable to inspect signature safely; proceed without extra kwargs.
                call_kwargs = {}

        if not supports_patches:
            unsupported_reason = (
                unsupported_reason
                or "Patch estimation is not available for the current model."
            )

        for dim in request.dimensions:
            try:
                if not supports_patches:
                    raise NotImplementedError(unsupported_reason)

                image_size = (dim.width, dim.height)
                try:
                    n_patches_x, n_patches_y = get_n_patches_fn(  # type: ignore[misc]
                        image_size, **call_kwargs
                    )
                except NotImplementedError:
                    raise

                results.append(
                    PatchResult(
                        width=dim.width,
                        height=dim.height,
                        n_patches_x=int(n_patches_x),
                        n_patches_y=int(n_patches_y),
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


@app.post("/heatmap", response_model=HeatmapResponse)
async def heatmap(
    query: str = Form(...),
    image: UploadFile = File(...),
    aggregate: str = Form("max"),
):
    """Generate a normalized similarity heatmap for a query-image pair."""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query is required.")
        image_bytes = await image.read()
        pil_image = load_image_from_bytes(image_bytes)
        return generate_similarity_heatmap(
            query=query, image=pil_image, aggregate=aggregate
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating heatmap: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7000, reload=True, workers=1)
