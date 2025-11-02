---
title: OCRdeepSeekService
emoji: ⚡
colorFrom: green
colorTo: green
sdk: docker
pinned: false
---

# DeepSeek-OCR Service

OCR service using DeepSeek-OCR for maximum quality text extraction.

## Features

- High-quality OCR using DeepSeek-OCR model
- FastAPI-based REST API
- Support for JPEG, PNG, and WebP images
- Configurable quality settings
- Rate limiting and API key authentication
- Compatible with HuggingFace Spaces

## Quick Start with Docker Compose

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional)
```

### 2. Start the Service

**Choose CPU or GPU profile:**

```bash
# CPU-only (no GPU required)
docker compose --profile cpu up -d --build

# GPU-accelerated (requires NVIDIA GPU + drivers)
docker compose --profile gpu up -d --build

# View logs
docker compose logs -f
```

### 3. Test the Service

```bash
# Health check
curl http://localhost:7860/

# OCR request (requires image file)
curl -X POST http://localhost:7860/ocr \
  -H "X-API-Key: dev-key-change-in-production" \
  -F "file=@your-image.png"
```

### 4. Stop the Service

```bash
docker compose down
```

## GPU Support

The GPU profile includes:
- **PyTorch 2.7.0** with CUDA 12.8 support
- **Flash Attention 2.7.4** for optimized transformer performance
- **Python 3.12** for latest features
- Automatic GPU detection and utilization

**Requirements:**
- NVIDIA GPU with compute capability 8.0+ (RTX 30/40/50 series)
- NVIDIA drivers installed
- Docker with NVIDIA Container Toolkit

## Configuration

Environment variables (see `.env.example`):

- `SERVICE_API_KEY` - API key for authentication (default: dev-key-change-in-production)
- `REQUIRE_API_KEY` - Enable API key requirement (default: false)
- `PUBLIC_HOST` - Public hostname (default: localhost)
- `PUBLIC_PORT` - Public port (default: 7860)
- `DEEPSEEK_BASE_SIZE` - Base image size (default: 1024)
- `DEEPSEEK_IMAGE_SIZE` - Processing image size (default: 640)
- `DEEPSEEK_GPU_COUNT` - Number of GPUs to use (default: all)
- `RATE_LIMIT_REQUESTS` - Max requests per window (default: 30)
- `MAX_UPLOAD_BYTES` - Max file upload size in bytes (default: 5242880)

## Integration with Main Project

To connect this service to the main Snappy network:

1. Uncomment the network sections in `docker-compose.yml`
2. Start from the main project directory:
   ```bash
   docker compose -f docker-compose.yml -f deepseek-ocr/docker-compose.yml up -d
   ```

## API Endpoints

- `GET /` - Health check
- `POST /ocr` - Perform OCR on uploaded image
- `GET /docs` - Interactive API documentation

## HuggingFace Spaces

This service is compatible with HuggingFace Spaces. The configuration is in the YAML frontmatter above.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
