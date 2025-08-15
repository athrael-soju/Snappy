import os
import io
import base64
from typing import List, Optional, Dict


from fastapi import HTTPException
from pdf2image import convert_from_path

from config import WORKER_THREADS


BRAIN_PLACEHOLDERS = [
    "🙂 Consulting the hippocampus…",
    "🧩 Rewiring a few synapses…",
    "🧮 Counting neurons (still a lot)…",
    "📚 Indexing mental PDFs…",
    "📟 Paging working memory…",
    "📑 Cross-referencing footnotes in my head…",
    "🧠 Spinning up the prefrontal cortex…",
    "✏️ Sharpening imaginary pencils…",
    "🤔 Goog... I mean, thinking really hard…",
    "🏃‍♂️ Chasing a thought that just ran by…",
    "🔭 Polishing cognitive lenses…",
    "🏰 Defragmenting the memory palace…",
    "🧬 Tickling the basal ganglia for hints…",
    "⏳ Buffering stray ideas…",
    "🎛️ Warming up the cerebellum…",
    "🧶 Untangling a thought knot…",
    "🗂️ Dusting off mental index cards…",
    "✅ Running a quick sanity check…",
    "🍊 Squeezing a bit more brain juice…",
    "📐 Aligning mental vectors…",
    "🧑‍🏫 Asking my inner librarian…",
    "💻 Compiling neural code…",
    "🔓 Decrypting a vague hunch…",
    "🗃️ Sorting concepts by relevance…",
    "🧲 Fetching semantic embeddings…",
    "☕ Brewing a fresh insight…",
    "🐑 Herding stray neurons…",
    "🔮 Consulting the oracle of memory…",
    "📥 Caching the gist…",
    "🗺️ Mapping the idea space…",
    "🔀 Rerouting around confusion…",
    "🎚️ Calibrating intuition…",
    "💧 Rehydrating context…",
    "🔎 Zooming in on the crux…",
    "🗜️ Zipping up stray thoughts…",
    "📡 Pinging associative networks…",
    "📏 Lining up evidence…",
    "⚗️ Fusing facts with logic…",
    "🧰 Refactoring the mental model…",
    "🧐 Cross checking assumptions…",
    "🎭 Peeking behind the abstraction curtain…",
    "👉 Nudging attention back on track…",
    "🪜 Filling in missing steps…",
    "🗣️ Translating gut feeling into words…",
    "✂️ Pruning irrelevant branches…",
    "⬆️ Upgrading the working hypothesis…",
    "🧊 Crunching the edge cases…",
    "🔁 Double checking the premises…",
    "🔄 Looping through possibilities…",
    "📘 Finalizing the answer blueprint…",
]


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
