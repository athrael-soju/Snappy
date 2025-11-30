# Snappy Architecture Simplification Plan

## Goal
Simplify Snappy from a 5-service architecture to 2-service architecture:
- **Remove**: MinIO (object storage), DuckDB (analytics)
- **Keep**: Qdrant (vector DB), Backend/Frontend
- **External**: ColPali API, OCR API (unchanged)

## Current Architecture

### MinIO Usage
1. **Image Storage** (`backend/clients/minio.py`)
   - Page images: `{doc_id}/{page_num}/image/{page_id}.{ext}`
   - Extracted images from OCR
   - Stores as objects, returns public URLs

2. **OCR Data Storage** (`backend/domain/ocr_persistence.py`)
   - Full OCR JSON: `{doc_id}/{page_num}/ocr/{uuid}.json`
   - Individual regions: `{doc_id}/{page_num}/ocr_regions/region_{uuid}.json`
   - All stored as JSON objects in MinIO

### DuckDB Usage
1. **OCR Analytics** (`backend/clients/duckdb.py`)
   - Stores complete OCR results for SQL querying
   - Document deduplication checks
   - Statistics and analytics
   - Text search across OCR data

2. **API Endpoints** (`backend/api/routers/duckdb.py`)
   - Query execution
   - Document listing
   - Statistics retrieval

### Qdrant Payload Structure
Currently stores **references** to external storage:
```python
payload = {
    "image_url": "http://minio:9000/bucket/doc/page/img.jpg",
    "image_inline": False,
    "image_storage": "minio",
    "ocr_url": "http://minio:9000/bucket/doc/page/ocr.json",
    "ocr_regions": [{"label": "text", "url": "...", "id": "..."}],
    ...
}
```

## New Architecture

### Qdrant as Single Storage
Store everything directly in Qdrant payloads:
```python
payload = {
    "image_data": "base64_encoded_image_string",
    "image_format": "webp",
    "image_mime_type": "image/webp",
    "ocr_data": {
        "text": "...",
        "markdown": "...",
        "regions": [...],
        "extracted_images": ["base64_1", "base64_2"]
    },
    ...
}
```

### Benefits
1. **Simpler deployment**: 2 services vs 5 (60% reduction)
2. **Fewer dependencies**: No MinIO/DuckDB config
3. **Atomic storage**: Everything in one place
4. **Better reliability**: No coordination needed between services
5. **Easier setup**: Just Qdrant + Backend/Frontend

### Trade-offs
1. **Qdrant payload size**: Will increase significantly
2. **No SQL queries**: Lose DuckDB analytics (can use Qdrant filters instead)
3. **No deduplication**: Will need to implement in backend if needed
4. **Network overhead**: Base64 encoding increases size by ~33%

## Migration Steps

### Phase 1: Backend Storage Layer
**Files to modify:**
1. `backend/clients/qdrant/indexing/points.py`
   - Change payload structure to store base64 images
   - Store OCR data inline instead of URLs

2. `backend/domain/ocr_persistence.py`
   - Remove MinIO storage calls
   - Store OCR directly in Qdrant payload
   - Remove DuckDB storage calls

3. `backend/domain/pipeline/stages/storage.py`
   - Store images as base64 in memory for Qdrant
   - Remove MinIO upload logic

4. `backend/domain/pipeline/stages/upsert.py`
   - Pass image data instead of URLs
   - Include OCR data in point construction

**Files to delete:**
1. `backend/clients/minio.py` - Complete MinIO client
2. `backend/clients/duckdb.py` - Complete DuckDB client
3. `backend/config/schema/minio.py` - MinIO config schema
4. `backend/config/schema/duckdb.py` - DuckDB config schema
5. `backend/api/routers/duckdb.py` - DuckDB API endpoints
6. `backend/domain/analytics.py` - DuckDB analytics domain logic

### Phase 2: Backend Retrieval Layer
**Files to modify:**
1. `backend/clients/qdrant/search.py`
   - Return base64 images in search results
   - Include OCR data in payloads

2. `backend/domain/retrieval.py`
   - Remove MinIO image fetching
   - Return base64 images from Qdrant payloads

3. `backend/api/dependencies.py`
   - Remove MinIO/DuckDB client initialization
   - Update QdrantClient initialization

### Phase 3: Configuration
**Files to modify:**
1. `backend/config/application.py`
   - Remove MinIO configuration
   - Remove DuckDB configuration

2. `.env.example` and `backend/.env.example`
   - Remove MINIO_* variables
   - Remove DUCKDB_* variables
   - Update documentation

3. `backend/requirements.txt`
   - Remove `minio` package

**Files to delete:**
1. `duckdb/` - Entire DuckDB service directory
2. `duckdb/.env` and `duckdb/.env.example`
3. `duckdb/docker-compose.yml`

### Phase 4: Docker & Deployment
**Files to modify:**
1. `docker-compose.yml`
   - Remove `minio` service
   - Remove `duckdb` service
   - Remove MinIO volume
   - Remove DuckDB volume
   - Update backend environment variables
   - Remove backend dependency on MinIO

2. `Makefile`
   - Simplify profiles (remove DuckDB references)
   - Update service lists

**Files to delete:**
1. Any Docker-specific MinIO/DuckDB configs

### Phase 5: Frontend
**Files to modify:**
1. `frontend/next.config.ts`
   - Remove MinIO remote patterns from images config

2. `frontend/lib/api/generated/`
   - Regenerate SDK after backend OpenAPI changes

3. `frontend/app/search/page.tsx`
   - Handle base64 images instead of URLs
   - Update image display logic

4. `frontend/lib/chat/content.ts`
   - Handle base64 images in chat context

5. `frontend/.env.example`
   - Remove MinIO-related variables

**Files to delete:**
1. `frontend/lib/api/generated/services/DuckdbService.ts`
2. Any DuckDB-related UI components

### Phase 6: Maintenance & Cleanup
**Files to modify:**
1. `backend/api/routers/maintenance/actions.py`
   - Remove MinIO initialization/clear actions
   - Remove DuckDB initialization/clear actions

2. `backend/api/routers/maintenance/status.py`
   - Remove MinIO health check
   - Remove DuckDB health check

3. `backend/domain/maintenance.py`
   - Remove MinIO/DuckDB maintenance operations

4. `README.md`
   - Update architecture diagram
   - Update setup instructions
   - Update feature descriptions
   - Remove MinIO/DuckDB references

**Files to delete:**
1. Documentation about MinIO/DuckDB setup
2. Any MinIO/DuckDB troubleshooting guides

## Testing Strategy
1. **Unit tests**: Update to not expect MinIO/DuckDB
2. **Integration tests**: Test Qdrant-only storage
3. **Migration test**: Ensure existing data can be migrated
4. **Performance test**: Measure payload size impact
5. **Frontend test**: Verify base64 image rendering

## Risks & Mitigations

### Risk: Qdrant Payload Size Limits
- **Impact**: Qdrant has payload size limits
- **Mitigation**:
  - Use efficient image formats (WebP)
  - Compress images more aggressively
  - Test with large documents first
  - Consider max page limit per document

### Risk: Memory Usage
- **Impact**: Storing base64 in memory uses more RAM
- **Mitigation**:
  - Keep batch sizes reasonable
  - Monitor memory usage during testing
  - Adjust batch_size config if needed

### Risk: Search Performance
- **Impact**: Larger payloads may slow down search
- **Mitigation**:
  - Use `with_payload=False` when not needed
  - Only fetch images when displaying results
  - Enable Qdrant on-disk payloads

### Risk: Lost Functionality
- **Impact**: No SQL queries over OCR data
- **Mitigation**:
  - Use Qdrant filters for common queries
  - Document limitations
  - Consider future re-addition if needed

## Implementation Order
1. Start with backend storage (Phase 1)
2. Update retrieval layer (Phase 2)
3. Update configuration (Phase 3)
4. Update Docker setup (Phase 4)
5. Update frontend (Phase 5)
6. Clean up maintenance/docs (Phase 6)

## Rollback Plan
- Keep MinIO/DuckDB services commented out in docker-compose
- Tag commit before migration
- Document revert steps if needed

## Success Criteria
- ✅ Application starts with only Qdrant + Backend/Frontend
- ✅ Documents can be uploaded and indexed
- ✅ Search returns results with images
- ✅ OCR data is accessible
- ✅ No references to MinIO/DuckDB in code
- ✅ Documentation updated
- ✅ All tests pass
