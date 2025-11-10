FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt /app/

# Install DuckDB and required dependencies
FROM python:3.11-slim

WORKDIR /app

# Install DuckDB CLI and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and install DuckDB CLI
RUN wget -q https://github.com/duckdb/duckdb/releases/download/v1.1.3/duckdb_cli-linux-amd64.zip \
    && unzip duckdb_cli-linux-amd64.zip \
    && mv duckdb /usr/local/bin/ \
    && chmod +x /usr/local/bin/duckdb \
    && rm duckdb_cli-linux-amd64.zip

# Install Python dependencies
RUN pip install --no-cache-dir \
    duckdb==1.1.3 \
    fastapi==0.115.4 \
    uvicorn[standard]==0.32.0 \
    python-multipart==0.0.12

# Copy application files
COPY app.py /app/
COPY init_db.py /app/
COPY static/ /app/static/

# Create data directory
RUN mkdir -p /var/lib/duckdb

# Expose port for API
EXPOSE 8300

# Run the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8300"]
