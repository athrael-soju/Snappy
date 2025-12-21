# OCR Data Storage in Qdrant

## Overview

Snappy stores OCR data (text, markdown, and region metadata) directly in Qdrant vector payloads. This eliminates the need for a separate analytical database while maintaining all retrieval functionality. Local storage serves as a backup for OCR JSON files.

## Architecture

### Storage Flow

```
PDF Upload
    ↓
Rasterize → Page Images
    ↓
OCR Processing (DeepSeek)
    ↓
    ├─→ Local Storage: {filename}/{page}/ocr/{uuid}.json (backup)
    └─→ Qdrant Payload: full OCR data (text, markdown, regions)
```

### Retrieval Flow

```
Query
    ↓
ColPali Embedding
    ↓
Qdrant Search (Late Interaction)
    ↓
Top-K Results + OCR Payloads
    ↓
Region Filtering (if enabled)
    ↓
LLM Context
```

## Payload Structure

Each Qdrant point contains the following OCR data in its payload:

```json
{
  "filename": "document.pdf",
  "page_number": 0,
  "page_id": "abc123...",
  "image_url": "http://localhost:8100/api/files/images/document.pdf/0/image/xyz.png",
  "ocr_url": "http://localhost:8100/api/files/ocr/document.pdf/0/ocr/xyz.json",
  "ocr": {
    "text": "Full extracted text from the page...",
    "markdown": "# Structured markdown\n\nWith tables and formatting...",
    "regions": [
      {
        "bbox": [100, 200, 300, 250],
        "text": "Region text content",
        "type": "text",
        "confidence": 0.98
      },
      {
        "bbox": [100, 300, 400, 500],
        "text": "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |",
        "type": "table",
        "confidence": 0.95
      }
    ]
  }
}
```

### Payload Size Analysis

Typical OCR payload sizes:
- **Uncompressed JSON**: 16-22 KB per page
- **Optimized (no whitespace)**: ~8-9 KB per page
- **10,000 pages**: ~80-90 MB total

This is very reasonable for modern systems and provides fast access without additional database queries.

## Implementation Details

### Indexing Stage

During the OCR processing stage ([domain/pipeline/stages/ocr.py:133-154](../domain/pipeline/stages/ocr.py#L133-L154)):

```python
# Build OCR payload with full content
ocr_payload = {
    "ocr_url": storage_result["ocr_url"],
    "ocr": {
        "text": ocr_result.get("text", ""),
        "markdown": ocr_result.get("markdown", ""),
        "regions": storage_result.get("ocr_regions", []),
    }
}

# Update Qdrant points with OCR data
self.qdrant_service.collection_manager.service.set_payload(
    collection_name=self.collection_name,
    payload=ocr_payload,
    points=point_ids,
)
```

### Retrieval Stage

During search ([domain/retrieval.py:165-224](../domain/retrieval.py#L165-L224)):

```python
for it in items:
    payload = it.get("payload", {})

    if include_ocr:
        # OCR data is already in Qdrant payload
        ocr_data = payload.get("ocr")

        if ocr_data:
            # Apply region-level filtering if enabled
            if enable_region_filtering and ocr_data.get("regions"):
                filtered_regions = await _filter_regions_by_interpretability(
                    regions=ocr_data["regions"],
                    query=q,
                    image_url=image_url,
                    payload=payload,
                )
                # Update payload with filtered regions
                payload["ocr"] = {
                    "text": ocr_data.get("text", ""),
                    "markdown": ocr_data.get("markdown", ""),
                    "regions": filtered_regions,
                }
```

## Benefits

### Performance
- **Single Query**: OCR data retrieved alongside vectors (no joins)
- **Fast Access**: Direct payload access without additional database round-trips
- **Reduced Latency**: Eliminates cross-database coordination

### Simplicity
- **Fewer Dependencies**: No analytical database to manage
- **Simpler Architecture**: One source of truth for vector + metadata
- **Easier Deployment**: Reduced infrastructure complexity

### Scalability
- **Payload Size**: 8-9 KB per page is negligible for modern systems
- **Linear Growth**: Storage scales linearly with document count
- **No Join Overhead**: All data co-located with vectors

## Backup Storage

Local storage maintains OCR JSON files as backup:

**Path Structure**:
```
{bucket}/
  {filename}/
    {page}/
      image/
        {uuid}.png          # Page image
      ocr/
        {uuid}.json         # Full OCR JSON (backup)
      ocr_regions/
        {region_uuid}.json  # Individual region metadata
        {region_uuid}.png   # Region images (figures, etc.)
```

The `ocr_url` in the payload points to the backup JSON file, which can be used:
- For debugging and manual inspection
- As a fallback if payload data is corrupted
- For bulk export or migration

## Region-Level Filtering

When `ENABLE_REGION_LEVEL_RETRIEVAL=true`, the system:

1. Retrieves top-K pages with full OCR payloads from Qdrant
2. Generates interpretability maps (patch-level similarity scores)
3. Filters OCR regions based on spatial relevance
4. Returns only query-relevant regions to the LLM

This provides precise retrieval granularity while maintaining efficiency.

**See**: [Spatial Grounding Documentation](spatial_grounding.md)

## Migration from DuckDB

If you have existing documents indexed with DuckDB:

### Option 1: Re-upload Documents
1. Delete old collection and bucket via `/delete` endpoint
2. Re-upload all documents with OCR enabled
3. OCR data will be stored in Qdrant payloads

### Option 2: Gradual Migration
1. Keep existing documents (they still work via `ocr_url` fallback)
2. New documents will use Qdrant payloads
3. Eventually re-index old documents

### Removed Features
- **Duplicate Detection**: Previously powered by DuckDB filename tracking
  - Can be re-implemented using Qdrant scroll queries if needed
- **Full-Text Search**: Previously powered by DuckDB SQL queries
  - Vector search provides semantic retrieval instead
  - Can be re-implemented using Qdrant payload filters if needed
- **Analytics Queries**: Previously exposed via DuckDB API router
  - Can be re-implemented using Qdrant aggregations if needed

## Configuration

### Enable OCR
```bash
# backend/.env
DEEPSEEK_OCR_ENABLED=true
DEEPSEEK_OCR_URL=http://localhost:8300
```

### Enable Region Filtering
```bash
# backend/.env
ENABLE_REGION_LEVEL_RETRIEVAL=true
```

### Verify Storage
Check Qdrant payloads via `/status` endpoint:
```bash
curl http://localhost:8000/status
```

Response includes:
- `collection.vector_count`: Number of pages indexed
- `collection.unique_files`: Number of unique documents
- `collection.size_mb`: Estimated collection size (vectors + payloads)

## Troubleshooting

### No OCR Data in Search Results
- Check `DEEPSEEK_OCR_ENABLED=true` in backend/.env
- Verify OCR service is running (`docker-compose --profile ml up`)
- Check `/status` endpoint shows OCR service healthy
- Re-upload documents if indexed before enabling OCR

### OCR Payload Missing
- Check Qdrant collection exists: `GET /status`
- Verify OCR stage completed: `GET /progress/stream/{job_id}`
- Check logs for OCR processing errors

### Large Payload Size
- Current implementation stores ~8-9 KB per page (optimized)
- For extremely large documents (10K+ pages), consider:
  - Keeping only regions (not full text/markdown)
  - Using ocr_url fallback for edge cases
  - Implementing on-demand OCR loading

## See Also

- [Architecture Overview](architecture.md) - Full system architecture
- [Spatial Grounding](spatial_grounding.md) - Region-level retrieval
- [Configuration Reference](configuration.md) - All configuration options
- [Pipeline Documentation](pipeline.md) - Streaming indexing pipeline
