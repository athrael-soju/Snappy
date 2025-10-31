# DeepSeek OCR Service

This FastAPI service wraps the `deepseek-ai/DeepSeek-OCR` vision-language model
so Snappy can request OCR, layout grounding, and figure/table parsing as a
standalone microservice. The backend proxies requests through `/ocr/*` routes
when the integration is enabled, while you can also run the service on its own
for batch experiments.

The service expects an NVIDIA GPU (CUDA) for production workloads, but it can
fall back to CPU for smoke tests. It exposes lightweight health and metadata
endpoints, enforces upload limits, and returns structured responses with
bounding boxes and optional captions.

---

## Quick Start (Docker)

```bash
cd deepseek-ocr

# Build and run with GPU access (recommended)
docker compose up -d --build

# Override the published port (defaults to 8200)
API_PORT=9210 docker compose up -d --build
```

The Compose file mounts `/models` so the Hugging Face cache persists across
restarts. GPU access is requested via the `deploy.resources.reservations` block;
make sure you have the NVIDIA Container Toolkit installed.

When running the full Snappy stack, start the service using the `ocr` profile in
the root `docker-compose.yml`:

```bash
docker compose --profile ocr up -d --build
```

Then enable the integration from the Configuration UI (`DEEPSEEK_OCR_ENABLED`).

> **FlashAttention:** provide a prebuilt wheel via `--build-arg FLASH_ATTN_WHEEL_URL=...`
> when building the image, or allow the Dockerfile to attempt a source build. If
> the package is unavailable the service automatically falls back to eager
> attention.

---

## Running Locally

```bash
cd deepseek-ocr
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8200 --reload
```

Set `CUDA_VISIBLE_DEVICES` if you need to restrict which GPU is used. On CPU the
service will log a warning because inference latency increases significantly.

---

## Configuration Reference

`.env` mirrors the defaults consumed by `ServiceSettings` inside `main.py`.
Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODEL_NAME` | `deepseek-ai/DeepSeek-OCR` | Hugging Face model to load. |
| `HF_HOME` | `/models` | Cache directory (persisted via Docker volume). |
| `API_HOST` | `0.0.0.0` | Bind address for uvicorn. |
| `API_PORT` | `8200` | Service port. |
| `MAX_UPLOAD_SIZE_MB` | `100` | Hard limit for incoming files. |
| `BASE_SIZE` | `1024` | Default base resize dimension when callers omit it (minimum `512`). |
| `IMAGE_SIZE` | `640` | Default image size parameter (minimum `512`). |
| `CROP_MODE` | `true` | Default crop mode flag. |
| `DEFAULT_PROFILE` | `gundam` | Profile preset controlling base/image sizing (`gundam`, `tiny`, `small`, `base`, `large`). |
| `ENABLE_FLASH_ATTN` | `true` | Attempt to load the model with FlashAttention 2 (falls back automatically when unavailable). |
| `RETURN_MARKDOWN` | `false` | Include markdown output (with embedded figures) when callers omit the flag. |
| `RETURN_FIGURES` | `false` | Include base64 figure crops by default (automatically enabled when markdown is requested). |
| `ALLOWED_ORIGINS` | `*` | Optional CORS override (comma-separated). |

The Snappy backend adds higher-level configuration keys (`DEEPSEEK_OCR_*`) so
you can control defaults and timeouts from the runtime configuration panel.

---

### Preset Profiles

| Key | Base Size | Image Size | Crop Mode |
|-----|-----------|------------|-----------|
| Gundam | 1024 | 640 | True |
| Tiny | 512 | 512 | False |
| Small | 640 | 640 | False |
| Base | 1024 | 1024 | False |
| Large | 1280 | 1280 | False |

Allowed base sizes: 512, 640, 1024, 1280. Allowed image sizes: 512, 640, 1024, 1280.

## API Surface

| Method | Path | Description |
|--------|------|-------------|

| `GET` | `/` | Service banner and docs pointer. |
| `GET` | `/health` | Reports whether the model is loaded and on which device. |
| `GET` | `/info` | Detailed configuration (model name, dtype, defaults, flash-attn status). |
| `GET` | `/presets` | Available profile presets and task aliases. |
| `POST` | `/api/ocr` | OCR inference endpoint used by the backend `/ocr/infer`. |

`POST /api/ocr` accepts `multipart/form-data` with an `image` file and optional
form fields (`mode`, `prompt`, `grounding`, `include_caption`, `find_term`,
`schema`, `profile`, `base_size`, `image_size`, `crop_mode`, `test_compress`,
`return_markdown`, `return_figures`). The response
includes:

```json
{
  "success": true,
  "text": "cleaned text or description",
  "raw_text": "raw model output",
  "markdown": "markdown representation optionally containing figure embeds",
  "boxes": [
    {"label": "Total", "box": [x1, y1, x2, y2]}
  ],
  "figures": [
    {
      "index": 1,
      "label": "image",
      "box": [10, 25, 320, 400],
      "data_uri": "data:image/png;base64,iVBORw0K..."
    }
  ],
  "image_dims": {"w": 2480, "h": 3508},
  "metadata": {
    "mode": "plain_ocr",
    "grounding": true,
    "base_size": 1024,
    "image_size": 640,
    "crop_mode": true,
    "include_caption": false,
    "elapsed_ms": 431,
    "profile": "gundam",
    "attention": "flash_attention_2"
  }
}
```

Bounding boxes are normalised to the original image dimensions and grounding
tags are removed from the display text.

?? **Sizing requirements:** `base_size` must be greater than or equal to `image_size`. The service enforces minimum values of 512 for `base_size` and 512 for `image_size` to avoid kernel-size runtime errors.

---

## Integration with Snappy

1. Start the DeepSeek OCR service (Docker profile or manual run).
2. In the backend configuration, set `DEEPSEEK_OCR_URL` if the service is not on
   the default `http://localhost:8200`.
3. Toggle `DEEPSEEK_OCR_ENABLED` to `True` and adjust defaults (mode, prompt,
   sizing profile, markdown/figure toggles, flash attention) as necessary.
4. Use the `/ocr/health` or `/ocr/info` endpoints to confirm connectivity before
   wiring OCR steps into your ingestion or chat workflows.

The backend exposes `/ocr/defaults`, `/ocr/health`, `/ocr/info`, and `/ocr/infer`
routes that fan out to this service. Frontend components can rely on those
endpoints without embedding service-specific secrets.

---

## Troubleshooting

- **Model fails to load** – confirm GPU memory availability and that the Hugging
  Face credentials (if required) are configured in the environment.
- **Slow inference** – running on CPU is intended only for validation. Switch to
  a CUDA host or reduce `BASE_SIZE`/`IMAGE_SIZE` via configuration.
- **FlashAttention missing?** – supply a compatible `flash-attn` wheel via the
  Docker build argument or install build essentials so the fallback compilation
  can succeed. The service automatically falls back to eager attention if the
  kernels are unavailable.
- **CORS errors** – set `ALLOWED_ORIGINS` to the frontend origin when calling
  the service directly from the browser (the backend proxy already handles
  CORS).
- **Timeouts** – increase `DEEPSEEK_OCR_TIMEOUT` in the backend configuration or
  optimise image preprocessing.

Logs include upload size violations, temporary file cleanup, and any exceptions
raised during inference. Enable debug logging via `LOG_LEVEL=DEBUG` if you need
additional detail during development.
