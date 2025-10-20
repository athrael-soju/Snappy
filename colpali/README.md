# ColPali Embedding API - The Vision Brain!

This service generates query and image embeddings with the ColModernVBert late-interaction retriever (`ModernVBERT/colmodernvbert-merged`) and exposes image-token boundary metadata.

- **App**: `colpali/app.py`
- **Ports**: listen on 7000 in-container
- **Model**: `ModernVBERT/colmodernvbert-merged` (late-interaction ModernVBERT retriever)

## API Endpoints
- `GET /health` - runtime status and active device
- `GET /info` - device, dtype, model id, and optional image-token metadata
- `POST /patches` - patch grid counts when supported (returns an informative error for ColModernVBert)
- `POST /embed/queries` - text embeddings
- `POST /embed/images` - image embeddings with image-token boundaries

## Docker Compose - The Easy Way

```bash
# From the colpali/ directory

# GPU profile (builds with CUDA + flash-attn support)
docker compose --profile gpu up -d --build
# api available at http://localhost:7000

# CPU profile (lighter image, no GPU requirements)
docker compose --profile cpu up -d --build

# Override port/GPU exposure as needed
PUBLIC_PORT=7010 COLPALI_GPUS=all docker compose --profile gpu up -d --build
```

> Profiles are mutually exclusive—run with either `--profile gpu` or `--profile cpu` depending on your host.

**Smart Caching**: We use a named volume (`hf-cache`) to persist your Hugging Face model downloads at `/data/hf-cache`. Download once, use forever.

`Dockerfile.cpu` keeps things lightweight for local development, while `Dockerfile.gpu` builds on NVIDIA's `pytorch/pytorch:2.9.0-cuda13.0-cudnn9-devel` image and layers in `flash-attn` so recent GPUs work out of the box. You can override `PUBLIC_PORT`/`PUBLIC_HOST` the same way.

## Connect Snappy to ColPali

In your root `.env` file (the backend reads this):

```bash
# Tell Snappy where to find the services
COLPALI_URL=http://localhost:7000
```

> If you override `PUBLIC_PORT` when starting the container, keep the `COLPALI_URL` in sync.

## Running Locally (No Docker)

```bash
# From the colpali/ directory

# Set up your virtual environment
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -U pip setuptools wheel
pip install -r requirements.txt

# Fire it up!
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

**Access Points**:
- Local direct: http://localhost:7000
- Docker Compose style: http://localhost:7000 or your chosen `PUBLIC_PORT` 

## Good to Know
- **Model Access**: ColModernVBert is public but it is a large download; the first run may take a minute.
- **GPU Requirements**: You need the NVIDIA Container Toolkit for GPU mode (`COLPALI_GPUS` controls how many devices are exposed).
- **First GPU build pulls CUDA 12.6 tooling**: The image installs the minimal CUDA compiler stack so `flash-attn` can build; expect the first `--build` to download a few extra packages.
- **Gated Models**: If you switch to a gated model, authenticate with Hugging Face first.

## How It All Connects

This embedding service is Snappy's visual brain:
1. Provides query and image embeddings to the backend
2. Powers the search functionality (`GET /search`)
3. Enables the chat route to find relevant document pages
4. Makes visual citations possible

When the Next.js chat route finds relevant images, it emits a `kb.images` Server-Sent Event so the UI can highlight that visual citations are available.
