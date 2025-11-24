# ColPali Embedding Service

FastAPI service for ColModernVBert/ColPali embeddings. The Snappy backend calls it for query and image embeddings; you can also run it standalone for experiments.

## Quick start (Docker)
```bash
cd colpali
docker compose up -d --build
```
Exposes `http://localhost:7000`. In Compose, the backend reaches it at `http://colpali:7000`.

## Local run
```bash
cd colpali
python -m venv .venv
. .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload
```

## Key settings
| Variable | Purpose |
| --- | --- |
| `COLPALI_MODEL_ID` | HF model id (default `ModernVBERT/colmodernvbert-merged`). |
| `CPU_THREADS` | Torch thread count when on CPU. |
| `HUGGINGFACE_HUB_CACHE` / `HF_HOME` | Cache location for model downloads. |

Hardware is auto-detected in order: CUDA -> MPS -> CPU.

## API surface
- `GET /health`, `GET /info`
- `POST /patches` - estimate patch grid
- `POST /embed/queries` - text to embeddings
- `POST /embed/images` - images to multivector embeddings

Example:
```bash
curl -X POST http://localhost:7000/embed/queries \
  -H "Content-Type: application/json" \
  -d '{"queries": ["modern architecture"]}'
```
