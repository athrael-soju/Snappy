# GPU-enabled Dockerfile for ColModernVBert on RTX 50-series
# Torch 2.7.0 + Python 3.12 + FlashAttention 2.7.4.post1 (cp312)

FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HUGGINGFACE_HUB_CACHE=/data/hf-cache \
    HF_HOME=/data/hf-cache

# --- Versions & sources -------------------------------------------------------
# Official torch 2.7.0 wheels are published for CUDA 12.8 ("cu128").
# If you truly need cu129 with torch==2.7.0, provide a custom torch wheel URL.
ARG TORCH_VERSION="2.7.0"
ARG TORCHVISION_VERSION="0.22.0"
ARG TORCH_INDEX_URL="https://download.pytorch.org/whl/cu128"
# e.g. https://your-artifacts/torch-2.7.0+cu129-...whl
ARG TORCH_WHL_URL=""   

# FlashAttention wheel built against torch 2.7.0 (cp312). Provide your artifact URL.
ARG FLASH_ATTN_WHEEL_URL="https://github.com/loscrossos/lib_flashattention/releases/download/v2.7.4.post1_crossos00/flash_attn-2.7.4.post1+cu129torch2.7.0-cp312-cp312-linux_x86_64.whl"

# Create workdir
WORKDIR /app

# System deps (git for installing from GitHub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    ninja-build \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Make sure PyTorch can find the toolchain when compiling flash-attn/runtime kernels
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"

# Install PyTorch first (so packages that depend on torch see it),
# then app deps, then FlashAttention.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && if [ -n "$TORCH_WHL_URL" ]; then \
    echo "Installing custom torch wheel from \$TORCH_WHL_URL"; \
    pip install --no-cache-dir "$TORCH_WHL_URL" torchvision=="${TORCHVISION_VERSION}"; \
    else \
    echo "Installing official torch==${TORCH_VERSION} (cu128) & torchvision==${TORCHVISION_VERSION}"; \
    pip install --no-cache-dir torch=="${TORCH_VERSION}" torchvision=="${TORCHVISION_VERSION}" --index-url "${TORCH_INDEX_URL}"; \
    fi \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "${FLASH_ATTN_WHEEL_URL}"

# Copy app
COPY . /app
COPY main.py .

EXPOSE 8200

# Use main entrypoint so API_HOST/API_PORT envs are respected
CMD ["python", "main.py"]