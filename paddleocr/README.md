# PaddleOCR-VL Service

Standalone Docker Compose stack for running the PaddleOCR-VL layout parsing server with an accompanying FastAPI proxy that provides OpenAPI docs.

- `paddleocr-upstream`: official `paddlex-genai-vllm-server` image with FlashAttention 2.8.3 preinstalled
- `paddleocr`: lightweight FastAPI proxy that forwards requests to the upstream service and exposes Swagger UI at `http://localhost:8118/docs`

## Prerequisites

- NVIDIA GPU with recent drivers
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on the host
- Docker Compose v2 (`docker compose`)

## Usage

```bash
cd paddleocr
docker compose up --pull always
```

The first startup pulls model weights and builds FlashAttention; subsequent runs reuse the cached volume (`paddleocr_cache`). When the proxy reports `Uvicorn running on http://0.0.0.0:8118`, open http://localhost:8118/docs for the interactive UI.

Stop the service with:

```bash
docker compose down
```

## Configuration

The Snappy backend expects the service at `http://localhost:8118` by default. Adjust `PADDLEOCR_URL` in the root `.env` file if you bind to a different host/port or run the container on another machine.

## Health Check

Use the `/health` endpoint exposed by the proxy or the OpenAPI UI to verify connectivity to the upstream container.
