import os
from typing import List, Dict, Generator, Tuple

from fastapi import HTTPException
from pdf2image import convert_from_path, pdfinfo_from_path

import config  # Import module for dynamic config access


def convert_pdf_paths_to_images_streaming(paths: List[str], original_filenames: Dict[str, str] = None, batch_size: int = 10) -> Generator[Tuple[dict, int], None, None]:
    """Convert PDF files to images with metadata, yielding pages incrementally in batches.
    
    Args:
        paths: List of file paths (may be temporary files)
        original_filenames: Optional mapping of path -> original filename
        batch_size: Number of pages to convert at once (default: 10)
        
    Yields:
        Tuple of (page_dict, total_pages_across_all_files)
    """
    # First pass: count total pages across all PDFs (fast metadata read)
    total_pages_all_files = 0
    for f in paths:
        try:
            info = pdfinfo_from_path(f)
            total_pages_all_files += info.get("Pages", 1)
        except Exception:
            # Fallback: we'll count during conversion
            total_pages_all_files = -1  # Unknown
            break
    
    # Second pass: convert pages in batches and yield incrementally
    for f in paths:
        try:
            size_bytes = os.path.getsize(f)
        except Exception:
            size_bytes = None
        
        # Use original filename if provided
        if original_filenames and f in original_filenames:
            filename = original_filenames[f]
        else:
            filename = os.path.basename(str(f))
        
        # Get total page count for this file
        try:
            info = pdfinfo_from_path(f)
            total_pages_this_file = info.get("Pages", 1)
        except Exception:
            # Fallback: convert first batch to count
            total_pages_this_file = -1
        
        # If we didn't get total earlier, use current file count as estimate
        if total_pages_all_files == -1:
            total_pages_all_files = total_pages_this_file if total_pages_this_file > 0 else 1
        
        # Convert pages in batches to reduce memory usage
        try:
            page_num = 1
            while page_num <= total_pages_this_file or total_pages_this_file == -1:
                # Convert a batch of pages
                batch_end = min(page_num + batch_size - 1, total_pages_this_file) if total_pages_this_file > 0 else page_num + batch_size - 1
                
                try:
                    pages = convert_from_path(
                        f, 
                        first_page=page_num,
                        last_page=batch_end,
                        thread_count=int(config.WORKER_THREADS)
                    )
                except Exception as e:
                    # If batch conversion fails and we don't know total, we're done
                    if total_pages_this_file == -1:
                        break
                    raise
                
                # Update total if we didn't know it
                if total_pages_this_file == -1 and len(pages) < batch_size:
                    total_pages_this_file = page_num + len(pages) - 1
                    total_pages_all_files = total_pages_this_file
                
                # Yield each page in the batch
                for idx, img in enumerate(pages):
                    w, h = (img.size[0], img.size[1]) if hasattr(img, "size") else (None, None)
                    page_dict = {
                        "image": img,
                        "filename": filename,
                        "file_size_bytes": size_bytes,
                        "pdf_page_index": page_num + idx,
                        "total_pages": total_pages_this_file,
                        "page_width_px": w,
                        "page_height_px": h,
                    }
                    yield (page_dict, total_pages_all_files)
                
                page_num += len(pages)
                
                # Break if we got fewer pages than requested (end of document)
                if len(pages) < batch_size:
                    break
                    
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to convert PDF {f}: {e}"
            )


def convert_pdf_paths_to_images(paths: List[str], original_filenames: Dict[str, str] = None) -> List[dict]:
    """Convert PDF files to images with metadata (batch mode - loads all at once).
    
    Args:
        paths: List of file paths (may be temporary files)
        original_filenames: Optional mapping of path -> original filename
    """
    items: List[dict] = []
    for page_dict, _ in convert_pdf_paths_to_images_streaming(paths, original_filenames):
        items.append(page_dict)
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
