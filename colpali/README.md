# ColPali Embedding API – Morty™’s Vision Engine

Morty inherits this FastAPI service from Snappy to generate page-level embeddings and patch metadata. The branding is new, but the endpoints and behaviors remain identical.

- **Application:** `colpali/app.py`  
- **In-container port:** `7000`  
- **Published ports:** `7001` (CPU) and `7002` (GPU) via docker compose  
- **Default model:** `vidore/colqwen2.5-v0.2`

## API Endpoints

- `GET /health` – Reports readiness and selected device.  
- `GET /info` – Returns device details, dtype, embedding dimensionality, and `image_token_id`.  
- `POST /patches` – Computes grid boundaries for image patches.  
- `POST /embed/queries` – Generates embeddings for text queries.  
- `POST /embed/images` – Produces image embeddings with patch metadata.

## Docker Compose Workflow

```bash
# From colpali/

# CPU profile
docker compose up -d api-cpu
# -> http://localhost:7001

# GPU profile (requires NVIDIA Container Toolkit)
docker compose up -d api-gpu
# -> http://localhost:7002
```

Model downloads persist in the shared `hf-cache` volume mounted at `/data/hf-cache`.

## Connecting Morty

Configure the root `.env` consumed by the backend:

```bash
COLPALI_MODE=cpu      # or gpu
COLPALI_CPU_URL=http://localhost:7001
COLPALI_GPU_URL=http://localhost:7002
```

Morty selects the appropriate URL based on `COLPALI_MODE`. The backend skips proxying calls, so keep the service accessible from wherever Morty runs.

## Running Without Docker

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7000 --reload
```

- Direct access: `http://localhost:7000`  
- Match the docker compose ports by adding `--port 7001` or `7002` when needed.

## Operational Notes

- First run downloads the ColQwen weights; expect a sizable initial pull.  
- GPU mode requires the NVIDIA Container Toolkit (or equivalent drivers when running bare-metal).  
- For gated Hugging Face models, authenticate before starting the service.  
- Morty does not alter request or response formats; any Snappy automation continues to work.

## How Morty Uses ColPali

1. Morty’s backend requests embeddings during ingestion.  
2. Qdrant stores multivectors to enable high-recall visual search.  
3. The chat endpoint retrieves relevant page images and emits `kb.images` events for citation thumbnails.  
4. The Morty frontend combines streamed responses and citations to keep answers audit-ready.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
