FROM python:3.10-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    curl \
    ffmpeg \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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

# Use system Python (3.10) from base image
RUN pip install --no-cache-dir -U pip setuptools wheel packaging

COPY --chown=1000 ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
COPY --chown=1000 . ${HOME}/app
ENV PYTHONPATH=${HOME}/app \
    PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]