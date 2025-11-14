# ColPali Embedding Service

This service wraps the ColModernVBert family of ColPali models behind a focused
FastAPI app. The FastAPI backend calls it whenever it needs to create text or
image embeddings; you can also run it independently for local experiments.

The service can run on CPU or GPU, exposes lightweight health and metadata
endpoints, and ships with Docker Compose profiles to make switching between CPU
and GPU builds trivial.

---

## Quick Start (Docker)

```bash
cd colpali

# GPU profile (builds flash-attn and enables CUDA)
docker compose --profile gpu up -d --build

# CPU profile (lean image, no GPU requirements)
docker compose --profile cpu up -d --build
```

Environment overrides:

- `PUBLIC_PORT=7010 docker compose --profile gpu up -d --build`  
  Publishes the API on port 7010.
- `COLPALI_GPUS=0,1 docker compose --profile gpu up -d --build`  
  Pins the service to specific GPU IDs (defaults to `all`).

Compose mounts a shared Hugging Face cache (`hf-cache` volume) and exposes the
API on `http://{PUBLIC_HOST}:{PUBLIC_PORT}` (defaults to `http://localhost:7000`).
Set `COLPALI_URL` in `backend/.env` to match the published URL.

---

## Running Locally

```bash
cd colpali
python -m venv .venv
. .venv/Scripts/activate  # on PowerShell use .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload
```

The service picks the device automatically:

- `cuda` when a compatible GPU is available.
- `mps` on Apple Silicon.
- `cpu` otherwise (torch thread counts are set via `CPU_THREADS`).

---

## Configuration Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `COLPALI_MODEL_ID` | `ModernVBERT/colmodernvbert-merged` | Hugging Face model used for embeddings (override for custom checkpoints). |
| `COLPALI_API_VERSION` | `0.1.0` | Version string returned by the service. |
| `CPU_THREADS` | `4` | Torch intra/inter-op thread count when running on CPU. |
| `ENABLE_CPU_MULTIPROCESSING` | `false` | Reserved flag for future CPU parallelism tweaks. |
| `PUBLIC_HOST` | `localhost` | Compose helper used for port publishing. |
| `PUBLIC_PORT` | `7000` | Compose helper; adjust to avoid clashes. |
| `COLPALI_GPUS` | `all` | GPU selector passed to Compose when using the GPU profile. |
| `HUGGINGFACE_HUB_CACHE`, `HF_HOME` | `/data/hf-cache` | Cache location inside the container so model downloads persist across restarts. |

The backend connects with `COLPALI_URL` and honours `COLPALI_API_TIMEOUT`.
Update those values in `.env` to point at the correct host/port.

---

## API Surface

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Basic welcome payload with the reported version. |
| `GET` | `/health` | Runtime health and current device. |
| `GET` | `/info` | Detailed model metadata (model id, dtype, flash attention, token stats). |
| `POST` | `/patches` | Estimate patch grid counts for supplied image dimensions. |
| `POST` | `/embed/queries` | Accepts a string or list of strings, returns pooled query embeddings. |
| `POST` | `/embed/images` | Accepts image files (`multipart/form-data`); returns embeddings and token boundaries per image. |

Example request:

```bash
curl -X POST http://localhost:7000/embed/queries \
  -H "Content-Type: application/json" \
  -d '{"queries": ["modern architecture", "structured cabling"]}'
```

Error responses follow FastAPI's default shape. The `/embed/images` endpoint
validates content types and reports per-image failures with an `error` field in
the response payload.

---

## Implementation Notes

- Uses `ColModernVBert.from_pretrained(..., trust_remote_code=True)` to load both
  model and processor.
- Automatically enables Flash Attention 2 when available.
- Normalises embeddings and intermediate tensors to CPU memory before returning
  them, keeping responses device-agnostic.
- The Hugging Face cache is shared between CPU and GPU builds, so the first
  download is the slowest; subsequent rebuilds reuse the weights.

For deeper changes inspect the `colpali/app/` directory structure and the Dockerfiles in this folder.
