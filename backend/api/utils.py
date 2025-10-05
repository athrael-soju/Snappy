import os
import logging
from typing import Dict, Iterator, List, Tuple

from fastapi import HTTPException
from pdf2image import convert_from_path, pdfinfo_from_path

import config  # Import module for dynamic config access

logger = logging.getLogger(__name__)


def convert_pdf_paths_to_images(
    paths: List[str],
    original_filenames: Dict[str, str] | None = None,
    batch_size: int | None = None,
) -> Tuple[int, Iterator[dict]]:
    """Stream PDF pages as image dictionaries instead of materialising them all at once."""
    if not paths:
        return 0, iter(())

    conversion_batch_size = batch_size or max(1, int(config.BATCH_SIZE))
    sources: List[dict] = []
    total_pages = 0

    for pdf_path in paths:
        try:
            info = pdfinfo_from_path(pdf_path)
            pages = int(info.get("Pages", 0))
        except Exception as exc:  # pragma: no cover - defensive guard
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read PDF metadata for {pdf_path}: {exc}",
            ) from exc

        try:
            size_bytes = os.path.getsize(pdf_path)
        except Exception:
            size_bytes = None

        filename = (
            original_filenames.get(pdf_path)
            if original_filenames and pdf_path in original_filenames
            else os.path.basename(str(pdf_path))
        )

        sources.append(
            {
                "path": pdf_path,
                "filename": filename,
                "file_size_bytes": size_bytes,
                "total_pages": pages,
            }
        )
        total_pages += pages

    def _image_iterator() -> Iterator[dict]:
        for source in sources:
            path = source["path"]
            total = source["total_pages"]
            if total <= 0:
                logger.warning("PDF %s reported zero pages; skipping", path)
                continue

            page = 1
            while page <= total:
                last_page = min(page + conversion_batch_size - 1, total)
                try:
                    images = convert_from_path(
                        path,
                        thread_count=int(config.WORKER_THREADS),
                        first_page=page,
                        last_page=last_page,
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    raise HTTPException(
                        status_code=400, detail=f"Failed to convert PDF {path}: {exc}"
                    ) from exc

                for offset, img in enumerate(images):
                    width, height = (
                        (img.size[0], img.size[1]) if hasattr(img, "size") else (None, None)
                    )
                    yield {
                        "image": img,
                        "filename": source["filename"],
                        "file_size_bytes": source["file_size_bytes"],
                        "pdf_page_index": page + offset,
                        "total_pages": total,
                        "page_width_px": width,
                        "page_height_px": height,
                    }

                page = last_page + 1

    return total_pages, _image_iterator()


def compute_page_label(payload: Dict) -> str:
    """Compute a human-friendly label for a retrieved page."""
    fname = payload["filename"]
    page_num = payload["pdf_page_index"]
    total = payload["total_pages"]
    return f"{fname} - Page {page_num} of {total}"
