# DeepSeek OCR Service

FastAPI-based microservice for DeepSeek-OCR document analysis and optical character recognition.

⚠️ **GPU Required**: This service requires an NVIDIA GPU with CUDA support.

## Overview

This service wraps the DeepSeek-OCR model in a RESTful API, providing powerful document understanding capabilities:

- **Markdown Conversion**: Convert documents to structured markdown with grounding
- **Plain OCR**: Extract raw text from images
- **Text Location**: Find and locate specific text in images with bounding boxes
- **Image Description**: Generate detailed descriptions of images
- **Custom Prompts**: Use custom prompts for specialized tasks

## Features

- 🚀 **FastAPI** - High-performance async API
- 🎯 **Multiple Processing Modes** - From tiny (512×512) to large (1280×1280)
- 📦 **Batch Processing** - PDF multi-page support
- 🎨 **Visual Grounding** - Bounding boxes for detected elements
- 🖼️ **Image Extraction** - Extract and embed figures from documents
- 🔄 **Docker Ready** - GPU-enabled container with NVIDIA runtime
- 🖥️ **GPU Only** - Optimized for NVIDIA CUDA acceleration

## Quick Start

### Standalone Development

⚠️ **Requires NVIDIA GPU with CUDA**

```bash
cd deepseek-ocr
docker compose up -d --build
```

This starts DeepSeek OCR in isolation. Perfect for:
- Testing OCR functionality independently
- Debugging OCR-specific issues
- Development without the full stack

The service will be available at `http://localhost:8200`.

### As Part of Full Stack

From the project root:

```bash
# ML profile (ColPali + DeepSeek OCR)
make up-ml

# Full profile (all services)
make up-full
```

**Note:** DeepSeek OCR is **not included** in the `minimal` profile since it requires GPU.

### Local Development

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**:
```bash
export MODEL_NAME=deepseek-ai/DeepSeek-OCR
export API_HOST=0.0.0.0
export API_PORT=8200
export HF_HOME=/models  # Model cache directory
```

3. **Run the Service**:
```bash
python main.py
```

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: `http://localhost:8200/docs`
- ReDoc: `http://localhost:8200/redoc`

### Endpoints

#### `GET /health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "model": "deepseek-ai/DeepSeek-OCR",
  "device": "cuda",
  "torch_dtype": "torch.bfloat16"
}
```

#### `GET /info`
Get model information and available options.

**Response**:
```json
{
  "model": "deepseek-ai/DeepSeek-OCR",
  "device": "cuda",
  "modes": ["Gundam", "Tiny", "Small", "Base", "Large"],
  "tasks": ["markdown", "plain_ocr", "locate", "describe", "custom"],
  "model_configs": { ... }
}
```

#### `POST /api/ocr`
Perform OCR on uploaded image or PDF.

**Parameters**:
- `image` (file): Image or PDF file to process
- `mode` (string, optional): Processing mode (default: "Gundam")
  - `Gundam`: 1024 base + 640 tiles with cropping (best balance)
  - `Tiny`: 512×512, fastest
  - `Small`: 640×640, quick
  - `Base`: 1024×1024, standard
  - `Large`: 1280×1280, highest quality
- `task` (string, optional): Task type (default: "markdown")
  - `markdown`: Convert to structured markdown
  - `plain_ocr`: Simple text extraction
  - `locate`: Find specific text (requires `custom_prompt`)
  - `describe`: Image description
  - `custom`: Custom prompt (requires `custom_prompt`)
- `custom_prompt` (string, optional): Custom prompt for locate/custom tasks
- `include_grounding` (boolean, optional): Include bounding boxes (default: true)
- `include_images` (boolean, optional): Extract and embed images (default: true)

**Response**:
```json
{
  "text": "Extracted text with grounding references...",
  "markdown": "# Cleaned markdown\n\n![Figure 1](data:image/png;base64,...)",
  "raw": "Raw model output...",
  "bounding_boxes": [
    {
      "x1": 100,
      "y1": 50,
      "x2": 300,
      "y2": 100,
      "label": "title"
    }
  ],
  "crops": ["base64_image_1", "base64_image_2"],
  "annotated_image": "base64_annotated_image"
}
```

## Processing Modes

| Mode | Base Size | Image Size | Crop Mode | Best For |
|------|-----------|------------|-----------|----------|
| **Gundam** | 1024 | 640 | ✅ | Best balance (recommended) |
| **Tiny** | 512 | 512 | ❌ | Fastest processing |
| **Small** | 640 | 640 | ❌ | Quick results |
| **Base** | 1024 | 1024 | ❌ | Standard quality |
| **Large** | 1280 | 1280 | ❌ | Highest quality |

## Task Types

### Markdown Conversion
```bash
curl -X POST "http://localhost:8200/api/ocr" \
  -F "image=@document.pdf" \
  -F "mode=Gundam" \
  -F "task=markdown"
```

### Plain OCR
```bash
curl -X POST "http://localhost:8200/api/ocr" \
  -F "image=@page.png" \
  -F "task=plain_ocr"
```

### Locate Text
```bash
curl -X POST "http://localhost:8200/api/ocr" \
  -F "image=@document.jpg" \
  -F "task=locate" \
  -F "custom_prompt=contact information"
```

### Image Description
```bash
curl -X POST "http://localhost:8200/api/ocr" \
  -F "image=@chart.png" \
  -F "task=describe"
```

### Custom Prompt
```bash
curl -X POST "http://localhost:8200/api/ocr" \
  -F "image=@form.pdf" \
  -F "task=custom" \
  -F "custom_prompt=<|grounding|>Extract all form fields and their values"
```

## Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8200

# Model Configuration
MODEL_NAME=deepseek-ai/DeepSeek-OCR
HF_HOME=/models
DEVICE=cuda  # GPU mode only

# CORS Settings
ALLOWED_ORIGINS=*  # Comma-separated list or '*' for all
```

## Docker Configuration

### GPU Support (Recommended)

The default `docker-compose.yml` includes GPU support. Ensure you have:
- NVIDIA GPU drivers installed
- NVIDIA Container Toolkit installed
- Docker with GPU support enabled

### CPU Mode

CPU execution is temporarily unsupported—run the GPU profile (`docker compose --profile gpu ...`) to use DeepSeek OCR.

## Integration with Snappy

This service is designed to integrate with the Snappy backend:

1. **Environment Variables** in Snappy's `.env`:
```bash
DEEPSEEK_OCR_ENABLED=true
DEEPSEEK_OCR_URL=http://localhost:8200  # or http://deepseek-ocr:8200 in Docker
DEEPSEEK_OCR_API_TIMEOUT=300
DEEPSEEK_OCR_MAX_WORKERS=4
DEEPSEEK_OCR_POOL_SIZE=20
```

2. **Docker Network**: Add to Snappy's `docker-compose.yml`:
```yaml
services:
  deepseek-ocr:
    build: ./deepseek-ocr
    container_name: deepseek-ocr
    ports:
      - "8200:8200"
    networks:
      - snappy-network
```

3. **Backend Usage**: The Snappy backend automatically uses DeepSeek OCR during indexing when enabled.

## Performance Considerations

- **GPU vs CPU**: DeepSeek OCR currently runs on GPU only; CPU fallback is unavailable
- **Batch Processing**: PDFs are processed page-by-page sequentially
- **Memory**: Large mode requires ~8GB GPU memory
- **Disk**: Model weights are ~3GB, cached in `HF_HOME`

## Troubleshooting

### Model Download Issues
```bash
# Pre-download the model
python -c "from transformers import AutoModel; AutoModel.from_pretrained('deepseek-ai/DeepSeek-OCR', trust_remote_code=True)"
```

### GPU Not Detected
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check environment
python -c "import torch; print(torch.cuda.is_available())"
```

### Out of Memory
- Use smaller processing mode (Tiny or Small)
- Reduce image resolution before upload


### Font Errors (Bounding Boxes)
```bash
# Install DejaVu fonts in container
apt-get update && apt-get install -y fonts-dejavu-core
```

## Model Information

- **Model**: [deepseek-ai/DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR)
- **Architecture**: Vision-Language Model with grounding capabilities
- **Features**: Multi-scale processing, visual grounding, structured output
- **License**: Check model card on Hugging Face

## API Response Schema

### OCRResponse
```typescript
{
  text: string;              // Extracted text with grounding references
  markdown: string | null;   // Cleaned markdown with embedded images
  raw: string;               // Raw model output
  bounding_boxes: Array<{    // Detected bounding boxes
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    label: string;
  }>;
  crops: string[];           // Base64-encoded cropped images
  annotated_image: string | null;  // Base64-encoded annotated image
}
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality
```bash
# Format code
black main.py

# Type checking
mypy main.py

# Linting
ruff check main.py
```

## Contributing

Contributions are welcome! Please:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## License

This service is part of the Snappy project. See the main project LICENSE file.

## Credits

- **DeepSeek-OCR**: [deepseek-ai](https://huggingface.co/deepseek-ai)
- **Original Gradio Demo**: [merterbak/DeepSeek-OCR-Demo](https://huggingface.co/spaces/merterbak/DeepSeek-OCR-Demo)
- **FastAPI**: [tiangolo/fastapi](https://github.com/tiangolo/fastapi)

## Support

For issues related to:
- **Service API**: Open an issue in the Snappy repository
- **DeepSeek Model**: Check [DeepSeek-OCR model card](https://huggingface.co/deepseek-ai/DeepSeek-OCR)
- **Integration**: See [Snappy documentation](../README.md)
