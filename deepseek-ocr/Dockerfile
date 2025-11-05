# Backend Dockerfile - FastAPI + DeepSeek-OCR
FROM nvcr.io/nvidia/pytorch:25.09-py3

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py .

EXPOSE 8200

# Use main entrypoint so API_HOST/API_PORT envs are respected
CMD ["python", "main.py"]
