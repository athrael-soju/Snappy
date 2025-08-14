from typing import Optional, Dict


def compute_page_label(payload: Optional[Dict]) -> str:
    """Compute a human-friendly label for a retrieved page based on payload metadata.

    Expected payload keys (if available):
      - filename: str
      - pdf_page_index: int (1-based)
      - total_pages: int
      - index: int (fallback)
    """
    try:
        payload = payload or {}
        fname = payload.get("filename")
        page_num = payload.get("pdf_page_index")
        total = payload.get("total_pages")

        if fname and page_num and total:
            return f"{fname} — {page_num}/{total}"
        if fname and page_num:
            return f"{fname} — {page_num}"
        if page_num and total:
            return f"Page {page_num}/{total}"
        if page_num:
            return f"Page {page_num}"
        return fname or f"Index {payload.get('index', '')}"
    except Exception:
        return f"Index {payload.get('index', '')}"
