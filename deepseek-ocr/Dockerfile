# Backend Dockerfile - FastAPI + DeepSeek-OCR
FROM nvcr.io/nvidia/pytorch:25.09-py3

ARG FLASH_ATTN_WHEEL_URL=""

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0" \
    CC=/usr/bin/gcc \
    CXX=/usr/bin/g++

WORKDIR /app

# System build tools required for flash-attn (wheel fallback optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ninja-build \
    pkg-config \
    git \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies (and optional FlashAttention wheel)
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && if [ -n "$FLASH_ATTN_WHEEL_URL" ]; then \
      echo "Installing FlashAttention wheel from $FLASH_ATTN_WHEEL_URL"; \
      pip install "$FLASH_ATTN_WHEEL_URL"; \
    else \
      echo "Attempting to install flash-attn from PyPI (will skip on failure)"; \
      pip install flash-attn --no-build-isolation || echo "flash-attn installation skipped"; \
    fi

# Copy backend code
COPY main.py .

EXPOSE 8200

# Use main entrypoint so API_HOST/API_PORT envs are respected
CMD ["python", "main.py"]
