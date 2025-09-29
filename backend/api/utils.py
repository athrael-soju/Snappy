import os
from typing import List, Dict


from fastapi import HTTPException
from pdf2image import convert_from_path

from config import WORKER_THREADS


def convert_pdf_paths_to_images(paths: List[str], original_filenames: Dict[str, str] = None) -> List[dict]:
    """Convert PDF files to images with metadata.
    
    Args:
        paths: List of file paths (may be temporary files)
        original_filenames: Optional mapping of path -> original filename
    """
    items: List[dict] = []
    for f in paths:
        try:
            pages = convert_from_path(f, thread_count=int(WORKER_THREADS))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to convert PDF {f}: {e}"
            )
        total = len(pages)
        try:
            size_bytes = os.path.getsize(f)
        except Exception:
            size_bytes = None
        
        # Use original filename if provided, otherwise fall back to basename
        if original_filenames and f in original_filenames:
            filename = original_filenames[f]
        else:
            filename = os.path.basename(str(f))
            
        for idx, img in enumerate(pages):
            w, h = (img.size[0], img.size[1]) if hasattr(img, "size") else (None, None)
            items.append(
                {
                    "image": img,
                    "filename": filename,
                    "file_size_bytes": size_bytes,
                    "pdf_page_index": idx + 1,  # 1-based
                    "total_pages": total,
                    "page_width_px": w,
                    "page_height_px": h,
                }
            )
    return items


def compute_page_label(payload: Dict) -> str:
    """Compute a human-friendly label for a retrieved page.

    Required payload keys:
      - filename: str
      - pdf_page_index: int (1-based)
      - total_pages: int
    
    Returns format: "filename.pdf — Page X of Y"
    """
    fname = payload["filename"]
    page_num = payload["pdf_page_index"]
    total = payload["total_pages"]
    return f"{fname} — Page {page_num} of {total}"
