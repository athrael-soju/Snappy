"""
DuckDB Analytics Service for OCR Data

This service provides:
1. Persistent storage of OCR results in DuckDB
2. SQL query interface for analytics
3. DuckDB-Wasm UI for interactive exploration
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import duckdb

# Configuration
DATABASE_PATH = os.getenv("DUCKDB_DATABASE_PATH", "./data/ocr_data.duckdb")
API_HOST = os.getenv("DUCKDB_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("DUCKDB_API_PORT", "8300"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_VERSION = "1.0.0"

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global database connection
db_connection: Optional[duckdb.DuckDBPyConnection] = None


# Pydantic Models
class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class InfoResponse(BaseModel):
    version: str
    database_path: str
    database_size_mb: float
    tables: Dict[str, int]


class OcrPageData(BaseModel):
    """OCR data for a single page"""

    provider: str
    version: str
    filename: str
    page_number: int
    text: str
    markdown: str
    raw_text: Optional[str] = None
    regions: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_at: str
    storage_url: str
    document_id: Optional[str] = None
    pdf_page_index: Optional[int] = None
    total_pages: Optional[int] = None
    page_width_px: Optional[int] = None
    page_height_px: Optional[int] = None
    image_url: Optional[str] = None
    image_storage: Optional[str] = None
    extracted_images: List[Dict[str, Any]] = Field(default_factory=list)


class OcrBatchData(BaseModel):
    """Batch of OCR data"""

    pages: List[OcrPageData]


class QueryRequest(BaseModel):
    """SQL query request"""

    query: str
    limit: Optional[int] = Field(default=1000, le=10000)


class QueryResponse(BaseModel):
    """SQL query response"""

    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    query: str


class StatsResponse(BaseModel):
    """Database statistics"""

    total_documents: int
    total_pages: int
    total_regions: int
    total_extracted_images: int
    providers: Dict[str, int]
    storage_size_mb: float


class DocumentInfo(BaseModel):
    """Document information"""

    filename: str
    page_count: int
    first_indexed: str
    last_indexed: str
    total_regions: int
    total_extracted_images: int


def init_database():
    """Initialize DuckDB database and create tables"""
    global db_connection

    # Ensure data directory exists
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing DuckDB database at: {DATABASE_PATH}")
    db_connection = duckdb.connect(DATABASE_PATH)

    # Install and load the UI extension
    try:
        logger.info("Installing DuckDB UI extension...")
        db_connection.execute("INSTALL ui;")
        db_connection.execute("LOAD ui;")

        # Start the UI server on port 4213
        db_connection.execute("CALL start_ui_server();")
        logger.info("DuckDB UI server started on http://0.0.0.0:4213")
    except Exception as e:
        logger.warning(f"Failed to start DuckDB UI extension: {e}")
        logger.info("Continuing without UI extension...")

    # Create tables
    db_connection.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS ocr_pages_id_seq START 1;
        
        CREATE TABLE IF NOT EXISTS ocr_pages (
            id INTEGER PRIMARY KEY DEFAULT nextval('ocr_pages_id_seq'),
            provider VARCHAR,
            version VARCHAR,
            filename VARCHAR NOT NULL,
            page_number INTEGER NOT NULL,
            text TEXT,
            markdown TEXT,
            raw_text TEXT,
            regions JSON,
            extracted_at TIMESTAMP,
            storage_url VARCHAR,
            document_id VARCHAR,
            pdf_page_index INTEGER,
            total_pages INTEGER,
            page_width_px INTEGER,
            page_height_px INTEGER,
            image_url VARCHAR,
            image_storage VARCHAR,
            extracted_images JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(filename, page_number)
        )
    """
    )

    # Create indexes for common queries
    db_connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_filename ON ocr_pages(filename)"
    )
    db_connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_page_number ON ocr_pages(page_number)"
    )
    db_connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_provider ON ocr_pages(provider)"
    )
    db_connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_extracted_at ON ocr_pages(extracted_at)"
    )

    # Create full-text search index
    db_connection.execute("CREATE INDEX IF NOT EXISTS idx_text_fts ON ocr_pages(text)")

    logger.info("Database initialized successfully")


def close_database():
    """Close database connection"""
    global db_connection
    if db_connection:
        # Stop UI server before closing
        try:
            db_connection.execute("CALL stop_ui_server();")
            logger.info("DuckDB UI server stopped")
        except Exception as e:
            logger.debug(f"UI server stop warning: {e}")

        db_connection.close()
        db_connection = None
        logger.info("Database connection closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    init_database()
    yield
    # Shutdown
    close_database()


# Initialize FastAPI app
app = FastAPI(
    title="DuckDB Analytics Service",
    description="OCR data storage and analytics with DuckDB",
    version=API_VERSION,
    lifespan=lifespan,
)


# API Endpoints


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "DuckDB Analytics Service",
        "version": API_VERSION,
        "description": "OCR data storage and analytics",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        result = db_connection.execute("SELECT 1").fetchone()
        if result and result[0] == 1:
            return HealthResponse(
                status="healthy", database="connected", version=API_VERSION
            )
        else:
            raise HTTPException(status_code=503, detail="Database query failed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@app.get("/info", response_model=InfoResponse)
async def get_info():
    """Get database information and statistics"""
    try:
        # Get database size
        db_path = Path(DATABASE_PATH)
        size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0

        # Get table row counts
        tables = {}
        result = db_connection.execute("SELECT COUNT(*) FROM ocr_pages").fetchone()
        tables["ocr_pages"] = result[0] if result else 0

        return InfoResponse(
            version=API_VERSION,
            database_path=DATABASE_PATH,
            database_size_mb=round(size_mb, 2),
            tables=tables,
        )
    except Exception as e:
        logger.error(f"Failed to get info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/store", response_model=Dict[str, Any])
async def store_ocr_page(data: OcrPageData):
    """Store OCR data for a single page"""
    try:
        # Prepare data for insertion with ON CONFLICT
        # Note: DuckDB doesn't allow updating indexed columns in ON CONFLICT
        # Since we're storing the same data, just ignore duplicates
        db_connection.execute(
            """
            INSERT INTO ocr_pages (
                provider, version, filename, page_number, text, markdown, raw_text,
                regions, extracted_at, storage_url, document_id, pdf_page_index,
                total_pages, page_width_px, page_height_px, image_url, image_storage,
                extracted_images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (filename, page_number) DO NOTHING
        """,
            [
                data.provider,
                data.version,
                data.filename,
                data.page_number,
                data.text,
                data.markdown,
                data.raw_text,
                data.regions,
                data.extracted_at,
                data.storage_url,
                data.document_id,
                data.pdf_page_index,
                data.total_pages,
                data.page_width_px,
                data.page_height_px,
                data.image_url,
                data.image_storage,
                data.extracted_images,
            ],
        )

        logger.info(f"Stored OCR data: {data.filename} page {data.page_number}")
        return {
            "status": "success",
            "filename": data.filename,
            "page_number": data.page_number,
        }
    except Exception as e:
        logger.error(f"Failed to store OCR data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/store/batch", response_model=Dict[str, Any])
async def store_ocr_batch(data: OcrBatchData):
    """Store multiple OCR pages in a batch"""
    try:
        stored_count = 0
        for page_data in data.pages:
            # Note: DuckDB doesn't allow updating indexed columns in ON CONFLICT
            # Since we're storing the same data, just ignore duplicates
            db_connection.execute(
                """
                INSERT INTO ocr_pages (
                    provider, version, filename, page_number, text, markdown, raw_text,
                    regions, extracted_at, storage_url, document_id, pdf_page_index,
                    total_pages, page_width_px, page_height_px, image_url, image_storage,
                    extracted_images
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (filename, page_number) DO NOTHING
            """,
                [
                    page_data.provider,
                    page_data.version,
                    page_data.filename,
                    page_data.page_number,
                    page_data.text,
                    page_data.markdown,
                    page_data.raw_text,
                    page_data.regions,
                    page_data.extracted_at,
                    page_data.storage_url,
                    page_data.document_id,
                    page_data.pdf_page_index,
                    page_data.total_pages,
                    page_data.page_width_px,
                    page_data.page_height_px,
                    page_data.image_url,
                    page_data.image_storage,
                    page_data.extracted_images,
                ],
            )
            stored_count += 1

        logger.info(f"Stored {stored_count} OCR pages in batch")
        return {"status": "success", "stored_count": stored_count}
    except Exception as e:
        logger.error(f"Failed to store batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/documents", response_model=List[DocumentInfo])
async def list_documents(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """List all indexed documents"""
    try:
        result = db_connection.execute(
            """
            SELECT 
                filename,
                COUNT(*) as page_count,
                MIN(extracted_at) as first_indexed,
                MAX(extracted_at) as last_indexed,
                SUM(json_array_length(regions)) as total_regions,
                SUM(json_array_length(extracted_images)) as total_extracted_images
            FROM ocr_pages
            GROUP BY filename
            ORDER BY last_indexed DESC
            LIMIT ? OFFSET ?
        """,
            [limit, offset],
        ).fetchall()

        documents = []
        for row in result:
            documents.append(
                DocumentInfo(
                    filename=row[0],
                    page_count=row[1],
                    first_indexed=str(row[2]),
                    last_indexed=str(row[3]),
                    total_regions=row[4] or 0,
                    total_extracted_images=row[5] or 0,
                )
            )

        return documents
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/documents/{filename}", response_model=DocumentInfo)
async def get_document(filename: str):
    """Get information about a specific document"""
    try:
        result = db_connection.execute(
            """
            SELECT 
                filename,
                COUNT(*) as page_count,
                MIN(extracted_at) as first_indexed,
                MAX(extracted_at) as last_indexed,
                SUM(json_array_length(regions)) as total_regions,
                SUM(json_array_length(extracted_images)) as total_extracted_images
            FROM ocr_pages
            WHERE filename = ?
            GROUP BY filename
        """,
            [filename],
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentInfo(
            filename=result[0],
            page_count=result[1],
            first_indexed=str(result[2]),
            last_indexed=str(result[3]),
            total_regions=result[4] or 0,
            total_extracted_images=result[5] or 0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ocr/pages/{filename}/{page_number}", response_model=Dict[str, Any])
async def get_page(filename: str, page_number: int):
    """Get OCR data for a specific page"""
    try:
        result = db_connection.execute(
            """
            SELECT 
                provider, version, filename, page_number, text, markdown, raw_text,
                regions, extracted_at, storage_url, document_id, pdf_page_index,
                total_pages, page_width_px, page_height_px, image_url, image_storage,
                extracted_images, created_at
            FROM ocr_pages
            WHERE filename = ? AND page_number = ?
        """,
            [filename, page_number],
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Page not found")

        return {
            "provider": result[0],
            "version": result[1],
            "filename": result[2],
            "page_number": result[3],
            "text": result[4],
            "markdown": result[5],
            "raw_text": result[6],
            "regions": result[7],
            "extracted_at": str(result[8]),
            "storage_url": result[9],
            "document_id": result[10],
            "pdf_page_index": result[11],
            "total_pages": result[12],
            "page_width_px": result[13],
            "page_height_px": result[14],
            "image_url": result[15],
            "image_storage": result[16],
            "extracted_images": result[17],
            "created_at": str(result[18]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/ocr/documents/{filename}", response_model=Dict[str, Any])
async def delete_document(filename: str):
    """Delete all data for a document"""
    try:
        result = db_connection.execute(
            "DELETE FROM ocr_pages WHERE filename = ?", [filename]
        )
        deleted_count = result.fetchone()[0] if result else 0

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info(f"Deleted {deleted_count} pages for document: {filename}")
        return {"status": "success", "deleted_pages": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a raw SQL query (with safety limits)"""
    try:
        # Add LIMIT if not present
        query = request.query.strip()
        query_upper = query.upper()

        # Block dangerous operations
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "ALTER",
            "CREATE",
            "INSERT",
            "UPDATE",
        ]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query contains forbidden keyword: {keyword}",
                )

        # Add limit if not present
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {request.limit}"

        # Execute query
        result = db_connection.execute(query)
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description] if result.description else []

        return QueryResponse(
            columns=columns, rows=rows, row_count=len(rows), query=query
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get aggregate statistics"""
    try:
        # Count documents
        total_docs = db_connection.execute(
            "SELECT COUNT(DISTINCT filename) FROM ocr_pages"
        ).fetchone()[0]

        # Count pages
        total_pages = db_connection.execute(
            "SELECT COUNT(*) FROM ocr_pages"
        ).fetchone()[0]

        # Count regions
        total_regions = (
            db_connection.execute(
                "SELECT SUM(json_array_length(regions)) FROM ocr_pages WHERE regions IS NOT NULL"
            ).fetchone()[0]
            or 0
        )

        # Count extracted images
        total_images = (
            db_connection.execute(
                "SELECT SUM(json_array_length(extracted_images)) FROM ocr_pages WHERE extracted_images IS NOT NULL"
            ).fetchone()[0]
            or 0
        )

        # Provider breakdown
        providers_result = db_connection.execute(
            "SELECT provider, COUNT(*) FROM ocr_pages GROUP BY provider"
        ).fetchall()
        providers = {row[0]: row[1] for row in providers_result}

        # Database size
        db_path = Path(DATABASE_PATH)
        size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0

        return StatsResponse(
            total_documents=total_docs,
            total_pages=total_pages,
            total_regions=total_regions,
            total_extracted_images=total_images,
            providers=providers,
            storage_size_mb=round(size_mb, 2),
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/text", response_model=QueryResponse)
async def search_text(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, le=500),
):
    """Full-text search across OCR text"""
    try:
        result = db_connection.execute(
            """
            SELECT filename, page_number, text, markdown, extracted_at
            FROM ocr_pages
            WHERE text LIKE ?
            ORDER BY extracted_at DESC
            LIMIT ?
        """,
            [f"%{q}%", limit],
        )
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            query=f"Search: {q}",
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount UI directory for serving DuckDB-Wasm UI
ui_path = Path(__file__).parent / "ui"
if ui_path.exists() and any(ui_path.iterdir()):
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")
    logger.info("DuckDB UI mounted at /ui")
else:
    logger.warning("UI directory not found or empty. DuckDB UI will not be available.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower(),
    )
