# DeepSeek OCR Service

FastAPI microservice for [DeepSeek-OCR-2](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2) (3.3B params, bfloat16). **Requires an NVIDIA GPU with CUDA.**

Upgraded from DeepSeek-OCR v1 to v2 for improved text extraction, bounding box accuracy, and Gundam mode support at higher resolution (base_size=1024, image_size=768).

## Quick start (Docker)
```bash
cd deepseek-ocr
docker compose up -d --build
```
Runs at `http://localhost:8200`. Included in the default `docker compose up -d`.

## Local run
```bash
pip install -r requirements.txt
export MODEL_NAME=deepseek-ai/DeepSeek-OCR-2
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
