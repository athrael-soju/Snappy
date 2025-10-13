import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.dependencies import (
    get_qdrant_service,
    get_minio_service,
    qdrant_init_error,
    minio_init_error,
)
import config

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
        msg = await asyncio.to_thread(svc.clear_collection)
        return {"status": "ok", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear/minio")
async def clear_minio():
    try:
        if not config.MINIO_ENABLED:
            return {
                "status": "skipped",
                "message": "MinIO disabled via configuration",
            }
        msvc = get_minio_service()
        if not msvc:
            raise HTTPException(
                status_code=503,
                detail=f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}",
            )
        res = await asyncio.to_thread(msvc.clear_images)
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
        svc = get_qdrant_service()
        msvc = get_minio_service()
        message = await asyncio.to_thread(_clear_all_sync, svc, msvc)
        return {"status": "ok", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Get the status of collection and bucket including statistics."""
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        collection_status, bucket_status = await asyncio.gather(
            asyncio.to_thread(_collect_collection_status, svc),
            asyncio.to_thread(_collect_bucket_status, msvc),
        )
        return {
            "collection": collection_status,
            "bucket": bucket_status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize():
    """Initialize/create collection and bucket based on current configuration."""
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        return await asyncio.to_thread(_initialize_sync, svc, msvc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_collection_and_bucket():
    """Delete collection and bucket completely."""
    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        return await asyncio.to_thread(_delete_sync, svc, msvc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _collect_collection_status(svc: Optional[object]) -> dict:
    status = {
        "name": config.QDRANT_COLLECTION_NAME,
        "exists": False,
        "vector_count": 0,
        "unique_files": 0,
        "error": None,
    }
    if not svc:
        status["error"] = qdrant_init_error or "Service unavailable"
        return status
    try:
        collection_info = svc.service.get_collection(config.QDRANT_COLLECTION_NAME)
        status["exists"] = True
        status["vector_count"] = collection_info.points_count or 0
        try:
            scroll_result = svc.service.scroll(
                collection_name=config.QDRANT_COLLECTION_NAME,
                limit=10000,
                with_payload=["filename"],
                with_vectors=False,
            )
            points = scroll_result[0] if scroll_result else []
            unique_filenames = {
                point.payload["filename"]
                for point in points
                if point.payload and "filename" in point.payload
            }
            status["unique_files"] = len(unique_filenames)
        except Exception:
            # Best-effort; leave unique_files at default if scroll fails
            pass
    except Exception as exc:
        if "not found" not in str(exc).lower():
            status["error"] = str(exc)
    return status

def _collect_bucket_status(msvc: Optional[object]) -> dict:
    status = {
        "name": config.MINIO_BUCKET_NAME,
        "exists": False,
        "object_count": 0,
        "disabled": not config.MINIO_ENABLED,
        "error": None,
    }
    if not config.MINIO_ENABLED:
        status["error"] = "MinIO disabled via configuration"
        return status
    if not msvc:
        status["error"] = minio_init_error or "Service unavailable"
        return status
    try:
        bucket_exists = msvc.service.bucket_exists(config.MINIO_BUCKET_NAME)
        status["exists"] = bucket_exists
        if bucket_exists:
            objects = list(
                msvc.service.list_objects(
                    config.MINIO_BUCKET_NAME,
                    recursive=True,
                )
            )
            status["object_count"] = len(objects)
    except Exception as exc:
        status["error"] = str(exc)
    return status


def _clear_all_sync(svc: Optional[object], msvc: Optional[object]) -> str:
    if svc:
        try:
            q_msg = svc.clear_collection()
        except Exception as exc:
            q_msg = f"Qdrant clear failed: {exc}"
    else:
        q_msg = f"Qdrant unavailable: {qdrant_init_error or 'Dependency service is down'}"
    if not config.MINIO_ENABLED:
        m_msg = "MinIO disabled via configuration"
    elif msvc:
        try:
            res = msvc.clear_images()
            m_msg = (
                f"Cleared MinIO images: deleted={res.get('deleted')}, "
                f"failed={res.get('failed')}"
            )
        except Exception as exc:
            m_msg = f"MinIO clear failed: {exc}"
    else:
        m_msg = f"MinIO unavailable: {minio_init_error or 'Dependency service is down'}"
    return f"{q_msg} {m_msg}".strip()


def _initialize_sync(svc: Optional[object], msvc: Optional[object]) -> dict:
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc._create_collection_if_not_exists()
            results["collection"]["status"] = "success"
            results["collection"]["message"] = (
                f"Collection '{config.QDRANT_COLLECTION_NAME}' initialized successfully"
            )
        except Exception as exc:
            results["collection"]["status"] = "error"
            results["collection"]["message"] = str(exc)
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = qdrant_init_error or "Service unavailable"
    if not config.MINIO_ENABLED:
        results["bucket"]["status"] = "skipped"
        results["bucket"]["message"] = "MinIO disabled via configuration"
    elif msvc:
        try:
            msvc._create_bucket_if_not_exists()
            results["bucket"]["status"] = "success"
            results["bucket"]["message"] = (
                f"Bucket '{config.MINIO_BUCKET_NAME}' initialized successfully"
            )
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error or "Service unavailable"
    overall_status = "success" if (
        results["collection"]["status"] == "success"
        and results["bucket"]["status"] == "success"
    ) else "partial" if (
        results["collection"]["status"] == "success"
        or results["bucket"]["status"] == "success"
    ) else "error"
    return {"status": overall_status, "results": results}


def _delete_sync(svc: Optional[object], msvc: Optional[object]) -> dict:
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc.service.delete_collection(collection_name=config.QDRANT_COLLECTION_NAME)
            results["collection"]["status"] = "success"
            results["collection"]["message"] = (
                f"Collection '{config.QDRANT_COLLECTION_NAME}' deleted successfully"
            )
        except Exception as exc:
            if "not found" in str(exc).lower():
                results["collection"]["status"] = "success"
                results["collection"]["message"] = "Collection did not exist"
            else:
                results["collection"]["status"] = "error"
                results["collection"]["message"] = str(exc)
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = qdrant_init_error or "Service unavailable"
    if not config.MINIO_ENABLED:
        results["bucket"]["status"] = "skipped"
        results["bucket"]["message"] = "MinIO disabled via configuration"
    elif msvc:
        try:
            bucket_exists = msvc.service.bucket_exists(config.MINIO_BUCKET_NAME)
            if bucket_exists:
                objects = msvc.list_object_names(recursive=True)
                if objects:
                    from minio.deleteobjects import DeleteObject
                    delete_objects = [DeleteObject(name) for name in objects]
                    errors = list(
                        msvc.service.remove_objects(
                            config.MINIO_BUCKET_NAME,
                            delete_objects,
                        )
                    )
                    if errors:
                        results["bucket"]["status"] = "error"
                        results["bucket"]["message"] = (
                            f"Failed to delete some objects: {len(errors)} errors"
                        )
                        return {"status": "error", "results": results}
                msvc.service.remove_bucket(config.MINIO_BUCKET_NAME)
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = (
                    f"Bucket '{config.MINIO_BUCKET_NAME}' deleted successfully"
                )
            else:
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = "Bucket did not exist"
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error or "Service unavailable"
    overall_status = "success" if (
        results["collection"]["status"] == "success"
        and results["bucket"]["status"] == "success"
    ) else "partial" if (
        results["collection"]["status"] == "success"
        or results["bucket"]["status"] == "success"
    ) else "error"
    return {"status": overall_status, "results": results}
