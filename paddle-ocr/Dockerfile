# PaddleOCR Pipeline Service
# Runs full PaddleOCR-VL with PP-DocLayoutV3 for structured output with labels

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PaddlePaddle CPU and PaddleOCR with doc-parser
# PP-DocLayoutV3 runs on CPU here; heavy VLM inference is done by vLLM server
RUN pip install --no-cache-dir \
    paddlepaddle==3.2.1 \
    "paddleocr[doc-parser]>=3.4.0" \
    safetensors \
    fastapi \
    uvicorn \
    python-multipart \
    pillow

# Copy application code
COPY app.py /app/

# Expose port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Run the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8200"]
