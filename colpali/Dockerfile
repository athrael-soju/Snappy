# Dockerfile for ColPali - Installs CUDA-enabled PyTorch
# Runtime auto-detects GPU/MPS/CPU via torch.cuda.is_available()

FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HUGGINGFACE_HUB_CACHE=/data/hf-cache \
    HF_HOME=/data/hf-cache

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    ninja-build \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set compiler environment for potential GPU builds
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"

# Copy requirements first for better caching
COPY requirements.txt ./

# Install CUDA-enabled PyTorch (works on CPU too, GPU used at runtime if available)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.7.0 \
        torchvision==0.22.0 \
        --index-url https://download.pytorch.org/whl/cu128 && \
    pip install --no-cache-dir \
        https://github.com/loscrossos/lib_flashattention/releases/download/v2.7.4.post1_crossos00/flash_attn-2.7.4.post1+cu129torch2.7.0-cp312-cp312-linux_x86_64.whl && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

EXPOSE 7000

# Start API - runtime auto-detects cuda/mps/cpu
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
