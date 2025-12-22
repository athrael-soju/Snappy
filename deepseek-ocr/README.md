# DeepSeek OCR Service

FastAPI microservice for DeepSeek-OCR. **Requires an NVIDIA GPU with CUDA.**

## Quick start (Docker)
```bash
cd deepseek-ocr
docker compose up -d --build
```
Runs at `http://localhost:8200`. Included in `docker compose up -d` from the repo root.

## Local run
```bash
pip install -r requirements.txt
export MODEL_NAME=deepseek-ai/DeepSeek-OCR
export API_HOST=0.0.0.0
export API_PORT=8200
export HF_HOME=/models  # cache
python main.py
```

## API
- `GET /health`, `GET /info`
- `POST /api/ocr` with `image` (file/PDF) and optional params (`mode`, `task`, `prompt`)
Docs: http://localhost:8200/docs

## Notes
- GPU only; disable OCR in the main stack if no CUDA is available.
- For missing font errors (bounding boxes), install DejaVu fonts in the container.
