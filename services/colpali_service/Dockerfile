FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    # python build dependencies \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user only if it doesn't exist
RUN if ! id -u 1000 >/dev/null 2>&1; then \
    useradd -m -u 1000 user; \
    fi && \
    mkdir -p /home/user && \
    chown -R 1000:1000 /home/user

USER 1000
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:${PATH}
WORKDIR ${HOME}/app

RUN curl https://pyenv.run | bash
ENV PATH=${HOME}/.pyenv/shims:${HOME}/.pyenv/bin:${PATH}
ARG PYTHON_VERSION=3.10.12
RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash && \
    pip install --no-cache-dir -U pip setuptools wheel && \
    pip install packaging ninja

# Upgrade pip and install PyTorch with CUDA 12.9 support
RUN pip install --no-cache-dir --upgrade pip

# Install other requirements
COPY --chown=1000 ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu129
# Copy the application code
COPY --chown=1000 . .

# Set the working directory to the service directory
WORKDIR ${HOME}/app/services/colpali_service

# Set environment variables
ENV PYTHONPATH=${HOME}/app
ENV MODEL_NAME=nomic-ai/colnomic-embed-multimodal-3b

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
