"""Database initialization and lifecycle helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import logger

import duckdb


class DuckDBManager:
    """Manage the DuckDB connection and schema."""

    def __init__(self) -> None:
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._allow_connections = True

    def connect(self, *, force: bool = False) -> duckdb.DuckDBPyConnection:
        """Connect to DuckDB and ensure schema exists."""
        if self._connection:
            return self._connection

        if not self._allow_connections and not force:
            raise RuntimeError(
                "DuckDB storage is unavailable. Run the maintenance initialize action to recreate it."
            )

        db_path = Path(settings.DUCKDB_DATABASE_PATH)
        self._cleanup_wal(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing DuckDB database at %s", db_path)
        self._connection = duckdb.connect(str(db_path))
        self._allow_connections = True

        self._start_ui_extension()
        self._create_schema()

        return self._connection

    def _start_ui_extension(self) -> None:
        """Install and start the DuckDB UI extension if available."""
        if not self._connection:
            return

        try:
            self._connection.execute("INSTALL ui;")
            self._connection.execute("LOAD ui;")
            self._connection.execute("CALL start_ui_server();")
            logger.info("DuckDB UI server started on http://0.0.0.0:4213")
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.warning("DuckDB UI extension unavailable: %s", exc)

    def _create_schema(self) -> None:
        """Create the analytics schema with columnar tables.

        Schema design principles:
        - ocr_pages: Core page metadata with MinIO references
        - ocr_regions: Structured text regions with bounding boxes
        - Minimal duplication: Full data lives in MinIO, DB has queryable metadata
        - Retrieval: Query by (filename, page_number) matching Qdrant payload
        """
        if not self._connection:
            return

        self._connection.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS ocr_pages_id_seq START 1;
            CREATE SEQUENCE IF NOT EXISTS ocr_regions_id_seq START 1;

            CREATE TABLE IF NOT EXISTS ocr_pages (
                id INTEGER PRIMARY KEY DEFAULT nextval('ocr_pages_id_seq'),
                filename VARCHAR NOT NULL,
                page_number INTEGER NOT NULL,
                page_width_px INTEGER,
                page_height_px INTEGER,
                image_url VARCHAR,
                text TEXT,
                markdown TEXT,
                storage_url VARCHAR NOT NULL,
                extracted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, page_number)
            );

            CREATE TABLE IF NOT EXISTS ocr_regions (
                id INTEGER PRIMARY KEY DEFAULT nextval('ocr_regions_id_seq'),
                page_id INTEGER NOT NULL,
                region_id VARCHAR,
                label VARCHAR,
                bbox_x1 INTEGER,
                bbox_y1 INTEGER,
                bbox_x2 INTEGER,
                bbox_y2 INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(page_id) REFERENCES ocr_pages(id)
            );
            """
        )

        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pages_filename ON ocr_pages(filename);
            CREATE INDEX IF NOT EXISTS idx_pages_page_number ON ocr_pages(page_number);
            CREATE INDEX IF NOT EXISTS idx_pages_filename_page ON ocr_pages(filename, page_number);
            CREATE INDEX IF NOT EXISTS idx_pages_extracted_at ON ocr_pages(extracted_at);
            CREATE INDEX IF NOT EXISTS idx_pages_text_fts ON ocr_pages(text);

            CREATE INDEX IF NOT EXISTS idx_regions_page_id ON ocr_regions(page_id);
            CREATE INDEX IF NOT EXISTS idx_regions_label ON ocr_regions(label);
            CREATE INDEX IF NOT EXISTS idx_regions_content_fts ON ocr_regions(content);
            """
        )

        logger.info("DuckDB schema ready")

    def close(self) -> None:
        """Close the DuckDB connection and stop the UI server."""
        if not self._connection:
            return

        try:
            self._connection.execute("CALL stop_ui_server();")
            logger.info("DuckDB UI server stopped")
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.debug("UI server stop warning: %s", exc)

        self._connection.close()
        self._connection = None
        logger.info("DuckDB connection closed")

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Return the active DuckDB connection, reconnecting if needed."""
        if not self._connection:
            return self.connect()
        return self._connection

    def mark_deleted(self) -> None:
        """Mark DuckDB as deleted until explicitly initialized."""
        self._allow_connections = False
        self._connection = None

    def ensure_schema(self) -> None:
        """Recreate schema even if already connected."""
        if not self._connection:
            self.connect(force=True)
        self._create_schema()

    @staticmethod
    def _cleanup_wal(db_path: Path) -> None:
        wal_path = db_path.with_suffix(db_path.suffix + ".wal")
        if wal_path.exists():
            try:
                wal_path.unlink()
                logger.info("Removed stale DuckDB WAL file at %s", wal_path)
            except OSError as exc:  # pragma: no cover - best effort
                logger.warning("Failed to remove WAL file %s: %s", wal_path, exc)


db_manager = DuckDBManager()
