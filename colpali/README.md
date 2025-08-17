# ColPali Embedding API (ColQwen2.5)

A FastAPI service that provides query and image embeddings compatible with the backend's expected contract, including image-token boundary metadata.

- App: `colpali/app.py`
- Ports: service listens on 7000 in-container; Compose maps to 7001 (CPU) and 7002 (GPU)
- Model: `vidore/colqwen2.5-v0.2`

## Endpoints
- `GET /health` — device and health
- `GET /info` — device, dtype, dim, `image_token_id`
- `POST /patches` — compute `n_patches_x/y` for image sizes
- `POST /embed/queries` — query embeddings
- `POST /embed/images` — image embeddings + `image_patch_start`, `image_patch_len`

## Run with Docker Compose (recommended)
```bash
# From colpali/
# CPU service on http://localhost:7001
docker compose up -d api-cpu

# GPU service on http://localhost:7002 (requires NVIDIA runtime)
docker compose up -d api-gpu
```
Caching:
- A named volume (`hf-cache`) persists Hugging Face model downloads (`/data/hf-cache`).

## Configure Backend to Use It
In the repo root `.env` (consumed by backend):
```bash
# Option A: select mode, uses per-mode URLs
COLPALI_MODE=cpu
COLPALI_CPU_URL=http://localhost:7001
COLPALI_GPU_URL=http://localhost:7002

# Option B: override explicitly
# COLPALI_API_BASE_URL=http://localhost:7001
```
The backend will pick `COLPALI_API_BASE_URL` if set; otherwise it uses `COLPALI_MODE` to choose CPU/GPU URL.

## Local (no Docker)
```bash
# From colpali/
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```
Visit:
- CPU-style URL: http://localhost:7001 (when using Docker Compose mapping)
- Local direct run: http://localhost:7000

## Notes
- If a model is gated, authenticate with Hugging Face or set appropriate env vars; the current model is public but large downloads can take time.
- GPU build requires NVIDIA Container Toolkit.
