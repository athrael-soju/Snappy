from fastapi import APIRouter, HTTPException

from api.dependencies import (
    get_qdrant_service,
    get_minio_service,
    qdrant_init_error,
    minio_init_error,
)

router = APIRouter(prefix="", tags=["maintenance"])


@router.post("/clear/qdrant")
async def clear_qdrant():
    try:
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error or 'Dependency services are down'}",
            )
        msg = svc.clear_collection()
        return {"status": "ok", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/minio")
async def clear_minio():
    try:
        msvc = get_minio_service()
        if not msvc:
            raise HTTPException(
                status_code=503,
                detail=f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}",
            )
        res = msvc.clear_images()
        return {
            "status": "ok",
            "deleted": res.get("deleted"),
            "failed": res.get("failed"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/all")
async def clear_all():
    try:
        # Clear Qdrant (if available)
        q_msg = ""
        svc = get_qdrant_service()
        if svc:
            try:
                q_msg = svc.clear_collection()
            except Exception as qe:
                q_msg = f"Qdrant clear failed: {qe}"
        else:
            q_msg = f"Qdrant unavailable: {qdrant_init_error or 'Dependency service is down'}"

        # Clear MinIO (independent of Qdrant)
        m_msg = ""
        msvc = get_minio_service()
        if msvc:
            try:
                res = msvc.clear_images()
                m_msg = f"Cleared MinIO images: deleted={res.get('deleted')}, failed={res.get('failed')}"
            except Exception as me:
                m_msg = f"MinIO clear failed: {me}"
        else:
            m_msg = (
                f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}"
            )

        return {"status": "ok", "message": f"{q_msg} {m_msg}".strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
