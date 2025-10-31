# CLAUDE.md - PaddleOCR-VL Service

This file provides comprehensive guidance to Claude Code (claude.ai/code) and developers working with the PaddleOCR-VL service.

## Repository Overview

**PaddleOCR-VL Service** is a GPU-accelerated document OCR microservice that provides RESTful API access to PaddlePaddle's PaddleOCR-VL model. It extracts structured information from documents including text, tables, charts, and formulas in 109 languages.

**Tech Stack:**
- **Framework**: FastAPI (Python 3.10)
- **OCR Engine**: PaddleOCR-VL 0.9B (NaViT + ERNIE-4.5)
- **GPU**: NVIDIA L4 (CUDA 12.4)
- **Deployment**: Docker + docker-compose
- **Target**: AWS EC2 g6.xlarge (us-west-2)

## Project Structure

```
paddleocr-vl-service/
├── config/                         # Application configuration
│   ├── __init__.py
│   ├── settings.py                # Pydantic settings (env vars)
│   └── logging_config.py          # Logging setup
├── services/                       # Business logic layer
│   ├── __init__.py
│   └── paddleocr_vl_service.py    # PaddleOCR-VL wrapper (singleton)
├── models/                         # Pydantic data models
│   ├── __init__.py
│   └── api_models.py              # Request/response schemas
├── routers/                        # API endpoints
│   ├── __init__.py
│   └── ocr_router.py              # OCR extraction endpoint
├── main.py                         # FastAPI application + lifespan
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Multi-stage GPU build
├── docker-compose.yml              # Docker Compose config
├── .env.template                   # Environment variables template
├── .gitignore                      # Git ignore patterns
├── README.md                       # User-facing documentation
└── CLAUDE.md                       # This file (technical guide)
```

## Architecture

### Service Layers

```
┌─────────────────────────────────────────────────┐
│              Client (HTTP Request)              │
└──────────────────┬──────────────────────────────┘
                   │ Multipart file upload
                   ▼
┌─────────────────────────────────────────────────┐
│          FastAPI Application (main.py)          │
│  - CORS middleware                              │
│  - Lifespan management                          │
│  - Global exception handler                     │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         OCR Router (routers/ocr_router.py)      │
│  - File validation (size, extension)           │
│  - Multipart file handling                      │
│  - Response formatting                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│   PaddleOCR-VL Service (services/...)           │
│  - Lazy initialization (singleton)              │
│  - Thread-safe pipeline management              │
│  - Image bytes → temp file → processing         │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         PaddleOCR-VL Pipeline (GPU)             │
│  - NaViT visual encoder (dynamic resolution)   │
│  - ERNIE-4.5-0.3B language model                │
│  - Grouped Query Attention (GQA)                │
│  - Output: Raw PaddleOCR-VL JSON       │
└─────────────────────────────────────────────────┘
```

### Key Design Patterns

**1. Singleton Pattern** (`paddleocr_vl_service.py`)
- Ensures only one PaddleOCR-VL pipeline instance
- Thread-safe initialization with double-checked locking
- Reduces memory footprint and startup time

**2. Lazy Loading**
- Pipeline initializes on first API request, not startup
- Improves container startup time (critical for health checks)
- Model download (~2GB) happens automatically on first use

**3. Temporary File Handling**
- API receives bytes -> write to temp file -> process -> delete
- PaddleOCR-VL requires file paths, not in-memory bytes
- Automatic cleanup even on errors

**4. Raw Result Passthrough** (`services/paddleocr_vl_service.py`, `routers/ocr_router.py`)
- Uses PaddleOCR-VL's `save_to_json()` to return canonical raw output
- Removes fragile regex parsing and markdown synthesis
- Automatically surfaces new upstream fields without code changes

**5. Lifespan Management**
- FastAPI async context manager for startup/shutdown
- Logs configuration on startup
- Graceful cleanup on shutdown

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Purpose:** Container health check, monitoring

**Response:**
```json
{
  "status": "healthy",
  "service": "PaddleOCR-VL Service",
  "version": "1.0.0",
  "gpu_enabled": true,
  "pipeline_ready": false,  // false until first request
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Usage:**
- Docker health check: `curl -f http://localhost:8000/health`
- Monitoring: Check `pipeline_ready` for model load status
- GPU verification: Check `gpu_enabled` matches config

### 2. Extract Document

**Endpoint:** `POST /api/v1/ocr/extract-document`

**Purpose:** OCR processing of images/PDFs

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (UploadFile)
- Max size: 50MB (configurable)
- Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.pdf`

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ocr/extract-document \
  -F "file=@document.jpg" \
  -H "Accept: application/json"
```

**Response:**
```json
{
  "success": true,
  "message": "Document processed successfully. Found 3 results.",
  "processing_time": 5.23,
  "results": [
    {
      "type": "text",
      "bbox": [10, 20, 200, 50],
      "content": "Document heading",
      "confidence": 0.98
    },
    {
      "type": "table",
      "bbox": [10, 60, 400, 200],
      "confidence": 0.92,
      "structure": {"rows": 5, "columns": 3}
    },
    {
      "type": "image",
      "bbox": [420, 80, 640, 360],
      "confidence": 0.87,
      "description": "Embedded chart"
    }
  ],
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format or empty file
- `413 Request Entity Too Large`: File exceeds 50MB
- `500 Internal Server Error`: Processing error (see logs)

## Configuration

### Environment Variables

All settings in `config/settings.py` can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | PaddleOCR-VL Service | Service name |
| `APP_VERSION` | 1.0.0 | Service version |
| `APP_PORT` | 8000 | HTTP port |
| `APP_HOST` | 0.0.0.0 | Bind address |
| `DEBUG` | false | Debug mode (enables reload) |
| `USE_GPU` | true | Enable GPU acceleration |
| `DEVICE` | gpu | Device type (gpu/cpu) |
| `MAX_UPLOAD_SIZE` | 52428800 | Max file size (50MB) |
| `MAX_CONCURRENT_REQUESTS` | 3 | Limit concurrent processing |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | json | Log format (json/text) |

### Logging

**Structured JSON Logs** (default):
```json
{"timestamp": "2025-01-15 10:30:00", "level": "INFO", "logger": "main", "message": "Starting up"}
```

**Text Logs** (for development):
```
2025-01-15 10:30:00 - main - INFO - Starting up
```

**Suppressed Loggers:**
- `paddleocr`: Set to WARNING (very verbose)
- `ppocr`: Set to WARNING
- `PIL`: Set to WARNING
- `urllib3`: Set to WARNING

## Deployment

### Prerequisites

**AWS EC2 g6.xlarge Instance:**
- Region: us-west-2
- GPU: NVIDIA L4 (24GB VRAM)
- vCPUs: 4
- RAM: 16GB
- Storage: 100GB gp3 EBS
- AMI: Ubuntu 22.04 with CUDA 12.4+

**Required Software:**
- Docker 24.0+
- Docker Compose 2.20+
- NVIDIA Container Toolkit

### Step 1: Create EC2 Instance

```bash
# Create key pair
aws ec2 create-key-pair \
  --region us-west-2 \
  --key-name paddleocr-vl-key \
  --query 'KeyMaterial' \
  --output text > paddleocr-vl-key.pem

chmod 400 paddleocr-vl-key.pem

# Create security group
aws ec2 create-security-group \
  --region us-west-2 \
  --group-name paddleocr-vl-sg \
  --description "Security group for PaddleOCR-VL service"

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --region us-west-2 \
  --group-name paddleocr-vl-sg \
  --protocol tcp \
  --port 22 \
  --cidr <YOUR_IP>/32

# Allow HTTP on port 8000
aws ec2 authorize-security-group-ingress \
  --region us-west-2 \
  --group-name paddleocr-vl-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Launch instance (Ubuntu 22.04 Deep Learning AMI with CUDA)
aws ec2 run-instances \
  --region us-west-2 \
  --image-id ami-0xyz... \  # Ubuntu 22.04 CUDA AMI
  --instance-type g6.xlarge \
  --key-name paddleocr-vl-key \
  --security-groups paddleocr-vl-sg \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}'
```

### Step 2: Configure Instance

```bash
# SSH into instance
ssh -i paddleocr-vl-key.pem ubuntu@<PUBLIC_IP>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### Step 3: Deploy Service

```bash
# Clone repository
git clone <repository-url>
cd paddleocr-vl-service

# Create .env file (optional, uses defaults)
cp .env.template .env

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify service
curl http://localhost:8000/health
```

### Step 4: Test from Local Machine

```bash
# Test health check
curl http://<EC2_PUBLIC_IP>:8000/health

# Test OCR extraction
curl -X POST http://<EC2_PUBLIC_IP>:8000/api/v1/ocr/extract-document \
  -F "file=@/Users/zhangshengjie/Downloads/scan_samples_en/scan_samples_en_63.jpg" \
  -o result.json

# View results
cat result.json | jq '.results[] | {type, confidence}'
```

## Performance Tuning

### GPU Memory Management

**Monitoring:**
```bash
# Real-time GPU monitoring
nvidia-smi -l 1

# Inside container
docker exec paddleocr-vl-service nvidia-smi
```

**Expected Usage:**
- Idle: ~100MB (minimal baseline)
- Model loaded: ~2GB (PaddleOCR-VL 0.9B)
- Processing: ~4-6GB (depends on image size)

**Optimization:**
- Set `MAX_CONCURRENT_REQUESTS=1` for large documents
- Use smaller images when possible (resize client-side)
- Monitor with `nvidia-smi` during load testing

### Startup Time Optimization

**Cold Start (first request):**
- Container startup: ~5s
- Model download: ~10-15s (if not cached)
- Model initialization: ~5-10s
- **Total:** ~20-30s

**Warm Start (subsequent requests):**
- Processing only: ~3-10s (depends on document complexity)

**Pre-warm Models:**
```bash
# Download models before first API request
docker exec -it paddleocr-vl-service python -c \
  "from paddleocr import PaddleOCRVL; PaddleOCRVL()"
```

**Volume Caching:**
Models are cached in `/home/appuser/.paddleocr` (persisted volume). Survives container restarts.

## Troubleshooting

### Issue: Model Download Fails

**Symptoms:**
- First request times out
- Logs show "Failed to download model"

**Solutions:**
1. Check internet connectivity from container:
   ```bash
   docker exec paddleocr-vl-service curl -I https://paddlepaddle.org.cn
   ```

2. Manually download models (one-time):
   ```bash
   docker exec paddleocr-vl-service python -c \
     "from paddleocr import PaddleOCRVL; PaddleOCRVL()"
   ```

3. Check proxy settings (if behind corporate firewall)

### Issue: GPU Not Detected

**Symptoms:**
- `gpu_enabled: false` in health check
- Logs show "GPU not available, using CPU"

**Solutions:**
1. Verify NVIDIA Container Toolkit:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
   ```

2. Check docker-compose GPU configuration:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```

3. Restart Docker daemon:
   ```bash
   sudo systemctl restart docker
   ```

### Issue: CUDA Out of Memory (OOM)

**Symptoms:**
- Processing fails with "CUDA out of memory"
- `nvidia-smi` shows 100% memory usage

**Solutions:**
1. Reduce concurrent requests:
   ```bash
   # In .env
   MAX_CONCURRENT_REQUESTS=1
   ```

2. Check for other GPU processes:
   ```bash
   nvidia-smi  # Look for other processes using GPU
   ```

3. Increase GPU size (upgrade to g6.2xlarge with 48GB VRAM)

### Issue: safetensors Import Error

**Symptoms:**
- Startup fails with "safetensors module not found"
- Or: "safetensors does not support PaddlePaddle"

**Solutions:**
This should not occur with the provided Dockerfile, but if it does:

```bash
# Install PaddlePaddle-compatible safetensors
docker exec paddleocr-vl-service pip install \
  https://paddle-whl.bj.bcebos.com/nightly/cu126/safetensors/safetensors-0.6.2.dev0-cp38-abi3-linux_x86_64.whl \
  --force-reinstall
```

**Root cause:** Standard `safetensors` package doesn't support PaddlePaddle tensors. Must use custom wheel.

### Issue: Processing Times Out

**Symptoms:**
- Request hangs for >60 seconds
- No response from server

**Solutions:**
1. Increase client timeout:
   ```bash
   curl --max-time 120 -X POST http://...
   ```

2. Check if model is still downloading (first request):
   ```bash
   docker-compose logs -f  # Watch for download progress
   ```

3. Verify instance has enough CPU/RAM:
   ```bash
   top  # Check CPU usage
   free -h  # Check memory usage
   ```

### Issue: File Upload Fails (413)

**Symptoms:**
- `413 Request Entity Too Large`

**Solutions:**
1. Check file size:
   ```bash
   ls -lh your-file.jpg  # Must be <50MB
   ```

2. Increase limit (in .env):
   ```bash
   MAX_UPLOAD_SIZE=104857600  # 100MB
   ```

3. Compress image before upload (client-side optimization)

## Development Workflow

### Local Testing (Platform Limitations)

**⚠️ CRITICAL PLATFORM REQUIREMENTS:**

This service is designed for **Linux x86_64 with NVIDIA GPU only**. Local testing without the target platform has significant limitations:

#### Supported Platforms

| Platform | PaddlePaddle | PaddleOCR | PaddleOCR-VL | Status |
|----------|--------------|-----------|--------------|---------|
| **Linux x86_64 + NVIDIA GPU** | ✅ 3.2.0 GPU | ✅ 3.3.0+ | ✅ Full support | **PRODUCTION** |
| **Linux x86_64 (CPU only)** | ✅ 3.2.0 CPU | ✅ 3.3.0+ | ⚠️ Untested | Development only |
| **macOS ARM64 (M1/M2/M3)** | ✅ 3.2.1 CPU | ✅ 3.3.0+ | ❌ **NOT SUPPORTED** | **INCOMPATIBLE** |
| **macOS x86_64 (Intel)** | ✅ CPU only | ✅ 3.3.0+ | ❌ **NOT SUPPORTED** | **INCOMPATIBLE** |
| **Windows** | ✅ CPU/GPU | ✅ 3.3.0+ | ⚠️ Untested | Not recommended |

#### Why macOS (M1/M2/M3) is NOT Compatible

**Blocking Issue:** PaddlePaddle-compatible `safetensors` wheel does not exist for ARM64 macOS.

**Technical Details:**
1. ✅ PaddlePaddle 3.2.1 CPU **installs successfully** on ARM64 macOS
2. ✅ PaddleOCR 3.3.0+ with doc-parser **installs successfully**
3. ❌ PaddleOCR-VL **initialization fails** with:
   ```
   safetensors_rust.SafetensorError: framework paddle is invalid
   ```

**Root Cause:**
- PaddleOCR-VL requires PaddlePaddle-specific `safetensors` (custom wheel)
- This wheel is only available as: `safetensors-0.6.2-cp38-abi3-linux_x86_64.whl`
- Standard PyPI `safetensors` doesn't support PaddlePaddle framework
- No ARM64 macOS build exists

### Adding New Features

**1. New API endpoint:**
- Add route in `routers/ocr_router.py`
- Add Pydantic models in `models/api_models.py`
- Update `main.py` to include router
- Update OpenAPI docs (automatic)

**2. Configuration changes:**
- Add setting in `config/settings.py`
- Update `.env.template`
- Document in `README.md` and this file

**3. Service logic:**
- Extend `services/paddleocr_vl_service.py`
- Maintain singleton pattern
- Add error handling

### Testing Checklist

Before committing:
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Test OCR with sample image
- [ ] Check logs for errors: `docker-compose logs`
- [ ] Verify GPU usage: `nvidia-smi`
- [ ] Test error cases (invalid file, too large, etc.)
- [ ] Update documentation if API changes

## Critical Dependencies

### PaddlePaddle GPU Installation Order

**⚠️ CRITICAL:** Must install in this exact order (Dockerfile handles this):

1. **PaddlePaddle GPU 3.2.0** (CUDA 12.6 compatible)
   ```bash
   pip install paddlepaddle-gpu==3.2.0 \
     -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
   ```

2. **PaddleOCR with doc-parser**
   ```bash
   pip install "paddleocr[doc-parser]>=3.3.0"
   ```

3. **PaddlePaddle-compatible safetensors** (custom wheel)
   ```bash
   pip install \
     https://paddle-whl.bj.bcebos.com/nightly/cu126/safetensors/safetensors-0.6.2.dev0-cp38-abi3-linux_x86_64.whl \
     --force-reinstall
   ```

**Why this order matters:**
- PaddleOCR depends on PaddlePaddle
- safetensors must be PaddlePaddle-compatible version
- Wrong order causes import errors or missing GPU support

### System Libraries (Ubuntu 22.04)

Required for PaddleOCR and image processing:
```
libglib2.0-0, libsm6, libxext6, libxrender1, libgomp1, libgl1-mesa-glx
```

## Model Information

### PaddleOCR-VL 0.9B

**Architecture:**
- Visual Encoder: NaViT-style dynamic resolution
- Language Model: ERNIE-4.5-0.3B
- Total Parameters: 0.9B
- Attention: Grouped Query Attention (16 heads, 2 KV heads)

**Capabilities:**
- **Text**: 109 languages (multilingual)
- **Tables**: Structure preservation, cell extraction
- **Formulas**: LaTeX output
- **Charts**: Data extraction from graphs

**Model Files:**
- Location: `/home/appuser/.paddleocr/models/`
- Size: ~2GB total
- Download: Automatic on first use
- Format: PaddlePaddle checkpoint + safetensors

**Performance:**
- SOTA vs pipeline-based solutions
- Competitive with 72B VLMs on DocVQA benchmarks
- Optimized for batch size = 1 (local inference)

## Monitoring

### Health Check Integration

For production monitoring, use the health endpoint:

```bash
# Prometheus-style check
curl -f http://localhost:8000/health || echo "unhealthy"

# JSON parsing for monitoring
curl -s http://localhost:8000/health | jq -r '.status'
```

### Metrics to Monitor

1. **Health Status**: `/health` returns 200 OK
2. **GPU Availability**: `.gpu_enabled == true`
3. **Pipeline Ready**: `.pipeline_ready == true` (after first request)
4. **Response Time**: `processing_time` field in API responses
5. **Error Rate**: Monitor 4xx/5xx responses
6. **GPU Memory**: `nvidia-smi --query-gpu=memory.used --format=csv`
7. **Container Status**: `docker ps | grep paddleocr-vl`

## Security Considerations

### File Upload Security

**Implemented:**
- File extension validation (whitelist)
- File size limits (50MB default)
- Temporary file cleanup (automatic)
- Non-root container user

**Recommended Additional Measures:**
- File content validation (magic bytes)
- Rate limiting (nginx/API gateway)
- Input sanitization for filenames
- Network isolation (VPC/security groups)

### Container Security

**Current:**
- Non-root user (`appuser`, UID 1000)
- Minimal base image (Ubuntu 22.04 runtime only)
- No unnecessary packages in final image
- Health checks enabled

**Production Recommendations:**
- Use read-only root filesystem
- Drop unnecessary Linux capabilities
- Scan images for vulnerabilities (Trivy, Snyk)
- Use secrets management for sensitive configs

## References

- **PaddleOCR-VL HuggingFace**: https://huggingface.co/PaddlePaddle/PaddleOCR-VL
- **PaddleOCR GitHub**: https://github.com/PaddlePaddle/PaddleOCR
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

## Changelog

### v1.0.0 (2025-01-15)
- Initial release
- FastAPI application with GPU support
- Multipart file upload endpoint
- Docker deployment with docker-compose
- Health check endpoint
- JSON and Markdown output formats

