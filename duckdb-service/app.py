"""
DuckDB HTTP API Service.

Provides REST API for storing and querying OCR data in DuckDB.
"""

import logging
from typing import Any, Dict, List, Optional

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from init_db import initialize_database
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "/var/lib/duckdb/snappy.db"

# Initialize FastAPI app
app = FastAPI(title="DuckDB OCR Service", version="1.0.0")

# Global database connection
db_conn: Optional[duckdb.DuckDBPyConnection] = None


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    global db_conn
    logger.info(f"Initializing DuckDB at {DB_PATH}")
    initialize_database(DB_PATH)
    db_conn = duckdb.connect(DB_PATH)
    logger.info("DuckDB service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    global db_conn
    if db_conn:
        db_conn.close()
        logger.info("DuckDB connection closed")


# Pydantic models for API
class OcrResult(BaseModel):
    filename: str
    page_number: int
    provider: str
    version: Optional[str] = None
    text: Optional[str] = None
    markdown: Optional[str] = None
    raw_text: Optional[str] = None
    extracted_at: Optional[str] = None
    storage_url: Optional[str] = None
    document_id: Optional[str] = None
    pdf_page_index: Optional[int] = None
    total_pages: Optional[int] = None
    page_dimensions: Optional[Dict[str, int]] = None
    image: Optional[Dict[str, str]] = None
    regions: Optional[List[Dict[str, Any]]] = None
    extracted_images: Optional[List[Dict[str, str]]] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    filename_filter: Optional[str] = None


class StatsRequest(BaseModel):
    filename: Optional[str] = None


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if db_conn:
            db_conn.execute("SELECT 1").fetchone()
            return {"status": "healthy", "database": "connected"}
        return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/ocr/store")
async def store_ocr_result(payload: OcrResult):
    """Store OCR result in DuckDB."""
    if not db_conn:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # Extract page dimensions
        page_dims = payload.page_dimensions or {}
        image_info = payload.image or {}

        # Insert main OCR result
        result = db_conn.execute(
            """
            INSERT INTO ocr_results (
                filename, page_number, provider, version,
                text, markdown, raw_text,
                extracted_at, storage_url,
                document_id, pdf_page_index, total_pages,
                page_width_px, page_height_px,
                image_url, image_storage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (filename, page_number) DO UPDATE SET
                text = EXCLUDED.text,
                markdown = EXCLUDED.markdown,
                raw_text = EXCLUDED.raw_text,
                extracted_at = EXCLUDED.extracted_at,
                storage_url = EXCLUDED.storage_url
            RETURNING id
        """,
            [
                payload.filename,
                payload.page_number,
                payload.provider,
                payload.version,
                payload.text,
                payload.markdown,
                payload.raw_text,
                payload.extracted_at,
                payload.storage_url,
                payload.document_id,
                payload.pdf_page_index,
                payload.total_pages,
                page_dims.get("width_px"),
                page_dims.get("height_px"),
                image_info.get("url"),
                image_info.get("storage"),
            ],
        )

        result_row = result.fetchone()
        if not result_row:
            raise HTTPException(status_code=500, detail="Failed to insert OCR result")

        ocr_result_id = result_row[0]

        # Insert regions if available
        if payload.regions:
            for region in payload.regions:
                bbox = region.get("bbox", [])
                db_conn.execute(
                    """
                    INSERT INTO ocr_regions (
                        ocr_result_id, region_type, content,
                        bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                        bbox_x3, bbox_y3, bbox_x4, bbox_y4,
                        confidence, image_url, image_storage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    [
                        ocr_result_id,
                        region.get("type"),
                        region.get("content", ""),
                        bbox[0] if len(bbox) > 0 else None,
                        bbox[1] if len(bbox) > 1 else None,
                        bbox[2] if len(bbox) > 2 else None,
                        bbox[3] if len(bbox) > 3 else None,
                        bbox[4] if len(bbox) > 4 else None,
                        bbox[5] if len(bbox) > 5 else None,
                        bbox[6] if len(bbox) > 6 else None,
                        bbox[7] if len(bbox) > 7 else None,
                        region.get("confidence"),
                        region.get("image_url"),
                        region.get("image_storage"),
                    ],
                )

        # Insert extracted images if available
        if payload.extracted_images:
            for idx, img in enumerate(payload.extracted_images):
                db_conn.execute(
                    """
                    INSERT INTO ocr_extracted_images (
                        ocr_result_id, image_url, storage, image_index
                    ) VALUES (?, ?, ?, ?)
                """,
                    [
                        ocr_result_id,
                        img.get("url"),
                        img.get("storage"),
                        idx,
                    ],
                )

        logger.info(
            f"Stored OCR result: {payload.filename} page {payload.page_number} (id={ocr_result_id})"
        )

        return {
            "status": "success",
            "ocr_result_id": ocr_result_id,
            "filename": payload.filename,
            "page_number": payload.page_number,
        }

    except Exception as e:
        logger.error(f"Failed to store OCR result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/search")
async def search_text(request: SearchRequest):
    """Full-text search across OCR results."""
    if not db_conn:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        sql = """
            SELECT 
                filename, page_number, text, markdown,
                document_id, storage_url, extracted_at
            FROM ocr_results
            WHERE text LIKE ?
        """
        params: List[Any] = [f"%{request.query}%"]

        if request.filename_filter:
            sql += " AND filename LIKE ?"
            params.append(f"%{request.filename_filter}%")

        sql += " ORDER BY extracted_at DESC LIMIT ?"
        params.append(request.limit)

        results = db_conn.execute(sql, params).fetchall()

        return {
            "results": [
                {
                    "filename": row[0],
                    "page_number": row[1],
                    "text": row[2],
                    "markdown": row[3],
                    "document_id": row[4],
                    "storage_url": row[5],
                    "extracted_at": row[6],
                }
                for row in results
            ],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/stats")
async def get_stats(request: StatsRequest):
    """Get statistics about stored OCR data."""
    if not db_conn:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        if request.filename:
            result = db_conn.execute(
                """
                SELECT 
                    COUNT(*) as page_count,
                    SUM(LENGTH(text)) as total_chars,
                    COUNT(DISTINCT document_id) as document_count
                FROM ocr_results
                WHERE filename = ?
            """,
                [request.filename],
            ).fetchone()
        else:
            result = db_conn.execute(
                """
                SELECT 
                    COUNT(*) as page_count,
                    SUM(LENGTH(text)) as total_chars,
                    COUNT(DISTINCT filename) as document_count,
                    COUNT(DISTINCT document_id) as unique_documents
                FROM ocr_results
            """
            ).fetchone()

        if not result:
            return {"page_count": 0, "total_chars": 0, "document_count": 0}

        stats = {
            "page_count": result[0] or 0,
            "total_chars": result[1] or 0,
            "document_count": result[2] or 0,
        }

        if not request.filename and len(result) > 3:
            stats["unique_documents"] = result[3] or 0

        return stats

    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/result/{filename}/{page_number}")
async def get_ocr_result(filename: str, page_number: int):
    """Fetch OCR result for a specific page."""
    if not db_conn:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        result = db_conn.execute(
            """
            SELECT 
                id, filename, page_number, provider, version,
                text, markdown, raw_text, extracted_at, storage_url,
                document_id, pdf_page_index, total_pages,
                page_width_px, page_height_px, image_url, image_storage
            FROM ocr_results
            WHERE filename = ? AND page_number = ?
        """,
            [filename, page_number],
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="OCR result not found")

        return {
            "id": result[0],
            "filename": result[1],
            "page_number": result[2],
            "provider": result[3],
            "version": result[4],
            "text": result[5],
            "markdown": result[6],
            "raw_text": result[7],
            "extracted_at": result[8],
            "storage_url": result[9],
            "document_id": result[10],
            "pdf_page_index": result[11],
            "total_pages": result[12],
            "page_width_px": result[13],
            "page_height_px": result[14],
            "image_url": result[15],
            "image_storage": result[16],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch OCR result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class QueryRequest(BaseModel):
    query: str


@app.post("/query/execute")
async def execute_query(request: QueryRequest):
    """Execute arbitrary SQL query (read-only recommended)."""
    if not db_conn:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # Execute the query
        result = db_conn.execute(request.query)

        # Fetch results
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description] if result.description else []

        return {"columns": columns, "rows": rows, "row_count": len(rows)}

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the web UI."""
    try:
        with open("/app/static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error loading UI</h1><p>{str(e)}</p>", status_code=500
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8300)
