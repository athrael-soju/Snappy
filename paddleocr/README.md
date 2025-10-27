# PaddleOCR-VL Service

Standalone Docker Compose stack for running the PaddleOCR-VL layout parsing server used by Snappy.

The container wraps the official `paddlex-genai-vllm-server` image, installs the matching FlashAttention wheel for CUDA 12.8 and PyTorch 2.8.0, and exposes the API on port `8118`.

## Prerequisites

- NVIDIA GPU with recent drivers
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on the host
- Docker Compose v2 (`docker compose`)

## Usage

```bash
cd paddleocr
docker compose up --pull always
```

The first startup pulls model weights and builds FlashAttention; subsequent runs reuse the cached volume (`paddleocr_cache`).

Stop the service with:

```bash
docker compose down
```

## Configuration

The Snappy backend expects the service at `http://localhost:8118` by default. Adjust `PADDLEOCR_URL` in the root `.env` file if you bind to a different host/port or run the container on another machine.

## Health Check

Once the logs show `Uvicorn running on http://0.0.0.0:8118`, test the service with:

```bash
curl -X POST http://localhost:8118/layout-parsing \
  -H "Content-Type: application/json" \
  -d '{"file":"<base64_encoded_image>","fileType":1}'
```

You should receive a JSON payload containing `layoutParsingResults`.
