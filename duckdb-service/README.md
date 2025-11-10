# DuckDB Service

Standalone HTTP API service for DuckDB OCR data storage and querying.

## Features

- REST API for storing and querying OCR results
- Full-text search across documents
- Statistics and analytics
- Persistent storage in DuckDB database

## API Endpoints

### Health Check
```
GET /health
```

### Store OCR Result
```
POST /ocr/store
```

### Search OCR Data
```
POST /ocr/search
```

### Get Statistics
```
POST /ocr/stats
```

### Get Specific Result
```
GET /ocr/result/{filename}/{page_number}
```

## Environment Variables

- `DB_PATH`: Path to DuckDB database file (default: `/var/lib/duckdb/snappy.db`)

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

## Docker

```bash
docker build -t duckdb-service .
docker run -p 8300:8300 -v duckdb_data:/var/lib/duckdb duckdb-service
```
