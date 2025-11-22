# ColPali Embedding Service

This service wraps the ColModernVBert family of ColPali models behind a focused
FastAPI app. The FastAPI backend calls it whenever it needs to create text or
image embeddings; you can also run it independently for local experiments.

The service **automatically detects available hardware** and runs optimally on:
- **NVIDIA GPU** with CUDA (30-50x faster than CPU)
- **Apple Silicon** with MPS acceleration
- **CPU** with optimized threading

No manual configuration needed - the service adapts at runtime!

---

## Quick Start (Docker)

### Standalone Development

```bash
cd colpali
docker compose up -d --build
```

This starts ColPali in isolation with automatic GPU/CPU detection. Perfect for:
- Testing embeddings independently
- Debugging ColPali-specific issues
- Quick iteration on model changes

### As Part of Full Stack

From the project root:

```bash
# Minimal profile (ColPali only)
make up-minimal

# ML profile (ColPali + DeepSeek OCR)
make up-ml

# Full profile (all services)
make up-full
```

The service exposes the API on `http://localhost:7000`. When running via docker-compose,
the backend automatically connects using service names (`http://colpali:7000`).

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

**Hardware Detection:** The service automatically selects the best available device:

1. `cuda:0` - When NVIDIA GPU with CUDA is available
2. `mps` - When running on Apple Silicon
3. `cpu` - Fallback with optimized thread counts (via `CPU_THREADS`)

Check logs on startup to see which device was selected.

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
