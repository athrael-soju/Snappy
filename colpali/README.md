# ColModernVBert Microservice

This folder packages the FastAPI microservice that serves ColModernVBert query and image embeddings. The service runs fine inside Docker (CPU or GPU) but you can also run it directly on your machine for local development or lightweight demos.

---

## 1. Prerequisites

- **Python**: 3.12 (3.10+ works, but the Docker images use 3.12).
- **Git**: required because `colpali_engine` is installed from a Git repo.
- **Torch**:
  - CPU only: install `torch`/`torchvision` from the PyTorch CPU index.
  - GPU (Linux/WSL preferred): install the CUDA build that matches your driver. FlashAttention requires a working C/C++ toolchain (`gcc`, `g++`, `ninja`) to compile its kernels. On Windows you’ll need Build Tools for Visual Studio *or* run inside WSL.
- (Optional) **FlashAttention 2**: only needed if you want the fastest GPU inference. Install the wheel published for your exact torch build, or rely on the one baked into the GPU Dockerfile.

---

## 2. Environment Setup

1. **Create a virtual environment** (recommended):
   ```bash
   cd colpali
   python -m venv .venv
   source .venv/bin/activate          # on Windows PowerShell: .venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   ```

2. **Install PyTorch** before the rest of the requirements:
   ```bash
   # CPU
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

   # GPU (example for CUDA 12.1 – adjust to your setup)
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Install service dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) FlashAttention 2 on GPU** – pick the wheel matching your environment:
   ```bash
   pip install <flash_attn_wheel.whl>
   ```

---

## 3. Configuration

The service honours the following environment variables:

| Variable | Default | Notes |
|----------|---------|-------|
| `COLPALI_MODEL_ID` | `ModernVBERT/colmodernvbert-merged` | Any Hugging Face ID supported by `ColModernVBert`. |
| `CPU_THREADS` | `4` | CPU thread count when running without a GPU. |
| `ENABLE_CPU_MULTIPROCESSING` | `false` | Reserved flag; currently unused. |
| `HUGGINGFACE_HUB_CACHE` / `HF_HOME` | unset | Set to reuse a local HF cache. |

Example:
```bash
export COLPALI_MODEL_ID="ModernVBERT/colmodernvbert-merged"
export HUGGINGFACE_HUB_CACHE="$HOME/.cache/huggingface"
```

---

## 4. Running the API Locally

```bash
cd colpali
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

Then open http://localhost:7000/docs for the Swagger UI (syntax highlighting is disabled to keep huge embedding payloads from crashing the viewer).

When using a GPU, confirm that:

```python
python - <<'PY'
import torch
print(torch.cuda.is_available(), torch.cuda.get_device_name(0))
PY
```

reports `True` and the expected device name before starting the server.

---

## 5. Troubleshooting

- **FlashAttention warnings during start-up**: ensure the model is on CUDA and loaded in `float16/bfloat16`. The app already takes care of this but the warning can appear briefly if PyTorch loads lazily – it is safe to ignore after the “Model dtype: torch.float16” line.
- **“Failed to find C compiler”**: install the system build tools (Linux: `build-essential ninja pkg-config`; Windows: MSVC build tools or use WSL). FlashAttention triggers this when the compiler is missing.
- **Token boundary warning** (`Non-contiguous image tokens`): indicates the tokenizer returned image tokens in multiple spans. Usually harmless unless you expect a single contiguous block – double-check the upstream processor if it’s frequent.
- **Hugging Face throttling**: set `HF_HOME`/`HUGGINGFACE_HUB_CACHE` to a persistent directory so you don’t re-download the 5 GB model every run.

---

## 6. Docker vs Local

| Scenario | Recommendation |
|----------|----------------|
| Quick local tweaks on CPU | Follow the steps above, run via `uvicorn --reload`. |
| Production GPU inference | Use the `Dockerfile.gpu` via `docker compose --profile gpu up`. |
| CPU-only deployment | Build `Dockerfile.cpu` or install CPU torch locally. |

Both the Docker images and the local setup ultimately run `colpali/app.py`; keep them in sync when you update the service logic.
