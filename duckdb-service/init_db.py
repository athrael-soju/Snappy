"""
DuckDB initialization script.

Creates the database schema for OCR data storage.
"""

import logging

import duckdb

logger = logging.getLogger(__name__)


def initialize_database(db_path: str) -> None:
    """Initialize DuckDB database with OCR schema."""
    conn = duckdb.connect(db_path)

    try:
        # Main OCR results table
        conn.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS ocr_results_seq START 1
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY DEFAULT nextval('ocr_results_seq'),
                filename VARCHAR NOT NULL,
                page_number INTEGER NOT NULL,
                provider VARCHAR NOT NULL,
                version VARCHAR,
                text TEXT,
                markdown TEXT,
                raw_text TEXT,
                extracted_at TIMESTAMP,
                storage_url VARCHAR,
                document_id VARCHAR,
                pdf_page_index INTEGER,
                total_pages INTEGER,
                page_width_px INTEGER,
                page_height_px INTEGER,
                image_url VARCHAR,
                image_storage VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, page_number)
            )
        """
        )

        # Regions table for detailed text regions
        conn.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS ocr_regions_seq START 1
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_regions (
                id INTEGER PRIMARY KEY DEFAULT nextval('ocr_regions_seq'),
                ocr_result_id INTEGER NOT NULL,
                region_type VARCHAR,
                content TEXT,
                bbox_x1 DOUBLE,
                bbox_y1 DOUBLE,
                bbox_x2 DOUBLE,
                bbox_y2 DOUBLE,
                bbox_x3 DOUBLE,
                bbox_y3 DOUBLE,
                bbox_x4 DOUBLE,
                bbox_y4 DOUBLE,
                confidence DOUBLE,
                image_url VARCHAR,
                image_storage VARCHAR,
                FOREIGN KEY (ocr_result_id) REFERENCES ocr_results(id)
            )
        """
        )

        # Extracted images table
        conn.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS ocr_extracted_images_seq START 1
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_extracted_images (
                id INTEGER PRIMARY KEY DEFAULT nextval('ocr_extracted_images_seq'),
                ocr_result_id INTEGER NOT NULL,
                image_url VARCHAR NOT NULL,
                storage VARCHAR,
                image_index INTEGER,
                FOREIGN KEY (ocr_result_id) REFERENCES ocr_results(id)
            )
        """
        )

        # Create indexes for common queries
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ocr_filename 
            ON ocr_results(filename)
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ocr_document_id 
            ON ocr_results(document_id)
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ocr_extracted_at 
            ON ocr_results(extracted_at)
        """
        )

        logger.info("DuckDB schema initialized successfully")

    finally:
        conn.close()
