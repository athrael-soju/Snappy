# DuckDB Analytics Service

A FastAPI-based service that stores and analyzes OCR data using DuckDB.

## Features

- **Persistent Storage**: Store OCR results in a DuckDB database for long-term analytics
- **SQL Query Interface**: Execute SQL queries against OCR data via REST API
- **DuckDB-Wasm UI**: Interactive web interface for data exploration
- **Full-Text Search**: Search across all OCR text content
- **Document Management**: List, retrieve, and delete documents
- **Statistics**: Aggregate statistics and insights

## Architecture

```
┌─────────────────┐
│   Backend API   │
│                 │
│  OCR Storage    │───┐
└─────────────────┘   │
                      │ HTTP POST
                      ▼
              ┌───────────────┐
              │ DuckDB Service│
              │               │
              │ ┌───────────┐ │
              │ │  FastAPI  │ │
              │ └─────┬─────┘ │
              │       │       │
              │ ┌─────▼─────┐ │
              │ │  DuckDB   │ │
              │ │  Engine   │ │
              │ └───────────┘ │
              │               │
              │ ┌───────────┐ │
              │ │ DuckDB UI │ │
              │ └───────────┘ │
              └───────────────┘
```

## Database Schema

### `ocr_pages` Table

Stores OCR results for each page:

| Column              | Type      | Description                        |
|---------------------|-----------|-------------------------------------|
| id                  | INTEGER   | Primary key                        |
| provider            | VARCHAR   | OCR provider (e.g., deepseek-ocr)  |
| version             | VARCHAR   | Provider version                   |
| filename            | VARCHAR   | Document filename                  |
| page_number         | INTEGER   | Page number                        |
| text                | TEXT      | Extracted plain text               |
| markdown            | TEXT      | Markdown-formatted text            |
| raw_text            | TEXT      | Raw OCR text                       |
| regions             | JSON      | Text regions with bounding boxes   |
| extracted_at        | TIMESTAMP | Extraction timestamp               |
| storage_url         | VARCHAR   | MinIO storage URL                  |
| document_id         | VARCHAR   | Document identifier                |
| pdf_page_index      | INTEGER   | PDF page index                     |
| total_pages         | INTEGER   | Total pages in document            |
| page_width_px       | INTEGER   | Page width in pixels               |
| page_height_px      | INTEGER   | Page height in pixels              |
| image_url           | VARCHAR   | Page image URL                     |
| image_storage       | VARCHAR   | Image storage location             |
| extracted_images    | JSON      | Extracted images metadata          |
| created_at          | TIMESTAMP | Record creation time               |

**Indexes:**
- `idx_filename` - For document lookups
- `idx_page_number` - For page queries
- `idx_provider` - For provider filtering
- `idx_extracted_at` - For temporal queries
- `idx_text_fts` - For full-text search

## API Endpoints

### Health & Info

- `GET /` - Service information
- `GET /health` - Health check
- `GET /info` - Database statistics

### Data Storage

- `POST /ocr/store` - Store single page OCR data
- `POST /ocr/store/batch` - Store multiple pages

### Data Retrieval

- `GET /ocr/documents` - List all documents
- `GET /ocr/documents/{filename}` - Get document info
- `GET /ocr/pages/{filename}/{page_number}` - Get page data
- `DELETE /ocr/documents/{filename}` - Delete document

### Analytics

- `POST /query` - Execute SQL query
- `GET /stats` - Aggregate statistics
- `POST /search/text` - Full-text search

### UI

- **DuckDB UI Extension** - Access at `http://localhost:4213` (when service is running)

## Configuration

Environment variables:

```bash
DUCKDB_DATABASE_PATH=./data/ocr_data.duckdb  # Database file path
DUCKDB_API_HOST=0.0.0.0                       # API host
DUCKDB_API_PORT=8300                          # API port
LOG_LEVEL=INFO                                # Logging level
```

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

The service will be available at `http://localhost:8300`.

### Docker Setup

```bash
# Build image
docker build -t duckdb:latest .

# Run container
docker run -p 8300:8300 -v $(pwd)/data:/app/data duckdb:latest
```

### With Docker Compose

The service is included in the root `docker-compose.yml`:

```bash
# Start with CPU profile
docker compose --profile cpu up duckdb

# Start with GPU profile
docker compose --profile gpu up duckdb
```

## Usage Examples

### Store OCR Data

```python
import requests

data = {
    "provider": "deepseek-ocr",
    "version": "1.0",
    "filename": "document.pdf",
    "page_number": 1,
    "text": "Sample text...",
    "markdown": "# Sample\n\nSample text...",
    "regions": [],
    "extracted_at": "2025-11-11T12:00:00Z",
    "storage_url": "http://minio:9000/..."
}

response = requests.post("http://localhost:8300/ocr/store", json=data)
print(response.json())
```

### Query Data

```python
import requests

query = {
    "query": "SELECT filename, page_number, text FROM ocr_pages WHERE text LIKE '%keyword%'",
    "limit": 100
}

response = requests.post("http://localhost:8300/query", json=query)
result = response.json()

for row in result["rows"]:
    print(row)
```

### Search Text

```python
import requests

response = requests.post(
    "http://localhost:8300/search/text",
    params={"q": "search term", "limit": 50}
)
print(response.json())
```

### Get Statistics

```python
import requests

response = requests.get("http://localhost:8300/stats")
stats = response.json()

print(f"Total documents: {stats['total_documents']}")
print(f"Total pages: {stats['total_pages']}")
print(f"Database size: {stats['storage_size_mb']} MB")
```

## Integration with Backend

The DuckDB service is integrated with the backend OCR pipeline:

1. Document is uploaded and processed
2. OCR results are stored in MinIO
3. **Simultaneously**, OCR data is sent to DuckDB for analytics
4. DuckDB storage failures don't block the indexing pipeline

Configuration in `backend/config_schema.py`:

```python
"duckdb": {
    "settings": [
        {
            "key": "DUCKDB_ENABLED",
            "type": "bool",
            "default": False,
            "depends_on": {"DEEPSEEK_OCR_ENABLED": True}
        },
        {
            "key": "DUCKDB_URL",
            "type": "str",
            "default": "http://localhost:8300"
        }
    ]
}
```

## DuckDB UI Extension

The service includes the official DuckDB UI extension for interactive data exploration:

### Access the UI

**URL:** `http://localhost:4213`

The UI provides:
- **SQL query editor** with syntax highlighting and autocomplete
- **Table browser** for exploring schema and data
- **Query results viewer** with visualization options
- **Notebook interface** for interactive analysis
- **Export functionality** (CSV, Parquet, JSON)
- **Chart builder** for data visualization

### Features

- **Local Query Execution**: All queries run in your DuckDB instance
- **Real-time Data Access**: Queries execute against your live OCR data
- **Auto-updating**: UI files are fetched from https://ui.duckdb.org
- **Persistent Notebooks**: Notebooks are stored in the DuckDB catalog

### Example Queries

Try these in the UI:

```sql
-- List all indexed documents
SELECT filename, COUNT(*) as pages 
FROM ocr_pages 
GROUP BY filename;

-- Search for specific text
SELECT filename, page_number, text 
FROM ocr_pages 
WHERE text LIKE '%search term%';

-- Provider breakdown
SELECT provider, COUNT(*) as page_count 
FROM ocr_pages 
GROUP BY provider;

-- Recent extractions
SELECT filename, page_number, extracted_at 
FROM ocr_pages 
ORDER BY extracted_at DESC 
LIMIT 10;
```

## Security Considerations

### Query Safety

The `/query` endpoint has built-in safety measures:

- **Forbidden keywords**: `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, `CREATE`, `INSERT`, `UPDATE`
- **Automatic LIMIT**: Adds `LIMIT` clause if not present (max 10,000)
- **Read-only**: Only `SELECT` queries are allowed

### Production Recommendations

- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Use connection pooling for high load
- [ ] Set up database backups
- [ ] Monitor database size and performance
- [ ] Implement query timeouts
- [ ] Add audit logging

## Troubleshooting

### Database locked error

DuckDB uses file-level locking. Ensure only one process accesses the database.

### Memory issues

For large queries, DuckDB may use significant memory. Consider:
- Adding query timeouts
- Implementing pagination
- Using streaming for large result sets

### UI not loading

Ensure the `ui/` directory contains the DuckDB-Wasm UI files:

```bash
ls -la ui/
# Should contain index.html and other assets
```

## Performance

### Database Size

DuckDB uses efficient columnar storage:
- Text data is compressed
- JSON fields are optimized
- Typical compression ratio: 5-10x

### Query Performance

- Indexed queries: < 100ms
- Full-text search: 100-500ms (depends on data size)
- Aggregate queries: 500ms-2s (depends on complexity)

### Scaling

For very large datasets (> 100GB):
- Consider partitioning by date or document
- Use materialized views for common queries
- Implement data retention policies

## Future Enhancements

- [ ] Advanced analytics dashboards
- [ ] Export to Parquet/CSV
- [ ] Scheduled aggregation jobs
- [ ] Multi-user support with row-level security
- [ ] Integration with BI tools (Metabase, Superset)
- [ ] Real-time updates via WebSocket
- [ ] Machine learning integration for document insights

## License

See root LICENSE file.

## Support

For issues and questions, please refer to the main project documentation.
