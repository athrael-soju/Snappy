from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from api.dependencies import qdrant_init_error

try:  # pragma: no cover - tooling support
    import config  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from backend import config as config  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from clients.qdrant import QdrantClient


INACTIVE_MESSAGE = ""


def collection_name() -> str:
    return str(getattr(config, "QDRANT_COLLECTION_NAME", "documents"))


def collect_collection_status(svc: Optional["QdrantClient"]) -> dict:
    """Collect status for Qdrant collection."""
    embedded = bool(getattr(config, "QDRANT_EMBEDDED", False))
    status = {
        "name": collection_name(),
        "exists": False,
        "vector_count": 0,
        "unique_files": 0,
        "error": None,
        "embedded": embedded,
        "image_store_mode": "inline",
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


def clear_all_sync(svc: Optional["QdrantClient"]) -> dict:
    """Clear all data from Qdrant collection."""
    results = {
        "collection": {"status": "pending", "message": ""},
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

    return results


def initialize_sync(svc: Optional["QdrantClient"]) -> dict:
    """Initialize Qdrant collection."""
    results = {
        "collection": {"status": "pending", "message": ""},
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

    overall_status = summarize_status(results)
    return {"status": overall_status, "results": results}


def delete_sync(svc: Optional["QdrantClient"]) -> dict:
    """Delete Qdrant collection."""
    results = {
        "collection": {"status": "pending", "message": ""},
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


def collection_exists(svc: "QdrantClient") -> bool:
    try:
        svc.service.get_collection(collection_name())
        return True
    except Exception as exc:
        return "not found" not in str(exc).lower()
