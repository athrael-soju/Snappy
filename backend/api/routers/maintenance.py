import asyncio
from typing import TYPE_CHECKING, Optional

from api.dependencies import (
    get_minio_service,
    get_qdrant_service,
    minio_init_error,
    qdrant_init_error,
)
from fastapi import APIRouter, HTTPException

try:  # pragma: no cover - tooling support
    import config  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from backend import config as config  # type: ignore

if TYPE_CHECKING:
    from app.integrations.minio_client import MinioClient
    from app.integrations.qdrant import QdrantService

_get_config = getattr  # alias for static analysis friendliness


def _collection_name() -> str:
    return str(getattr(config, "QDRANT_COLLECTION_NAME", ""))


def _bucket_name() -> str:
    return str(getattr(config, "MINIO_BUCKET_NAME", ""))


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
        msvc = get_minio_service()
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


def _collect_collection_status(svc: Optional["QdrantService"]) -> dict:
    collection_name = _collection_name()
    embedded = bool(getattr(config, "QDRANT_EMBEDDED", False))
    status = {
        "name": collection_name,
        "exists": False,
        "vector_count": 0,
        "unique_files": 0,
        "error": None,
        "embedded": embedded,
        "image_store_mode": "minio",
    }
    if not svc:
        status["error"] = qdrant_init_error or "Service unavailable"
        return status
    try:
        collection_info = svc.service.get_collection(collection_name)
        status["exists"] = True
        status["vector_count"] = collection_info.points_count or 0
        try:
            scroll_result = svc.service.scroll(
                collection_name=collection_name,
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


def _collect_bucket_status(msvc: Optional["MinioClient"]) -> dict:
    bucket_name = _bucket_name()

    status = {
        "name": bucket_name,
        "exists": False,
        "object_count": 0,
        "error": None,
    }
    if not msvc:
        status["error"] = minio_init_error or "Service unavailable"
        return status
    try:
        bucket_exists = msvc.service.bucket_exists(bucket_name)
        status["exists"] = bucket_exists
        if bucket_exists:
            objects = list(
                msvc.service.list_objects(
                    bucket_name,
                    recursive=True,
                )
            )
            status["object_count"] = len(objects)
    except Exception as exc:
        status["error"] = str(exc)
    return status


def _clear_all_sync(
    svc: Optional["QdrantService"], msvc: Optional["MinioClient"]
) -> str:
    _collection_name()
    if svc:
        try:
            q_msg = svc.clear_collection()
        except Exception as exc:
            q_msg = f"Qdrant clear failed: {exc}"
    else:
        q_msg = (
            f"Qdrant unavailable: {qdrant_init_error or 'Dependency service is down'}"
        )
    if msvc:
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


def _initialize_sync(
    svc: Optional["QdrantService"], msvc: Optional["MinioClient"]
) -> dict:
    collection_name = _collection_name()
    bucket_name = _bucket_name()
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc._create_collection_if_not_exists()
            results["collection"]["status"] = "success"
            results["collection"][
                "message"
            ] = f"Collection '{collection_name}' initialized successfully"
        except Exception as exc:
            results["collection"]["status"] = "error"
            results["collection"]["message"] = str(exc)
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = qdrant_init_error or "Service unavailable"
    if msvc:
        try:
            msvc._create_bucket_if_not_exists()
            results["bucket"]["status"] = "success"
            results["bucket"][
                "message"
            ] = f"Bucket '{bucket_name}' initialized successfully"
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error or "Service unavailable"
    overall_status = (
        "success"
        if (
            results["collection"]["status"] == "success"
            and results["bucket"]["status"] == "success"
        )
        else (
            "partial"
            if (
                results["collection"]["status"] == "success"
                or results["bucket"]["status"] == "success"
            )
            else "error"
        )
    )
    return {"status": overall_status, "results": results}


def _delete_sync(svc: Optional["QdrantService"], msvc: Optional["MinioClient"]) -> dict:
    collection_name = _collection_name()
    bucket_name = _bucket_name()

    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc.service.delete_collection(collection_name=collection_name)
            results["collection"]["status"] = "success"
            results["collection"][
                "message"
            ] = f"Collection '{collection_name}' deleted successfully"
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
    if msvc:
        try:
            bucket_exists = msvc.service.bucket_exists(bucket_name)
            if bucket_exists:
                objects = msvc.list_object_names(recursive=True)
                if objects:
                    from minio.deleteobjects import DeleteObject

                    delete_objects = [DeleteObject(name) for name in objects]
                    errors = list(
                        msvc.service.remove_objects(
                            bucket_name,
                            delete_objects,
                        )
                    )
                    if errors:
                        results["bucket"]["status"] = "error"
                        results["bucket"][
                            "message"
                        ] = f"Failed to delete some objects: {len(errors)} errors"
                        return {"status": "error", "results": results}
                msvc.service.remove_bucket(bucket_name)
                results["bucket"]["status"] = "success"
                results["bucket"][
                    "message"
                ] = f"Bucket '{bucket_name}' deleted successfully"
            else:
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = "Bucket did not exist"
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error or "Service unavailable"
    overall_status = (
        "success"
        if (
            results["collection"]["status"] == "success"
            and results["bucket"]["status"] == "success"
        )
        else (
            "partial"
            if (
                results["collection"]["status"] == "success"
                or results["bucket"]["status"] == "success"
            )
            else "error"
        )
    )
    return {"status": overall_status, "results": results}
