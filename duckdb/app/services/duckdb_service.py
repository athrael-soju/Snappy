"""DuckDB analytics service implementation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import logger
from app.models.schemas import (
    DocumentInfo,
    InfoResponse,
    OcrBatchData,
    OcrPageData,
    QueryRequest,
    QueryResponse,
    StatsResponse,
)


class DuckDBAnalyticsService:
    """Encapsulates all DuckDB queries used by the API."""

    def __init__(self) -> None:
        self._db_manager = db_manager

    @property
    def conn(self):
        return self._db_manager.connection

    # ------------------------------------------------------------------
    # Health & info
    # ------------------------------------------------------------------
    def health(self) -> bool:
        result = self.conn.execute("SELECT 1").fetchone()
        return bool(result and result[0] == 1)

    def info(self) -> InfoResponse:
        db_path = Path(settings.DUCKDB_DATABASE_PATH)
        size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0.0

        tables = {
            "documents": self._count_table("documents"),
            "pages": self._count_table("pages"),
            "regions": self._count_table("regions"),
        }

        return InfoResponse(
            version=settings.API_VERSION,
            database_path=str(db_path),
            database_size_mb=round(size_mb, 2),
            tables=tables,
        )

    def _count_table(self, table: str) -> int:
        """Count rows in a table with SQL injection protection."""
        # Whitelist of allowed table names
        allowed_tables = {"documents", "pages", "regions"}
        if table not in allowed_tables:
            raise ValueError(f"Invalid table name: {table}")

        # Use identifier quoting for additional safety
        result = self.conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
        return int(result[0]) if result else 0

    def _strip_block_comments(self, sql: str) -> str:
        """Remove /* */ comments with a linear scan to avoid regex backtracking."""
        cleaned: List[str] = []
        i = 0
        length = len(sql)
        while i < length:
            if sql[i : i + 2] == "/*":
                end = sql.find("*/", i + 2)
                if end == -1:
                    cleaned.append(sql[i:])
                    break
                i = end + 2
                continue
            cleaned.append(sql[i])
            i += 1
        return "".join(cleaned)

    def _schema_exists(self) -> bool:
        try:
            result = self.conn.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE lower(table_name) IN ('documents', 'pages', 'regions')
                """
            ).fetchone()
            return bool(result and result[0] == 3)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    def store_page(self, payload: OcrPageData) -> Dict[str, Any]:
        """Store a single OCR page and its columnar data.

        Stores:
        - Core page metadata (filename, page_number, dimensions, MinIO URLs)
        - Full text and markdown (for search/retrieval)
        - Structured regions with bounding boxes

        Note: Full JSON payload already exists in MinIO at storage_url
        """
        conn = self.conn

        self._delete_page_rows(payload.filename, payload.page_number)

        # Get or create document_id from documents table
        document_id = self._get_or_create_document_id(
            filename=payload.filename,
            file_size_bytes=None,  # Not available in OcrPageData
            total_pages=None,  # Not available in OcrPageData
        )

        row = conn.execute(
            """
            INSERT INTO pages (
                document_id, filename, page_number, page_width_px, page_height_px,
                image_url, text, markdown, storage_url, extracted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [
                document_id,
                payload.filename,
                payload.page_number,
                payload.page_width_px,
                payload.page_height_px,
                payload.image_url,
                payload.text,
                payload.markdown,
                payload.storage_url,
                payload.extracted_at,
            ],
        ).fetchone()

        if not row:
            raise RuntimeError("Failed to insert OCR page")

        page_id = int(row[0])
        self._insert_regions(page_id, payload.regions)

        logger.info(
            "Stored OCR data: %s page %s", payload.filename, payload.page_number
        )
        return {
            "status": "success",
            "filename": payload.filename,
            "page_number": payload.page_number,
        }

    def _delete_page_rows(self, filename: str, page_number: int) -> None:
        """Remove an existing page and its related rows."""
        params = [filename, page_number]
        self.conn.execute(
            "DELETE FROM pages WHERE filename = ? AND page_number = ?",
            params,
        )

    def store_batch(self, payload: OcrBatchData) -> Dict[str, Any]:
        count = 0
        for page in payload.pages:
            self.store_page(page)
            count += 1
        return {"status": "success", "stored_count": count}

    # ------------------------------------------------------------------
    # Maintenance helpers
    # ------------------------------------------------------------------

    def initialize_storage(self) -> Dict[str, Any]:
        """Ensure DuckDB is ready and report current counts."""
        db_manager.connect(force=True)
        db_manager.ensure_schema()
        stats = self.stats()
        return {
            "status": "success",
            "message": "DuckDB schema verified",
            "pages": stats.total_pages,
            "regions": stats.total_regions,
        }

    def clear_storage(self) -> Dict[str, Any]:
        """Remove all OCR data while keeping the schema."""
        counts = self.conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM documents) AS documents,
                (SELECT COUNT(*) FROM pages) AS pages,
                (SELECT COUNT(*) FROM regions) AS regions
            """
        ).fetchone()

        # Delete child tables first (respects foreign key constraints)
        self.conn.execute("DELETE FROM regions")
        self.conn.execute("DELETE FROM pages")
        self.conn.execute("DELETE FROM documents")

        cleared_documents = counts[0] if counts else 0
        cleared_pages = counts[1] if counts else 0
        cleared_regions = counts[2] if counts else 0

        return {
            "status": "success",
            "message": "Cleared DuckDB tables",
            "cleared_documents": cleared_documents,
            "cleared_pages": cleared_pages,
            "cleared_regions": cleared_regions,
        }

    def delete_storage(self) -> Dict[str, Any]:
        """Drop DuckDB OCR tables without removing the database file."""
        conn = db_manager.connect(force=True)
        conn.execute("DROP TABLE IF EXISTS regions")
        conn.execute("DROP TABLE IF EXISTS pages")
        conn.execute("DROP TABLE IF EXISTS documents")
        conn.execute("DROP SEQUENCE IF EXISTS regions_id_seq")
        conn.execute("DROP SEQUENCE IF EXISTS pages_id_seq")
        conn.execute("DROP SEQUENCE IF EXISTS documents_id_seq")
        conn.execute("CHECKPOINT")

        return {
            "status": "success",
            "message": "Dropped DuckDB OCR tables",
        }

    def _insert_regions(self, page_id: int, regions: Sequence[Dict[str, Any]]) -> None:
        """Insert OCR regions for a page.

        Stores:
        - region_id: Optional identifier from OCR provider
        - label: Region type (e.g., 'text', 'table', 'figure', 'image')
        - bbox: Bounding box coordinates (x1, y1, x2, y2)
        - content: Extracted text/data for this region, or image URL for image regions
        """
        if not regions:
            return

        rows: List[Tuple[Any, ...]] = []
        for region in regions:
            bbox = region.get("bbox") or [None, None, None, None]
            x1, y1, x2, y2 = self._parse_bbox(bbox)

            # For image/figure regions, use image_url as content if content is empty
            content = region.get("content")
            label = region.get("label", "").lower()
            if not content and label in ("image", "figure") and "image_url" in region:
                content = region.get("image_url")

            rows.append(
                (
                    page_id,
                    region.get("id"),
                    region.get("label"),
                    x1,
                    y1,
                    x2,
                    y2,
                    content,
                )
            )

        self.conn.executemany(
            """
            INSERT INTO regions (
                page_id, region_id, label, bbox_x1, bbox_y1, bbox_x2, bbox_y2, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    @staticmethod
    def _parse_bbox(bbox: Sequence[Any]) -> Tuple[Optional[int], ...]:
        def _to_int(value: Any) -> Optional[int]:
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        padded = list(bbox) + [None, None, None, None]
        return tuple(_to_int(x) for x in padded[:4])  # type: ignore[return-value]

    @staticmethod
    def _to_bool(value: Any) -> Optional[bool]:
        if value is None:
            return None
        return bool(value)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def list_documents(self, limit: int, offset: int) -> List[DocumentInfo]:
        result = self.conn.execute(
            """
            SELECT
                p.filename,
                COUNT(*) AS page_count,
                MIN(p.extracted_at) AS first_indexed,
                MAX(p.extracted_at) AS last_indexed,
                COALESCE(SUM(r.region_count), 0) AS total_regions
            FROM pages p
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS region_count
                FROM regions
                GROUP BY page_id
            ) r ON p.id = r.page_id
            GROUP BY p.filename
            ORDER BY last_indexed DESC
            LIMIT ? OFFSET ?
            """,
            [limit, offset],
        ).fetchall()

        return [
            DocumentInfo(
                filename=row[0],
                page_count=row[1],
                first_indexed=str(row[2]),
                last_indexed=str(row[3]),
                total_regions=row[4],
            )
            for row in result
        ]

    def get_document(self, filename: str) -> DocumentInfo:
        row = self.conn.execute(
            """
            SELECT
                p.filename,
                COUNT(*) AS page_count,
                MIN(p.extracted_at) AS first_indexed,
                MAX(p.extracted_at) AS last_indexed,
                COALESCE(SUM(r.region_count), 0) AS total_regions
            FROM pages p
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS region_count
                FROM regions
                GROUP BY page_id
            ) r ON p.id = r.page_id
            WHERE p.filename = ?
            GROUP BY p.filename
            """,
            [filename],
        ).fetchone()

        if not row:
            raise ValueError("Document not found")

        return DocumentInfo(
            filename=row[0],
            page_count=row[1],
            first_indexed=str(row[2]),
            last_indexed=str(row[3]),
            total_regions=row[4],
        )

    def get_page(self, filename: str, page_number: int) -> Dict[str, Any]:
        """Retrieve page data by filename and page_number.

        This matches Qdrant's payload structure:
        - filename: Document filename
        - page_number: Same as pdf_page_index in Qdrant

        Returns:
            Dict with page metadata, text, markdown, regions, and MinIO URLs
        """
        row = self.conn.execute(
            """
            SELECT
                id, filename, page_number, page_width_px, page_height_px,
                image_url, text, markdown, storage_url, extracted_at, created_at
            FROM pages
            WHERE filename = ? AND page_number = ?
            """,
            [filename, page_number],
        ).fetchone()

        if not row:
            raise ValueError("Page not found")

        page_id = row[0]
        regions = self._fetch_regions(page_id)

        return {
            "filename": row[1],
            "page_number": row[2],
            "page_width_px": row[3],
            "page_height_px": row[4],
            "image_url": row[5],
            "text": row[6],
            "markdown": row[7],
            "storage_url": row[8],
            "regions": regions,
            "extracted_at": str(row[9]),
            "created_at": str(row[10]),
        }

    def _fetch_regions(self, page_id: int) -> List[Dict[str, Any]]:
        """Fetch OCR regions for a page."""
        rows = self.conn.execute(
            """
            SELECT
                region_id, label, bbox_x1, bbox_y1, bbox_x2, bbox_y2, content
            FROM regions
            WHERE page_id = ?
            ORDER BY id
            """,
            [page_id],
        ).fetchall()

        regions = []
        for row in rows:
            bbox = [row[2], row[3], row[4], row[5]]
            regions.append(
                {
                    "id": row[0],
                    "label": row[1],
                    "bbox": bbox,
                    "content": row[6],
                }
            )
        return regions

    def delete_document(self, filename: str) -> Dict[str, Any]:
        count_row = self.conn.execute(
            "SELECT COUNT(*) FROM pages WHERE filename = ?", [filename]
        ).fetchone()
        deleted_pages = int(count_row[0]) if count_row else 0

        if deleted_pages == 0:
            raise ValueError("Document not found")

        # Delete in order: regions -> pages -> documents (respects FK constraints)
        self.conn.execute(
            """
            DELETE FROM regions
            WHERE page_id IN (
                SELECT id FROM pages WHERE filename = ?
            )
            """,
            [filename],
        )
        self.conn.execute("DELETE FROM pages WHERE filename = ?", [filename])
        self.conn.execute("DELETE FROM documents WHERE filename = ?", [filename])

        logger.info("Deleted %s pages for document %s", deleted_pages, filename)
        return {"status": "success", "deleted_pages": deleted_pages}

    def run_query(self, request: QueryRequest) -> QueryResponse:
        query = request.query.strip()
        if not query:
            raise ValueError("Query is required")

        # Limit input length to prevent resource exhaustion
        MAX_QUERY_LENGTH = 100_000
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")

        # Remove SQL comments to prevent bypasses
        # Remove single-line comments (--)
        query_no_comments = "\n".join(line.split("--")[0] for line in query.split("\n"))
        # Remove multi-line comments (/* */) without regex backtracking
        query_no_comments = self._strip_block_comments(query_no_comments)
        query_no_comments = query_no_comments.strip()

        if not query_no_comments:
            raise ValueError("Query is empty after removing comments")

        # Check for multiple statements (prevents injection via semicolons)
        if query_no_comments.count(";") > 1 or (
            ";" in query_no_comments and not query_no_comments.rstrip().endswith(";")
        ):
            raise ValueError("Multiple SQL statements are not allowed")

        # Normalize whitespace for validation
        query_normalized = " ".join(query_no_comments.split())
        query_upper = query_normalized.upper()

        # Verify it starts with SELECT
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Check for dangerous keywords (after comment removal)
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "ALTER",
            "CREATE",
            "INSERT",
            "UPDATE",
            "EXEC",
            "EXECUTE",
            "PRAGMA",
        ]
        for keyword in dangerous_keywords:
            # Use word boundaries to avoid false positives
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, query_upper):
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {request.limit}"

        result = self.conn.execute(query)
        rows = self._format_rows(result.fetchall())
        columns = [desc[0] for desc in result.description] if result.description else []

        return QueryResponse(
            columns=columns, rows=rows, row_count=len(rows), query=query
        )

    def stats(self) -> StatsResponse:
        schema_active = self._schema_exists()
        total_docs = total_pages = total_regions = total_images = 0

        if schema_active:
            total_docs_row = self.conn.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()
            total_docs = total_docs_row[0] if total_docs_row else 0

            total_pages_row = self.conn.execute(
                "SELECT COUNT(*) FROM pages"
            ).fetchone()
            total_pages = total_pages_row[0] if total_pages_row else 0

            total_regions_row = self.conn.execute(
                "SELECT COUNT(*) FROM regions"
            ).fetchone()
            total_regions = total_regions_row[0] if total_regions_row else 0

        db_path = Path(settings.DUCKDB_DATABASE_PATH)
        size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0.0

        return StatsResponse(
            total_documents=total_docs,
            total_pages=total_pages,
            total_regions=total_regions,
            storage_size_mb=round(size_mb, 2),
            schema_active=schema_active,
        )

    def search_text(self, query: str, limit: int) -> QueryResponse:
        result = self.conn.execute(
            """
            SELECT filename, page_number, text, markdown, extracted_at
            FROM pages
            WHERE text LIKE ?
            ORDER BY extracted_at DESC
            LIMIT ?
            """,
            [f"%{query}%", limit],
        )
        rows = self._format_rows(result.fetchall())
        columns = [desc[0] for desc in result.description] if result.description else []

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            query=f"Search: {query}",
        )

    @staticmethod
    def _format_rows(rows: Sequence[Tuple[Any, ...]]) -> List[List[Any]]:
        return [list(row) for row in rows]

    # ------------------------------------------------------------------
    # Document management helpers
    # ------------------------------------------------------------------
    def check_document_exists(
        self, filename: str, file_size_bytes: Optional[int], total_pages: int
    ) -> Optional[Dict[str, Any]]:
        """Check if a document already exists in the database.

        Args:
            filename: Document filename
            file_size_bytes: File size in bytes (None if unavailable)
            total_pages: Total number of pages

        Returns:
            Document info dict if exists, None otherwise

        Note:
            Only returns documents with valid metadata (not placeholders with -1 values)
        """
        try:
            row = self.conn.execute(
                """
                SELECT id, document_id, filename, file_size_bytes, total_pages,
                       first_indexed, last_indexed
                FROM documents
                WHERE filename = ?
                  AND file_size_bytes = ?
                  AND total_pages = ?
                  AND file_size_bytes >= 0
                  AND total_pages > 0
                """,
                [filename, file_size_bytes, total_pages],
            ).fetchone()

            if row:
                return {
                    "id": row[0],
                    "document_id": row[1],
                    "filename": row[2],
                    "file_size_bytes": row[3],
                    "total_pages": row[4],
                    "first_indexed": str(row[5]),
                    "last_indexed": str(row[6]),
                }
            return None
        except Exception as exc:
            logger.warning(f"Error checking document existence: {exc}")
            return None

    def store_document(
        self,
        document_id: str,
        filename: str,
        file_size_bytes: Optional[int],
        total_pages: int,
    ) -> int:
        """Store or update document metadata.

        Args:
            document_id: UUID for this document
            filename: Document filename
            file_size_bytes: File size in bytes
            total_pages: Total number of pages

        Returns:
            Database ID of the document
        """
        # Try to get existing document with same metadata
        row = self.conn.execute(
            """
            SELECT id FROM documents
            WHERE filename = ? AND file_size_bytes = ? AND total_pages = ?
            """,
            [filename, file_size_bytes, total_pages],
        ).fetchone()

        if row:
            # Update last_indexed timestamp
            doc_id = int(row[0])
            self.conn.execute(
                """
                UPDATE documents
                SET last_indexed = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [doc_id],
            )
            return doc_id

        # Check if there's a placeholder document to update
        placeholder_row = self.conn.execute(
            """
            SELECT id FROM documents
            WHERE filename = ?
              AND (file_size_bytes = -1 OR total_pages = -1)
            LIMIT 1
            """,
            [filename],
        ).fetchone()

        if placeholder_row:
            # Update placeholder with real metadata
            doc_id = int(placeholder_row[0])
            self.conn.execute(
                """
                UPDATE documents
                SET document_id = ?,
                    file_size_bytes = ?,
                    total_pages = ?,
                    last_indexed = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [document_id, file_size_bytes, total_pages, doc_id],
            )
            logger.info(
                f"Updated placeholder document entry for {filename} with complete metadata"
            )
            return doc_id

        # Insert new document
        row = self.conn.execute(
            """
            INSERT INTO documents (document_id, filename, file_size_bytes, total_pages)
            VALUES (?, ?, ?, ?)
            RETURNING id
            """,
            [document_id, filename, file_size_bytes, total_pages],
        ).fetchone()

        if not row:
            raise RuntimeError("Failed to insert document")

        return int(row[0])

    def _get_or_create_document_id(
        self,
        filename: str,
        file_size_bytes: Optional[int],
        total_pages: Optional[int],
    ) -> int:
        """Get existing document ID by filename, or create a placeholder.

        This is a helper for backward compatibility when storing OCR pages
        without explicit document metadata.

        Args:
            filename: Document filename
            file_size_bytes: File size in bytes (None if unavailable)
            total_pages: Total number of pages (None if unavailable)

        Returns:
            Database ID of the document
        """
        import uuid

        # Try to find existing document by filename
        # If we have complete metadata, use it for exact lookup
        if file_size_bytes is not None and total_pages is not None and total_pages > 0:
            row = self.conn.execute(
                """
                SELECT id FROM documents
                WHERE filename = ? AND file_size_bytes = ? AND total_pages = ?
                LIMIT 1
                """,
                [filename, file_size_bytes, total_pages],
            ).fetchone()

            if row:
                return int(row[0])

            # Create document with complete metadata
            doc_id = str(uuid.uuid4())
            row = self.conn.execute(
                """
                INSERT INTO documents (document_id, filename, file_size_bytes, total_pages)
                VALUES (?, ?, ?, ?)
                RETURNING id
                """,
                [doc_id, filename, file_size_bytes, total_pages],
            ).fetchone()

            if not row:
                raise RuntimeError(f"Failed to create document entry for {filename}")

            logger.info(f"Created document entry for {filename} with {total_pages} pages")
            return int(row[0])

        # Otherwise, find any document with matching filename
        row = self.conn.execute(
            """
            SELECT id FROM documents WHERE filename = ? LIMIT 1
            """,
            [filename],
        ).fetchone()

        if row:
            return int(row[0])

        # Last resort: create a minimal document entry
        # This will be updated with correct metadata during full indexing
        doc_id = str(uuid.uuid4())
        row = self.conn.execute(
            """
            INSERT INTO documents (document_id, filename, file_size_bytes, total_pages)
            VALUES (?, ?, ?, ?)
            RETURNING id
            """,
            [doc_id, filename, file_size_bytes or -1, total_pages or -1],
        ).fetchone()

        if not row:
            raise RuntimeError(f"Failed to create document entry for {filename}")

        logger.warning(
            f"Created placeholder document entry for {filename} with incomplete metadata. "
            f"This will be updated during full document indexing."
        )
        return int(row[0])


duckdb_service = DuckDBAnalyticsService()
