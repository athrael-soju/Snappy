from __future__ import annotations

import asyncio
import logging

from api.dependencies import (
    get_duckdb_service,
    get_minio_service,
    get_qdrant_service,
    minio_init_error,
    qdrant_init_error,
)
from fastapi import APIRouter, HTTPException
from utils.timing import PerformanceTimer

from domain.maintenance import (
    clear_all_sync,
    delete_sync,
    initialize_sync,
    summarize_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["maintenance"])


@router.post("/clear/qdrant")
async def clear_qdrant():
    logger.warning(
        "DESTRUCTIVE: Clearing Qdrant collection",
        extra={"operation": "clear_qdrant", "service": "qdrant"},
    )

    try:
        svc = get_qdrant_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {qdrant_init_error.get() or 'Dependency services are down'}",
            )

        with PerformanceTimer("clear Qdrant collection", log_on_exit=False) as timer:
            msg = await asyncio.to_thread(svc.clear_collection)

        logger.warning(
            "Qdrant collection cleared",
            extra={
                "operation": "clear_qdrant",
                "result": msg,
                "duration_ms": timer.duration_ms,
            },
        )

        return {"status": "ok", "message": msg}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to clear Qdrant collection",
            exc_info=exc,
            extra={"operation": "clear_qdrant"},
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clear/minio")
async def clear_minio():
    logger.warning(
        "DESTRUCTIVE: Clearing MinIO storage",
        extra={"operation": "clear_minio", "service": "minio"},
    )

    try:
        msvc = get_minio_service()
        if not msvc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {minio_init_error.get() or 'Dependency services are down'}",
            )

        with PerformanceTimer("clear MinIO storage", log_on_exit=False) as timer:
            res = await asyncio.to_thread(msvc.clear_images)

        logger.warning(
            "MinIO storage cleared",
            extra={
                "operation": "clear_minio",
                "deleted": res.get("deleted"),
                "failed": res.get("failed"),
                "duration_ms": timer.duration_ms,
            },
        )

        return {
            "status": "ok",
            "deleted": res.get("deleted"),
            "failed": res.get("failed"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to clear MinIO storage",
            exc_info=exc,
            extra={"operation": "clear_minio"},
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clear/all")
async def clear_all():
    logger.warning(
        "DESTRUCTIVE: Clearing ALL data (Qdrant, MinIO, DuckDB)",
        extra={"operation": "clear_all"},
    )

    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()

        with PerformanceTimer("clear all data", log_on_exit=False) as timer:
            results = await asyncio.to_thread(clear_all_sync, svc, msvc, dsvc)

        status = summarize_status(results)

        logger.warning(
            "All data cleared",
            extra={
                "operation": "clear_all",
                "status": status,
                "results": results,
                "duration_ms": timer.duration_ms,
            },
        )

        return {"status": status, "results": results}
    except Exception as exc:
        logger.error(
            "Failed to clear all data", exc_info=exc, extra={"operation": "clear_all"}
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/initialize")
async def initialize():
    logger.info("Initializing services", extra={"operation": "initialize"})

    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()

        with PerformanceTimer("initialize services", log_on_exit=False) as timer:
            result = await asyncio.to_thread(initialize_sync, svc, msvc, dsvc)

        logger.info(
            "Services initialized",
            extra={
                "operation": "initialize",
                "result": result,
                "duration_ms": timer.duration_ms,
            },
        )

        return result
    except Exception as exc:
        logger.error(
            "Failed to initialize services",
            exc_info=exc,
            extra={"operation": "initialize"},
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/delete")
async def delete_collection_and_bucket():
    logger.critical(
        "DESTRUCTIVE: Deleting collection and bucket (PERMANENT)",
        extra={"operation": "delete_all", "warning": "PERMANENT_DELETION"},
    )

    try:
        svc = get_qdrant_service()
        msvc = get_minio_service()
        dsvc = get_duckdb_service()

        with PerformanceTimer("delete all", log_on_exit=False) as timer:
            result = await asyncio.to_thread(delete_sync, svc, msvc, dsvc)

        logger.critical(
            "Collection and bucket deleted (PERMANENT)",
            extra={
                "operation": "delete_all",
                "result": result,
                "duration_ms": timer.duration_ms,
            },
        )

        return result
    except Exception as exc:
        logger.error(
            "Failed to delete collection and bucket",
            exc_info=exc,
            extra={"operation": "delete_all"},
        )
        raise HTTPException(status_code=500, detail=str(exc))
