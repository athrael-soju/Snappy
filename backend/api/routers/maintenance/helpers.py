from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from api.dependencies import duckdb_init_error, minio_init_error, qdrant_init_error

try:  # pragma: no cover - tooling support
    import config  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from backend import config as config  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from services.duckdb import DuckDBService
    from services.minio import MinioService
    from services.qdrant import QdrantService


INACTIVE_MESSAGE = ""


def collection_name() -> str:
    return str(getattr(config, "QDRANT_COLLECTION_NAME", "documents"))


def bucket_name() -> str:
    return str(getattr(config, "MINIO_BUCKET_NAME", "documents"))


def collect_collection_status(svc: Optional["QdrantService"]) -> dict:
    embedded = bool(getattr(config, "QDRANT_EMBEDDED", False))
    status = {
        "name": collection_name(),
        "exists": False,
        "vector_count": 0,
        "unique_files": 0,
        "error": None,
        "embedded": embedded,
        "image_store_mode": "minio",
        "size_mb": 0.0,
    }
    if not svc:
        status["error"] = qdrant_init_error.get() or "Service unavailable"
        return status
    try:
        collection_info = svc.service.get_collection(collection_name())
        status["exists"] = True
        status["vector_count"] = collection_info.points_count or 0
        try:
            scroll_result = svc.service.scroll(
                collection_name=collection_name(),
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
            pass
        status["size_mb"] = estimate_qdrant_size_mb(collection_info)
    except Exception as exc:
        if "not found" in str(exc).lower():
            status["error"] = INACTIVE_MESSAGE
        else:
            status["error"] = str(exc)
    return status


def collect_bucket_status(msvc: Optional["MinioService"]) -> dict:
    status = {
        "name": bucket_name(),
        "exists": False,
        "object_count": 0,
        "page_count": 0,
        "element_count": 0,
        "size_mb": 0.0,
        "error": None,
    }
    if not msvc:
        status["error"] = minio_init_error.get() or "Service unavailable"
        return status
    try:
        bucket_exists = msvc.service.bucket_exists(bucket_name())
        status["exists"] = bucket_exists
        if bucket_exists:
            total_bytes = 0
            for obj in msvc.service.list_objects(bucket_name(), recursive=True):
                status["object_count"] += 1
                size = getattr(obj, "size", 0) or 0
                total_bytes += size
                object_name = getattr(obj, "object_name", "") or ""
                filename = object_name.rsplit("/", 1)[-1]
                if filename.startswith("page."):
                    status["page_count"] += 1
                elif filename == "elements.json":
                    status["element_count"] += 1
            status["size_mb"] = (
                round(total_bytes / (1024 * 1024), 2) if total_bytes else 0.0
            )
        else:
            status["error"] = INACTIVE_MESSAGE
    except Exception as exc:
        status["error"] = str(exc)
    return status


def collect_duckdb_status(dsvc: Optional["DuckDBService"]) -> dict:
    enabled = bool(getattr(config, "DUCKDB_ENABLED", False))
    status = {
        "name": getattr(config, "DUCKDB_DATABASE_NAME", "documents"),
        "enabled": enabled,
        "available": False,
        "page_count": 0,
        "region_count": 0,
        "database_size_mb": 0.0,
        "error": None,
    }

    if not enabled:
        status["error"] = "Disabled via configuration"
        return status

    if not dsvc:
        status["error"] = duckdb_init_error.get() or "Service unavailable"
        return status

    try:
        stats = dsvc.get_stats() or {}
        if not stats.get("schema_active", True):
            status["error"] = INACTIVE_MESSAGE
            return status

        status["available"] = True
        status["page_count"] = int(stats.get("total_pages", 0) or 0)
        status["region_count"] = int(stats.get("total_regions", 0) or 0)
        status["document_count"] = int(stats.get("total_documents", 0) or 0)
        status["database_size_mb"] = float(stats.get("storage_size_mb", 0) or 0)
    except Exception as exc:
        status["error"] = str(exc)

    return status


def estimate_qdrant_size_mb(collection_info: Any) -> float:
    try:
        point_count = int(collection_info.points_count or 0)
        total_dim = get_vector_total_dim(collection_info)
        if point_count <= 0 or total_dim <= 0:
            return 0.0
        approximate_bytes = point_count * total_dim * 4
        return round(approximate_bytes / (1024 * 1024), 2)
    except Exception:
        return 0.0


def get_vector_total_dim(collection_info: Any) -> int:
    try:
        params = collection_info.config.params
        vectors = getattr(params, "vectors", None)
    except AttributeError:
        return 0

    total = 0
    if isinstance(vectors, dict):
        for vec in vectors.values():
            size = getattr(vec, "size", None)
            if size:
                total += int(size)
    else:
        size = getattr(vectors, "size", None)
        if size:
            total += int(size)
    return total


def clear_all_sync(
    svc: Optional["QdrantService"],
    msvc: Optional["MinioService"],
    dsvc: Optional["DuckDBService"],
) -> dict:
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
        "duckdb": {"status": "pending", "message": ""},
    }

    if svc:
        if collection_exists(svc):
            try:
                svc.clear_collection()
                results["collection"]["status"] = "success"
                results["collection"]["message"] = "Cleared Qdrant collection"
            except Exception as exc:
                results["collection"]["status"] = "error"
                results["collection"]["message"] = str(exc)
        else:
            results["collection"]["status"] = "skipped"
            results["collection"]["message"] = "Collection missing; initialize first"
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = (
            qdrant_init_error.get() or "Qdrant service unavailable"
        )

    if msvc:
        if bucket_exists(msvc):
            try:
                msvc.clear_images()
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = "Cleared MinIO objects"
            except Exception as exc:
                results["bucket"]["status"] = "error"
                results["bucket"]["message"] = str(exc)
        else:
            results["bucket"]["status"] = "skipped"
            results["bucket"]["message"] = "Bucket missing; initialize first"
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = (
            minio_init_error.get() or "MinIO service unavailable"
        )

    if not getattr(config, "DUCKDB_ENABLED", False):
        results["duckdb"]["status"] = "skipped"
        results["duckdb"]["message"] = "DuckDB disabled via configuration"
    elif not dsvc:
        results["duckdb"]["status"] = "error"
        results["duckdb"]["message"] = duckdb_init_error.get() or "DuckDB unavailable"
    else:
        if duckdb_available(dsvc):
            try:
                dsvc.clear_storage()
                results["duckdb"]["status"] = "success"
                results["duckdb"]["message"] = "Cleared DuckDB tables"
            except Exception as exc:
                results["duckdb"]["status"] = "error"
                results["duckdb"]["message"] = str(exc)
        else:
            results["duckdb"]["status"] = "skipped"
            results["duckdb"]["message"] = "DuckDB missing; initialize first"

    return results


def initialize_sync(
    svc: Optional["QdrantService"],
    msvc: Optional["MinioService"],
    dsvc: Optional["DuckDBService"],
) -> dict:
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
        "duckdb": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc._create_collection_if_not_exists()
            results["collection"]["status"] = "success"
            results["collection"][
                "message"
            ] = f"Collection '{collection_name()}' initialized successfully"
        except Exception as exc:
            results["collection"]["status"] = "error"
            results["collection"]["message"] = str(exc)
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = (
            qdrant_init_error.get() or "Service unavailable"
        )
    if msvc:
        try:
            msvc._create_bucket_if_not_exists()
            results["bucket"]["status"] = "success"
            results["bucket"][
                "message"
            ] = f"Bucket '{bucket_name()}' initialized successfully"
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error.get() or "Service unavailable"
    if not getattr(config, "DUCKDB_ENABLED", False):
        results["duckdb"]["status"] = "skipped"
        results["duckdb"]["message"] = "DuckDB disabled via configuration"
    elif not dsvc:
        results["duckdb"]["status"] = "error"
        results["duckdb"]["message"] = duckdb_init_error.get() or "Service unavailable"
    else:
        try:
            res = dsvc.initialize_storage()
            results["duckdb"]["status"] = "success" if res else "error"
            results["duckdb"]["message"] = (
                str(res.get("message") or "") if isinstance(res, dict) else ""
            )
        except Exception as exc:
            results["duckdb"]["status"] = "error"
            results["duckdb"]["message"] = str(exc)

    overall_status = summarize_status(results)
    return {"status": overall_status, "results": results}


def delete_sync(
    svc: Optional["QdrantService"],
    msvc: Optional["MinioService"],
    dsvc: Optional["DuckDBService"],
) -> dict:
    results = {
        "collection": {"status": "pending", "message": ""},
        "bucket": {"status": "pending", "message": ""},
        "duckdb": {"status": "pending", "message": ""},
    }
    if svc:
        try:
            svc.service.delete_collection(collection_name=collection_name())
            results["collection"]["status"] = "success"
            results["collection"][
                "message"
            ] = f"Collection '{collection_name()}' deleted successfully"
        except Exception as exc:
            if "not found" in str(exc).lower():
                results["collection"]["status"] = "success"
                results["collection"]["message"] = "Collection did not exist"
            else:
                results["collection"]["status"] = "error"
                results["collection"]["message"] = str(exc)
    else:
        results["collection"]["status"] = "error"
        results["collection"]["message"] = (
            qdrant_init_error.get() or "Service unavailable"
        )
    if msvc:
        try:
            bucket_exists = msvc.service.bucket_exists(bucket_name())
            if bucket_exists:
                objects = msvc.list_object_names(recursive=True)
                if objects:
                    from minio.deleteobjects import DeleteObject

                    delete_objects = [DeleteObject(name) for name in objects]
                    errors = list(
                        msvc.service.remove_objects(
                            bucket_name(),
                            delete_objects,
                        )
                    )
                    if errors:
                        results["bucket"]["status"] = "error"
                        results["bucket"][
                            "message"
                        ] = f"Failed to delete some objects: {len(errors)} errors"
                        return {"status": "error", "results": results}
                msvc.service.remove_bucket(bucket_name())
                results["bucket"]["status"] = "success"
                results["bucket"][
                    "message"
                ] = f"Bucket '{bucket_name()}' deleted successfully"
            else:
                results["bucket"]["status"] = "success"
                results["bucket"]["message"] = "Bucket did not exist"
        except Exception as exc:
            results["bucket"]["status"] = "error"
            results["bucket"]["message"] = str(exc)
    else:
        results["bucket"]["status"] = "error"
        results["bucket"]["message"] = minio_init_error.get() or "Service unavailable"
    if not getattr(config, "DUCKDB_ENABLED", False):
        results["duckdb"]["status"] = "skipped"
        results["duckdb"]["message"] = "DuckDB disabled via configuration"
    elif not dsvc:
        results["duckdb"]["status"] = "error"
        results["duckdb"]["message"] = duckdb_init_error.get() or "Service unavailable"
    else:
        try:
            res = dsvc.delete_storage()
            results["duckdb"]["status"] = "success" if res else "error"
            results["duckdb"]["message"] = (
                str(res.get("message") or "") if isinstance(res, dict) else ""
            )
        except Exception as exc:
            results["duckdb"]["status"] = "error"
            results["duckdb"]["message"] = str(exc)

    overall_status = summarize_status(results)
    return {"status": overall_status, "results": results}


def summarize_status(results: dict) -> str:
    statuses = [entry.get("status") for entry in results.values()]
    success_like = {"success", "skipped"}

    if all(status in success_like for status in statuses):
        return "success"
    if any(status == "success" for status in statuses):
        return "partial"
    return "error"


def collection_exists(svc: "QdrantService") -> bool:
    try:
        svc.service.get_collection(collection_name())
        return True
    except Exception as exc:
        return "not found" not in str(exc).lower()


def bucket_exists(msvc: "MinioService") -> bool:
    try:
        return bool(msvc.service.bucket_exists(bucket_name()))
    except Exception:
        return False


def duckdb_available(dsvc: "DuckDBService") -> bool:
    try:
        stats = dsvc.get_stats()
        return bool(stats)
    except Exception:
        return False


__all__ = [
    "INACTIVE_MESSAGE",
    "bucket_name",
    "bucket_exists",
    "clear_all_sync",
    "collect_bucket_status",
    "collect_collection_status",
    "collect_duckdb_status",
    "collection_exists",
    "delete_sync",
    "duckdb_available",
    "estimate_qdrant_size_mb",
    "get_vector_total_dim",
    "initialize_sync",
    "summarize_status",
]
