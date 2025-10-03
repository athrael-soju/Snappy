from fastapi import APIRouter, HTTPException
from typing import Optional

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


@router.get("/status")
async def get_status():
    """Get the status of collection and bucket including statistics."""
    try:
        result = {
            "collection": {
                "name": config.QDRANT_COLLECTION_NAME,
                "exists": False,
                "vector_count": 0,
                "unique_files": 0,
                "error": None
            },
            "bucket": {
                "name": config.MINIO_BUCKET_NAME,
                "exists": False,
                "object_count": 0,
                "error": None
            }
        }
        
        # Check Qdrant collection status
        svc = get_qdrant_service()
        if svc:
            try:
                collection_info = svc.service.get_collection(config.QDRANT_COLLECTION_NAME)
                result["collection"]["exists"] = True
                result["collection"]["vector_count"] = collection_info.points_count or 0
                
                # Get unique file count by scrolling through payloads
                try:
                    scroll_result = svc.service.scroll(
                        collection_name=config.QDRANT_COLLECTION_NAME,
                        limit=10000,
                        with_payload=["filename"],
                        with_vectors=False
                    )
                    points = scroll_result[0] if scroll_result else []
                    unique_filenames = set()
                    for point in points:
                        if point.payload and "filename" in point.payload:
                            unique_filenames.add(point.payload["filename"])
                    result["collection"]["unique_files"] = len(unique_filenames)
                except Exception:
                    pass
                    
            except Exception as e:
                if "not found" not in str(e).lower():
                    result["collection"]["error"] = str(e)
        else:
            result["collection"]["error"] = qdrant_init_error or "Service unavailable"
        
        # Check MinIO bucket status
        msvc = get_minio_service()
        if msvc:
            try:
                bucket_exists = msvc.service.bucket_exists(config.MINIO_BUCKET_NAME)
                result["bucket"]["exists"] = bucket_exists
                
                if bucket_exists:
                    # Count objects in bucket
                    objects = list(msvc.service.list_objects(
                        config.MINIO_BUCKET_NAME,
                        recursive=True
                    ))
                    result["bucket"]["object_count"] = len(objects)
            except Exception as e:
                result["bucket"]["error"] = str(e)
        else:
            result["bucket"]["error"] = minio_init_error or "Service unavailable"
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize():
    """Initialize/create collection and bucket based on current configuration."""
    try:
        results = {
            "collection": {"status": "pending", "message": ""},
            "bucket": {"status": "pending", "message": ""}
        }
        
        # Initialize Qdrant collection
        svc = get_qdrant_service()
        if svc:
            try:
                svc._create_collection_if_not_exists()
                results["collection"]["status"] = "success"
                results["collection"]["message"] = f"Collection '{config.QDRANT_COLLECTION_NAME}' initialized successfully"
            except Exception as e:
                results["collection"]["status"] = "error"
                results["collection"]["message"] = str(e)
        else:
            results["collection"]["status"] = "error"
            results["collection"]["message"] = qdrant_init_error or "Service unavailable"
        
        # Initialize MinIO bucket
        msvc = get_minio_service()
        if msvc:
            try:
                msvc._create_bucket_if_not_exists()
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = f"Bucket '{config.MINIO_BUCKET_NAME}' initialized successfully"
            except Exception as e:
                results["bucket"]["status"] = "error"
                results["bucket"]["message"] = str(e)
        else:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = minio_init_error or "Service unavailable"
        
        # Determine overall status
        overall_status = "success" if (
            results["collection"]["status"] == "success" and 
            results["bucket"]["status"] == "success"
        ) else "partial" if (
            results["collection"]["status"] == "success" or 
            results["bucket"]["status"] == "success"
        ) else "error"
        
        return {
            "status": overall_status,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_collection_and_bucket():
    """Delete collection and bucket completely."""
    try:
        results = {
            "collection": {"status": "pending", "message": ""},
            "bucket": {"status": "pending", "message": ""}
        }
        
        # Delete Qdrant collection
        svc = get_qdrant_service()
        if svc:
            try:
                svc.service.delete_collection(collection_name=config.QDRANT_COLLECTION_NAME)
                results["collection"]["status"] = "success"
                results["collection"]["message"] = f"Collection '{config.QDRANT_COLLECTION_NAME}' deleted successfully"
            except Exception as e:
                if "not found" in str(e).lower():
                    results["collection"]["status"] = "success"
                    results["collection"]["message"] = "Collection did not exist"
                else:
                    results["collection"]["status"] = "error"
                    results["collection"]["message"] = str(e)
        else:
            results["collection"]["status"] = "error"
            results["collection"]["message"] = qdrant_init_error or "Service unavailable"
        
        # Delete MinIO bucket (remove all objects first)
        msvc = get_minio_service()
        if msvc:
            try:
                bucket_exists = msvc.service.bucket_exists(config.MINIO_BUCKET_NAME)
                if bucket_exists:
                    # Clear all objects first
                    objects = msvc.list_object_names(recursive=True)
                    if objects:
                        from minio.deleteobjects import DeleteObject
                        delete_objects = [DeleteObject(name) for name in objects]
                        errors = list(msvc.service.remove_objects(config.MINIO_BUCKET_NAME, delete_objects))
                        if errors:
                            results["bucket"]["status"] = "error"
                            results["bucket"]["message"] = f"Failed to delete some objects: {len(errors)} errors"
                            return {"status": "error", "results": results}
                    
                    # Remove bucket
                    msvc.service.remove_bucket(config.MINIO_BUCKET_NAME)
                    results["bucket"]["status"] = "success"
                    results["bucket"]["message"] = f"Bucket '{config.MINIO_BUCKET_NAME}' deleted successfully"
                else:
                    results["bucket"]["status"] = "success"
                    results["bucket"]["message"] = "Bucket did not exist"
            except Exception as e:
                results["bucket"]["status"] = "error"
                results["bucket"]["message"] = str(e)
        else:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = minio_init_error or "Service unavailable"
        
        # Determine overall status
        overall_status = "success" if (
            results["collection"]["status"] == "success" and 
            results["bucket"]["status"] == "success"
        ) else "partial" if (
            results["collection"]["status"] == "success" or 
            results["bucket"]["status"] == "success"
        ) else "error"
        
        return {
            "status": overall_status,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
