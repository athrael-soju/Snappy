"""DuckDB analytics service implementation."""

from __future__ import annotations

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
            "ocr_pages": self._count_table("ocr_pages"),
            "ocr_regions": self._count_table("ocr_regions"),
            "ocr_extracted_images": self._count_table("ocr_extracted_images"),
        }

        return InfoResponse(
            version=settings.API_VERSION,
            database_path=str(db_path),
            database_size_mb=round(size_mb, 2),
            tables=tables,
        )

    def _count_table(self, table: str) -> int:
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(result[0]) if result else 0

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    def store_page(self, payload: OcrPageData) -> Dict[str, Any]:
        """Store a single OCR page and its columnar data."""
        conn = self.conn

        self._delete_page_rows(payload.filename, payload.page_number)

        row = conn.execute(
            """
            INSERT INTO ocr_pages (
                provider, version, filename, page_number, text, markdown, raw_text,
                extracted_at, storage_url, document_id, pdf_page_index, total_pages,
                page_width_px, page_height_px, image_url, image_storage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [
                payload.provider,
                payload.version,
                payload.filename,
                payload.page_number,
                payload.text,
                payload.markdown,
                payload.raw_text,
                payload.extracted_at,
                payload.storage_url,
                payload.document_id,
                payload.pdf_page_index,
                payload.total_pages,
                payload.page_width_px,
                payload.page_height_px,
                payload.image_url,
                payload.image_storage,
            ],
        ).fetchone()

        if not row:
            raise RuntimeError("Failed to insert OCR page")

        page_id = int(row[0])
        self._insert_regions(page_id, payload.regions)
        self._insert_images(page_id, payload.extracted_images)

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
            """
            DELETE FROM ocr_regions
            WHERE page_id IN (
                SELECT id FROM ocr_pages WHERE filename = ? AND page_number = ?
            )
            """,
            params,
        )
        self.conn.execute(
            """
            DELETE FROM ocr_extracted_images
            WHERE page_id IN (
                SELECT id FROM ocr_pages WHERE filename = ? AND page_number = ?
            )
            """,
            params,
        )
        self.conn.execute(
            "DELETE FROM ocr_pages WHERE filename = ? AND page_number = ?",
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
        db_manager.connect()
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
                (SELECT COUNT(*) FROM ocr_pages) AS pages,
                (SELECT COUNT(*) FROM ocr_regions) AS regions,
                (SELECT COUNT(*) FROM ocr_extracted_images) AS images
            """
        ).fetchone()

        self.conn.execute("DELETE FROM ocr_regions")
        self.conn.execute("DELETE FROM ocr_extracted_images")
        self.conn.execute("DELETE FROM ocr_pages")

        cleared_pages = counts[0] if counts else 0
        cleared_regions = counts[1] if counts else 0
        cleared_images = counts[2] if counts else 0

        return {
            "status": "success",
            "message": "Cleared DuckDB tables",
            "cleared_pages": cleared_pages,
            "cleared_regions": cleared_regions,
            "cleared_images": cleared_images,
        }

    def delete_storage(self) -> Dict[str, Any]:
        """Delete the DuckDB database file and recreate a clean schema."""
        db_manager.close()
        db_path = Path(settings.DUCKDB_DATABASE_PATH)
        removed = False
        if db_path.exists():
            db_path.unlink()
            removed = True

        db_manager.connect()
        return {
            "status": "success",
            "message": "DuckDB database file reset",
            "file_removed": removed,
        }

    def _insert_regions(self, page_id: int, regions: Sequence[Dict[str, Any]]) -> None:
        if not regions:
            return

        rows: List[Tuple[Any, ...]] = []
        for region in regions:
            bbox = region.get("bbox") or [None, None, None, None]
            x1, y1, x2, y2 = self._parse_bbox(bbox)
            rows.append(
                (
                    page_id,
                    region.get("id"),
                    region.get("label"),
                    x1,
                    y1,
                    x2,
                    y2,
                    region.get("content"),
                    region.get("image_url"),
                    region.get("image_storage"),
                    self._to_bool(region.get("image_inline")),
                )
            )

        self.conn.executemany(
            """
            INSERT INTO ocr_regions (
                page_id, region_id, label, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                content, image_url, image_storage, image_inline
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def _insert_images(self, page_id: int, images: Sequence[Dict[str, Any]]) -> None:
        if not images:
            return

        rows = []
        for idx, image in enumerate(images):
            rows.append((page_id, idx, image.get("url"), image.get("storage")))

        self.conn.executemany(
            """
            INSERT INTO ocr_extracted_images (page_id, image_index, url, storage)
            VALUES (?, ?, ?, ?)
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
                COALESCE(SUM(r.region_count), 0) AS total_regions,
                COALESCE(SUM(i.image_count), 0) AS total_extracted_images
            FROM ocr_pages p
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS region_count
                FROM ocr_regions
                GROUP BY page_id
            ) r ON p.id = r.page_id
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS image_count
                FROM ocr_extracted_images
                GROUP BY page_id
            ) i ON p.id = i.page_id
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
                total_extracted_images=row[5],
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
                COALESCE(SUM(r.region_count), 0) AS total_regions,
                COALESCE(SUM(i.image_count), 0) AS total_extracted_images
            FROM ocr_pages p
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS region_count
                FROM ocr_regions
                GROUP BY page_id
            ) r ON p.id = r.page_id
            LEFT JOIN (
                SELECT page_id, COUNT(*) AS image_count
                FROM ocr_extracted_images
                GROUP BY page_id
            ) i ON p.id = i.page_id
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
            total_extracted_images=row[5],
        )

    def get_page(self, filename: str, page_number: int) -> Dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT
                id, provider, version, filename, page_number, text, markdown, raw_text,
                extracted_at, storage_url, document_id, pdf_page_index, total_pages,
                page_width_px, page_height_px, image_url, image_storage, created_at
            FROM ocr_pages
            WHERE filename = ? AND page_number = ?
            """,
            [filename, page_number],
        ).fetchone()

        if not row:
            raise ValueError("Page not found")

        page_id = row[0]
        regions = self._fetch_regions(page_id)
        images = self._fetch_images(page_id)

        return {
            "provider": row[1],
            "version": row[2],
            "filename": row[3],
            "page_number": row[4],
            "text": row[5],
            "markdown": row[6],
            "raw_text": row[7],
            "regions": regions,
            "extracted_at": str(row[8]),
            "storage_url": row[9],
            "document_id": row[10],
            "pdf_page_index": row[11],
            "total_pages": row[12],
            "page_width_px": row[13],
            "page_height_px": row[14],
            "image_url": row[15],
            "image_storage": row[16],
            "extracted_images": images,
            "created_at": str(row[17]),
        }

    def _fetch_regions(self, page_id: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT
                region_id, label, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                content, image_url, image_storage, image_inline
            FROM ocr_regions
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
                    "image_url": row[7],
                    "image_storage": row[8],
                    "image_inline": row[9],
                }
            )
        return regions

    def _fetch_images(self, page_id: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT url, storage
            FROM ocr_extracted_images
            WHERE page_id = ?
            ORDER BY image_index
            """,
            [page_id],
        ).fetchall()

        images: List[Dict[str, Any]] = []
        for row in rows:
            images.append({"url": row[0], "storage": row[1]})
        return images

    def delete_document(self, filename: str) -> Dict[str, Any]:
        count_row = self.conn.execute(
            "SELECT COUNT(*) FROM ocr_pages WHERE filename = ?", [filename]
        ).fetchone()
        deleted_pages = int(count_row[0]) if count_row else 0

        if deleted_pages == 0:
            raise ValueError("Document not found")

        self.conn.execute(
            """
            DELETE FROM ocr_regions
            WHERE page_id IN (
                SELECT id FROM ocr_pages WHERE filename = ?
            )
            """,
            [filename],
        )
        self.conn.execute(
            """
            DELETE FROM ocr_extracted_images
            WHERE page_id IN (
                SELECT id FROM ocr_pages WHERE filename = ?
            )
            """,
            [filename],
        )
        self.conn.execute("DELETE FROM ocr_pages WHERE filename = ?", [filename])

        logger.info("Deleted %s pages for document %s", deleted_pages, filename)
        return {"status": "success", "deleted_pages": deleted_pages}

    def run_query(self, request: QueryRequest) -> QueryResponse:
        query = request.query.strip()
        if not query:
            raise ValueError("Query is required")

        query_upper = query.upper()
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

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
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {request.limit}"

        result = self.conn.execute(query)
        rows = self._format_rows(result.fetchall())
        columns = [desc[0] for desc in result.description] if result.description else []

        return QueryResponse(
            columns=columns, rows=rows, row_count=len(rows), query=query
        )

    def stats(self) -> StatsResponse:
        total_docs = self.conn.execute(
            "SELECT COUNT(DISTINCT filename) FROM ocr_pages"
        ).fetchone()[0]

        total_pages = self.conn.execute("SELECT COUNT(*) FROM ocr_pages").fetchone()[0]
        total_regions = self.conn.execute(
            "SELECT COUNT(*) FROM ocr_regions"
        ).fetchone()[0]

        total_images = self.conn.execute(
            "SELECT COUNT(*) FROM ocr_extracted_images"
        ).fetchone()[0]

        providers_result = self.conn.execute(
            "SELECT provider, COUNT(*) FROM ocr_pages GROUP BY provider"
        ).fetchall()
        providers = {row[0]: row[1] for row in providers_result}

        db_path = Path(settings.DUCKDB_DATABASE_PATH)
        size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0.0

        return StatsResponse(
            total_documents=total_docs,
            total_pages=total_pages,
            total_regions=total_regions,
            total_extracted_images=total_images,
            providers=providers,
            storage_size_mb=round(size_mb, 2),
        )

    def search_text(self, query: str, limit: int) -> QueryResponse:
        result = self.conn.execute(
            """
            SELECT filename, page_number, text, markdown, extracted_at
            FROM ocr_pages
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


duckdb_service = DuckDBAnalyticsService()
