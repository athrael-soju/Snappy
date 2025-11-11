FROM python:3.11-slim

LABEL maintainer="Snappy Team"
LABEL description="DuckDB Analytics Service for OCR Data"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p /app/data /app/ui

# Copy UI files (will be empty initially)
COPY ui /app/ui

# Set environment variables
ENV DUCKDB_DATABASE_PATH=/app/data/ocr_data.duckdb
ENV DUCKDB_API_HOST=0.0.0.0
ENV DUCKDB_API_PORT=8300
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8300/health').raise_for_status()" || exit 1

# Run the application
CMD ["python", "app.py"]
