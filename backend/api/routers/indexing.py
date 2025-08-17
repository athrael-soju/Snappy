import os
import tempfile
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from api.dependencies import get_qdrant_service, qdrant_init_error
from api.utils import convert_pdf_paths_to_images

router = APIRouter(prefix="", tags=["indexing"])


@router.post("/index")
async def index(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths: List[str] = []
    try:
        for uf in files:
            # Persist to a temporary file so pdf2image can read
            suffix = os.path.splitext(uf.filename or "")[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                data = await uf.read()
                tmp.write(data)
                temp_paths.append(tmp.name)

        images_with_meta = convert_pdf_paths_to_images(temp_paths)
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )
        message = svc.index_documents(images_with_meta)
        return {"status": "ok", "message": message, "pages": len(images_with_meta)}
    finally:
        for p in temp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass
