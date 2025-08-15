import os
import io
import base64
import tempfile
from typing import List

from fastapi import HTTPException
from pdf2image import convert_from_path

from config import WORKER_THREADS


def encode_pil_to_data_url(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def convert_pdf_paths_to_images(paths: List[str]) -> List[dict]:
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
