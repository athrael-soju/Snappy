"""PDF rasterization stage for streaming pipeline."""

import logging
import queue
import uuid
from pathlib import Path
from typing import Callable, List, Optional

import config
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image

from ..streaming_types import PageBatch

logger = logging.getLogger(__name__)


class PDFRasterizer:
    """Streams PDF pages as batches without waiting for all pages."""

    def __init__(
        self,
        batch_size: int = 4,
        worker_threads: Optional[int] = None,
    ):
        self.batch_size = batch_size
        self.worker_threads = worker_threads or config.get_ingestion_worker_threads()

    def rasterize_streaming(
        self,
        pdf_path: str,
        filename: str,
        document_id: str,
        output_queues: List[queue.Queue],
        cancellation_check: Optional[Callable] = None,
        batch_semaphore: Optional = None,
    ) -> int:
        """
        Rasterize PDF and broadcast batches to all output queues.

        Args:
            pdf_path: Path to PDF file
            filename: Display name for the document
            document_id: Unique document identifier
            output_queues: List of queues to broadcast batches to
            cancellation_check: Optional function to check for cancellation
            batch_semaphore: Optional semaphore to limit in-flight batches

        Returns:
            Total number of pages processed
        """
        try:
            # Get total pages
            info = pdfinfo_from_path(pdf_path)
            total_pages = int(info.get("Pages", 0))

            # Get file size
            file_size_bytes = Path(pdf_path).stat().st_size

            logger.info(
                f"Starting streaming rasterization: {filename} "
                f"({total_pages} pages, {file_size_bytes / 1024 / 1024:.1f} MB)"
            )

            batch_id = 0
            page = 1

            while page <= total_pages:
                # Check cancellation before expensive operation
                if cancellation_check:
                    cancellation_check()

                # Acquire semaphore before starting batch (blocks if at limit)
                # Use timeout to allow periodic cancellation checks
                semaphore_acquired = False
                if batch_semaphore:
                    while not semaphore_acquired:
                        semaphore_acquired = batch_semaphore.acquire(timeout=0.5)
                        if not semaphore_acquired and cancellation_check:
                            # Check cancellation while waiting for semaphore
                            cancellation_check()

                try:
                    # Rasterize next batch
                    last_page = min(page + self.batch_size - 1, total_pages)

                    logger.debug(f"Rasterizing pages {page}-{last_page} of {total_pages}")

                    images = convert_from_path(
                        pdf_path,
                        thread_count=self.worker_threads,
                        first_page=page,
                        last_page=last_page,
                    )

                    # Force load all images to avoid lazy-loading issues when copying
                    # PIL Images are lazy-loaded by default, calling load() forces data into memory
                    for img in images:
                        img.load()

                    # Generate unique image IDs for this batch (shared across all stages)
                    image_ids = [str(uuid.uuid4()) for _ in images]

                    # Build metadata for each page
                    metadata = []
                    for offset, img in enumerate(images):
                        page_num = page + offset
                        width, height = img.size if hasattr(img, "size") else (None, None)

                        metadata.append({
                            "document_id": document_id,
                            "page_id": image_ids[offset],  # Match page_id to image_id
                            "filename": filename,
                            "page_number": page_num,
                            "pdf_page_index": page_num,
                            "total_pages": total_pages,
                            "page_width_px": width,
                            "page_height_px": height,
                            "file_size_bytes": file_size_bytes,
                        })

                    # Broadcast to all output queues with independent copies
                    # Each consumer gets its own copy of the images to avoid PIL threading issues
                    for i, q in enumerate(output_queues):
                        # Create deep copy of images for thread safety
                        # PIL Image objects are not thread-safe when shared
                        images_copy = [img.copy() for img in images] if i > 0 else images

                        batch = PageBatch(
                            document_id=document_id,
                            filename=filename,
                            batch_id=batch_id,
                            page_start=page,
                            images=images_copy,
                            image_ids=image_ids.copy(),  # Share same IDs across all stages
                            metadata=metadata.copy(),
                            total_pages=total_pages,
                            file_size_bytes=file_size_bytes,
                        )
                        q.put(batch, block=True)

                    logger.debug(
                        f"Broadcast batch {batch_id} (pages {page}-{last_page}) to {len(output_queues)} queues"
                    )

                    batch_id += 1
                    page = last_page + 1
                except Exception:
                    # Release semaphore on error (including cancellation)
                    if semaphore_acquired:
                        batch_semaphore.release()
                    raise

            logger.info(
                f"Completed rasterization: {filename} "
                f"({total_pages} pages in {batch_id} batches)"
            )

            return total_pages

        except Exception as exc:
            logger.error(f"Rasterization failed for {filename}: {exc}", exc_info=True)
            raise
