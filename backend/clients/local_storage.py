"""
Local filesystem storage client for storing and retrieving images and JSON files.

This is a drop-in replacement for MinioClient that uses the local filesystem
instead of S3-compatible object storage. Files are served via a FastAPI endpoint.
"""

import io
import json
import logging
import os
import random
import shutil
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Optional, Protocol, Tuple
from urllib.parse import urlparse

from config import (
    LOCAL_STORAGE_BUCKET_NAME,
    LOCAL_STORAGE_PATH,
    LOCAL_STORAGE_PUBLIC_URL,
    STORAGE_FAIL_FAST,
    STORAGE_RETRIES,
    STORAGE_WORKERS,
    get_pipeline_max_concurrency,
)
from PIL import Image
from utils.timing import log_execution_time


class ImageContainer(Protocol):
    """Protocol for image containers to avoid circular dependencies."""
    size: int
    format: str
    content_type: str
    def to_buffer(self) -> io.BytesIO: ...


logger = logging.getLogger(__name__)


class _ObjectInfo:
    """Mimics MinIO object info for compatibility with maintenance.py."""
    def __init__(self, object_name: str, size: int):
        self.object_name = object_name
        self.size = size


class _ServiceShim:
    """
    Compatibility shim that mimics MinIO service methods for maintenance.py.

    maintenance.py directly accesses msvc.service.bucket_exists(), list_objects(), etc.
    This shim provides those methods using filesystem operations.
    """

    def __init__(self, storage_path: Path, bucket_name: str):
        self._storage_path = storage_path
        self._bucket_name = bucket_name

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if the bucket (directory) exists."""
        bucket_path = self._storage_path / bucket_name
        return bucket_path.exists() and bucket_path.is_dir()

    def make_bucket(self, bucket_name: str) -> None:
        """Create the bucket (directory)."""
        bucket_path = self._storage_path / bucket_name
        bucket_path.mkdir(parents=True, exist_ok=True)

    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        recursive: bool = True
    ) -> Iterator[_ObjectInfo]:
        """List objects in the bucket, yielding ObjectInfo-like objects."""
        bucket_path = self._storage_path / bucket_name
        if not bucket_path.exists():
            return

        if recursive:
            for file_path in bucket_path.rglob("*"):
                if file_path.is_file():
                    # Get relative path from bucket as object name
                    object_name = str(file_path.relative_to(bucket_path))
                    if prefix is None or object_name.startswith(prefix):
                        size = file_path.stat().st_size
                        yield _ObjectInfo(object_name, size)
        else:
            search_path = bucket_path / prefix if prefix else bucket_path
            if search_path.exists():
                for file_path in search_path.iterdir():
                    if file_path.is_file():
                        object_name = str(file_path.relative_to(bucket_path))
                        size = file_path.stat().st_size
                        yield _ObjectInfo(object_name, size)

    def remove_objects(
        self,
        bucket_name: str,
        delete_objects: List[Any]
    ) -> Iterator[Any]:
        """Remove objects from the bucket. Yields errors for failed deletions."""
        bucket_path = self._storage_path / bucket_name
        for delete_obj in delete_objects:
            object_name = getattr(delete_obj, "name", str(delete_obj))
            file_path = bucket_path / object_name
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                # Yield error info similar to MinIO
                class DeleteError:
                    def __init__(self, name: str, error: str):
                        self.object_name = name
                        self.error = error
                yield DeleteError(object_name, str(e))

    def remove_bucket(self, bucket_name: str) -> None:
        """Remove the bucket (directory) and all its contents."""
        bucket_path = self._storage_path / bucket_name
        if bucket_path.exists():
            shutil.rmtree(bucket_path)

    def list_buckets(self) -> List[str]:
        """List all buckets (directories) in storage path."""
        if not self._storage_path.exists():
            return []
        return [d.name for d in self._storage_path.iterdir() if d.is_dir()]


class LocalStorageClient:
    """Service for storing and retrieving files from local filesystem.

    This is a drop-in replacement for MinioClient with identical interface.
    Files are stored on the local filesystem and served via a FastAPI endpoint.
    """

    def __init__(self):
        """Initialize local storage client."""
        try:
            self.storage_path = Path(LOCAL_STORAGE_PATH)
            self.bucket_name = LOCAL_STORAGE_BUCKET_NAME

            # Parse public URL for generating file URLs
            self._public_base_url = LOCAL_STORAGE_PUBLIC_URL.rstrip("/")

            # Create the service shim for maintenance.py compatibility
            self.service = _ServiceShim(self.storage_path, self.bucket_name)

            logger.info(
                f"Local storage initialized at '{self.storage_path}' "
                f"for bucket '{self.bucket_name}'. "
                f"Public URL: {self._public_base_url}"
            )
        except Exception as e:
            raise Exception(f"Failed to initialize local storage: {e}") from e

    def _create_bucket_if_not_exists(self) -> None:
        """Create storage directory if it doesn't exist."""
        try:
            bucket_path = self.storage_path / self.bucket_name
            bucket_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {bucket_path}")
        except Exception as e:
            raise Exception(f"Error creating storage directory: {e}") from e

    def _require_bucket(self) -> None:
        """Ensure the storage directory exists before performing writes."""
        bucket_path = self.storage_path / self.bucket_name
        if not bucket_path.exists():
            raise RuntimeError(
                f"Storage directory '{bucket_path}' does not exist. "
                "Use the Maintenance → Initialize action to create it."
            )

    def _object_name_to_path(self, object_name: str) -> Path:
        """Convert object name to filesystem path."""
        return self.storage_path / self.bucket_name / object_name

    def _get_image_url(self, object_name: str) -> str:
        """Generate a public URL for the given object name."""
        base = self._public_base_url.rstrip("/")
        return f"{base}/{self.bucket_name}/{object_name}"

    def _extract_object_name_from_url(self, url: str) -> str:
        """Extract object name from a public URL."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        # Find the bucket name in the path and take the remainder
        components = path.split("/")
        try:
            # Skip 'files' prefix if present
            if components[0] == "files":
                components = components[1:]
            b_idx = components.index(self.bucket_name)
        except ValueError:
            raise ValueError(
                f"URL does not contain expected bucket '{self.bucket_name}': {url}"
            )

        if b_idx == len(components) - 1:
            raise ValueError(f"Invalid URL format (no object): {url}")

        object_name = "/".join(components[b_idx + 1:])
        return object_name

    def get_image(self, image_url: str) -> Image.Image:
        """Retrieve an image from storage by its public URL."""
        try:
            object_name = self._extract_object_name_from_url(image_url)
            file_path = self._object_name_to_path(object_name)

            if not file_path.exists():
                raise FileNotFoundError(f"Image not found: {file_path}")

            return Image.open(file_path)
        except Exception as e:
            raise Exception(f"Error retrieving image from {image_url}: {e}") from e

    def get_json(self, json_url: str) -> Dict[str, Any]:
        """Retrieve a JSON file from storage by its public URL."""
        try:
            object_name = self._extract_object_name_from_url(json_url)
            file_path = self._object_name_to_path(object_name)

            if not file_path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error retrieving JSON from {json_url}: {e}") from e

    @log_execution_time(
        "upload images to local storage", log_level=logging.DEBUG, warn_threshold_ms=3000
    )
    def store_processed_images_batch(
        self,
        processed_images: List[ImageContainer],
        image_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        page_numbers: Optional[List[int]] = None,
        max_workers: int = STORAGE_WORKERS,
        retries: int = STORAGE_RETRIES,
        fail_fast: bool = STORAGE_FAIL_FAST,
    ) -> Dict[str, str]:
        """
        Upload many pre-processed images concurrently with retries.

        Parameters
        ----------
        processed_images : List[ImageContainer]
            Pre-processed images with encoded data
        image_ids : Optional[List[str]]
            IDs for images; UUIDs created if omitted.
        document_ids : Optional[List[str]]
            Document UUIDs for organizing storage (required).
        page_numbers : Optional[List[int]]
            Page numbers within each document (required).
        max_workers : int
            Number of parallel upload threads.
        retries : int
            Retry attempts per object.
        fail_fast : bool
            If True, raises at first failure.

        Returns
        -------
        Dict[str, str]
            Mapping of image_id -> public URL.
        """
        self._require_bucket()
        n = len(processed_images)
        if image_ids is None:
            image_ids = [str(uuid.uuid4()) for _ in range(n)]
        if len(image_ids) != n:
            raise ValueError("Number of processed images must match number of image IDs")

        if document_ids is None or len(document_ids) != n:
            raise ValueError("document_ids is required and must match number of images")
        if page_numbers is None or len(page_numbers) != n:
            raise ValueError("page_numbers is required and must match number of images")

        successes: Dict[str, str] = {}
        errors: Dict[str, Exception] = {}

        def upload_one(idx: int):
            processed = processed_images[idx]
            img_id = image_ids[idx]
            doc_id = document_ids[idx]
            page_num = page_numbers[idx]

            attempt = 0
            while True:
                attempt += 1
                try:
                    buf = processed.to_buffer()
                    used_fmt = processed.format

                    # Storage structure: {doc_uuid}/{page_num}/image/{uuid}.{ext}
                    ext = used_fmt.lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    object_name = f"{doc_id}/{page_num}/image/{img_id}.{ext}"

                    file_path = self._object_name_to_path(object_name)
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write atomically using temp file
                    with tempfile.NamedTemporaryFile(
                        dir=file_path.parent, delete=False, suffix=f".{ext}"
                    ) as tmp:
                        tmp.write(buf.getvalue())
                        temp_path = tmp.name

                    # Atomic rename
                    os.replace(temp_path, file_path)

                    return img_id, self._get_image_url(object_name)
                except Exception:
                    if attempt > retries + 1:
                        raise
                    # Exponential backoff with jitter
                    sleep_s = (0.25 * (2 ** (attempt - 1))) + random.random() * 0.1
                    time.sleep(sleep_s)

        max_workers_eff = max(1, min(max_workers, n))
        with ThreadPoolExecutor(max_workers=max_workers_eff) as ex:
            future_to_idx = {ex.submit(upload_one, i): i for i in range(n)}
            for fut in as_completed(future_to_idx):
                i = future_to_idx[fut]
                img_id = image_ids[i]
                try:
                    _id, url = fut.result()
                    successes[_id] = url
                except Exception as e:
                    errors[img_id] = e
                    logger.exception(f"Failed to store image {img_id}: {e}")
                    if fail_fast:
                        for f in future_to_idx:
                            f.cancel()
                        raise Exception(f"Batch failed on {img_id}: {e}") from e

        if errors:
            logger.warning(f"{len(errors)} images failed to upload")
        return successes

    def store_json(
        self,
        payload: Dict[str, Any],
        *,
        page_number: Optional[int] = None,
        document_id: Optional[str] = None,
        json_filename: str = "data.json",
        content_type: str = "application/json; charset=utf-8",
    ) -> str:
        """
        Persist a JSON payload to storage and return its public URL.

        Parameters
        ----------
        payload : Dict[str, Any]
            JSON-serializable dictionary to store.
        page_number : int
            Page number for hierarchical structure (required).
        document_id : str
            Document UUID for organizing storage (required).
        json_filename : str
            Filename for the JSON file.
        content_type : str
            MIME type (unused, kept for interface compatibility).
        """
        self._require_bucket()
        if document_id is None:
            raise ValueError("document_id is required for storing JSON")
        if page_number is None:
            raise ValueError("page_number is required for storing JSON")

        # Storage structure: {doc_uuid}/{page_num}/{json_filename}
        object_name = f"{document_id}/{page_number}/{json_filename}"
        file_path = self._object_name_to_path(object_name)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically using temp file
            data = json.dumps(payload, ensure_ascii=False)
            with tempfile.NamedTemporaryFile(
                dir=file_path.parent, delete=False, mode="w",
                encoding="utf-8", suffix=".json"
            ) as tmp:
                tmp.write(data)
                temp_path = tmp.name

            os.replace(temp_path, file_path)
        except Exception as e:
            raise Exception(f"Failed to store JSON at {object_name}: {e}") from e

        return self._get_image_url(object_name)

    def delete_images_batch(self, image_urls: List[str]) -> Dict[str, str]:
        """
        Delete many files.

        Returns
        -------
        Dict[str, str]
            {url: 'deleted' | 'error: <msg>'}
        """
        result: Dict[str, str] = {u: "pending" for u in image_urls}

        for url in image_urls:
            try:
                object_name = self._extract_object_name_from_url(url)
                file_path = self._object_name_to_path(object_name)

                if file_path.exists():
                    file_path.unlink()
                result[url] = "deleted"
            except Exception as e:
                result[url] = f"error: {e}"

        return result

    def list_object_names(self, prefix: str = "", recursive: bool = True) -> List[str]:
        """List object names under an optional prefix."""
        bucket_path = self.storage_path / self.bucket_name
        if not bucket_path.exists():
            return []

        names: List[str] = []
        try:
            if recursive:
                for file_path in bucket_path.rglob("*"):
                    if file_path.is_file():
                        object_name = str(file_path.relative_to(bucket_path))
                        if not prefix or object_name.startswith(prefix):
                            names.append(object_name)
            else:
                search_path = bucket_path / prefix if prefix else bucket_path
                if search_path.exists():
                    for file_path in search_path.iterdir():
                        if file_path.is_file():
                            names.append(str(file_path.relative_to(bucket_path)))
        except Exception as e:
            raise Exception(f"Error listing objects with prefix='{prefix}': {e}") from e

        return names

    def clear_prefix(self, prefix: str = "") -> dict:
        """Delete all objects under the given prefix."""
        names = self.list_object_names(prefix=prefix, recursive=True)
        if not names:
            return {"deleted": 0, "failed": 0}

        deleted = 0
        failed = 0
        bucket_path = self.storage_path / self.bucket_name

        for name in names:
            file_path = bucket_path / name
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete {name}: {e}")
                failed += 1

        # Clean up empty directories
        self._cleanup_empty_dirs(bucket_path / prefix if prefix else bucket_path)

        logger.info(
            f"Cleared prefix '{prefix}' in bucket '{self.bucket_name}': "
            f"deleted={deleted}, failed={failed}"
        )
        return {"deleted": deleted, "failed": failed}

    def _cleanup_empty_dirs(self, path: Path) -> None:
        """Remove empty directories recursively up to bucket root."""
        bucket_path = self.storage_path / self.bucket_name
        try:
            for dirpath in sorted(path.rglob("*"), reverse=True):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    dirpath.rmdir()
        except Exception:
            pass  # Ignore cleanup errors

    def clear_images(self) -> dict:
        """Delete all stored content in the bucket."""
        return self.clear_prefix("")

    def health_check(self) -> bool:
        """Check if storage is healthy and accessible."""
        try:
            # Verify we can write to the storage directory
            test_path = self.storage_path / ".health_check"
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text("ok")
            test_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Local storage health check failed: {e}")
            return False

    def set_public_policy(self) -> None:
        """No-op for local storage (files are served via FastAPI endpoint)."""
        logger.info(
            f"Local storage bucket '{self.bucket_name}' - "
            "files are served publicly via /files endpoint"
        )

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """Generate URL for accessing an object (no expiry for local storage)."""
        return self._get_image_url(object_name)
