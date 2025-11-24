from typing import Dict


def compute_page_label(payload: Dict) -> str:
    """Compute a human-friendly label for a retrieved page."""
    fname = payload["filename"]
    page_num = payload["pdf_page_index"]
    total = payload["total_pages"]
    return f"{fname} - Page {page_num} of {total}"
