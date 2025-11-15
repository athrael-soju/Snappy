import io
import json
import logging
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import urllib3
from config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET_NAME,
    MINIO_FAIL_FAST,
    MINIO_PUBLIC_READ,
    MINIO_PUBLIC_URL,
    MINIO_RETRIES,
    MINIO_SECRET_KEY,
    MINIO_URL,
    MINIO_WORKERS,
    get_pipeline_max_concurrency,
)
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
from PIL import Image
from utils.timing import log_execution_time

if TYPE_CHECKING:
    from domain.pipeline.image_processor import ProcessedImage

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class MinioClient:
    """Service for storing and retrieving images from MinIO object storage.

    Improvements vs. the basic version:
      - Threaded batch uploads with retries and exponential backoff
      - No extra memory copy when computing content length
      - Optional output format (PNG/JPEG/WEBP)
      - Batch delete via `remove_objects`
      - More robust URL parsing and public URL generation (supports path prefixes)
    """

    # -------------------------------------------------------------------
    # Initialization & Bucket Setup
    # -------------------------------------------------------------------
    def __init__(self):
        """Initialize MinIO client and create bucket if it doesn't exist."""
        try:
            parsed = urlparse(MINIO_URL)
            # MinIO client expects just host[:port], no scheme/path
            endpoint = parsed.netloc or parsed.path.split("/")[0]
            if not endpoint:
                raise ValueError(f"Invalid MINIO_URL: {MINIO_URL}")

            self.endpoint = endpoint
            self.secure = parsed.scheme == "https"

            # Public base URL can differ from SDK endpoint (e.g., localhost vs container name)
            public_parsed = urlparse(MINIO_PUBLIC_URL)
            public_base_path = public_parsed.path.rstrip("/")
            self._public_base_url = (
                f"{public_parsed.scheme}://{public_parsed.netloc}{public_base_path}"
                if public_parsed.scheme and public_parsed.netloc
                else f"http://{endpoint}"
            )

            # Configure HTTP connection pool to handle high concurrency
            # Pool size scales with ingestion concurrency (workers * pipeline batches)
            # When concurrency grows, bump connections to avoid saturation
            max_pool_connections = max(
                50, MINIO_WORKERS * get_pipeline_max_concurrency() + 10
            )  # +10 for overhead
            http_client = urllib3.PoolManager(
                maxsize=max_pool_connections,
                cert_reqs="CERT_REQUIRED" if self.secure else "CERT_NONE",
                timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
                retries=urllib3.Retry(
                    total=0,  # Retries handled by our logic
                    connect=None,
                    read=False,
                    redirect=False,
                ),
            )

            self.service = Minio(
                self.endpoint,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=self.secure,
                http_client=http_client,
            )

            self.bucket_name = MINIO_BUCKET_NAME
            logger.info(
                f"MinIO service initialized for bucket '{self.bucket_name}' "
                f"(creation deferred to maintenance). Connection pool size: {max_pool_connections}"
            )

        except Exception as e:
            raise Exception(f"Failed to initialize MinIO service: {e}") from e

    def _create_bucket_if_not_exists(self) -> None:
        """Create MinIO bucket if it doesn't exist and set public read policy."""
        try:
            if not self.service.bucket_exists(self.bucket_name):
                self.service.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
            if MINIO_PUBLIC_READ:
                self.set_public_policy()
            else:
                logger.info(
                    "Skipping public read policy per MINIO_PUBLIC_READ env setting."
                )
        except S3Error as e:
            raise Exception(f"Error creating bucket {self.bucket_name}: {e}") from e

    def _require_bucket(self) -> None:
        """Ensure the configured bucket exists before performing writes."""
        if not self.service.bucket_exists(self.bucket_name):
            raise RuntimeError(
                f"MinIO bucket '{self.bucket_name}' does not exist. "
                "Use the Maintenance → Initialize action to create it."
            )

    # -------------------------------------------------------------------
    # Encoding Helpers
    # -------------------------------------------------------------------
    def _encode_image_to_bytes(
        self,
        image: Image.Image,
        fmt: str = "PNG",
        **save_kwargs,
    ) -> Tuple[io.BytesIO, int, str, str]:
        """
        Encode a PIL image to bytes efficiently.

        Returns
        -------
        (buffer, size, used_format, content_type)
        """
        buf = io.BytesIO()
        image.save(buf, format=fmt, **save_kwargs)
        size = buf.tell()  # avoids copying like .getvalue()
        buf.seek(0)
        used_fmt = (fmt or "PNG").upper()
        content_type = {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "WEBP": "image/webp",
        }.get(used_fmt, "application/octet-stream")
        return buf, size, used_fmt, content_type

    def get_image(self, image_url: str) -> Image.Image:
        """
        Retrieve an image from MinIO by its public URL and return a PIL Image.
        """
        try:
            object_name = self._extract_object_name_from_url(image_url)
            response = self.service.get_object(self.bucket_name, object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
            return Image.open(io.BytesIO(data))
        except Exception as e:
            raise Exception(f"Error retrieving image from {image_url}: {e}") from e

    def get_json(self, json_url: str) -> Dict[str, Any]:
        """
        Retrieve a JSON file from MinIO by its public URL and return the parsed data.
        """
        try:
            object_name = self._extract_object_name_from_url(json_url)
            response = self.service.get_object(self.bucket_name, object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            raise Exception(f"Error retrieving JSON from {json_url}: {e}") from e

    # -------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------
    @log_execution_time(
        "upload images to MinIO", log_level=logging.INFO, warn_threshold_ms=3000
    )
    def store_processed_images_batch(
        self,
        processed_images: List["ProcessedImage"],
        image_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        page_numbers: Optional[List[int]] = None,
        max_workers: int = MINIO_WORKERS,
        retries: int = MINIO_RETRIES,
        fail_fast: bool = MINIO_FAIL_FAST,
    ) -> Dict[str, str]:
        """
        Upload many pre-processed images concurrently with retries.

        This method accepts images that have already been processed (format conversion
        and quality optimization applied), avoiding redundant conversions.

        Parameters
        ----------
        processed_images : List[ProcessedImage]
            Pre-processed images with encoded data
        image_ids : Optional[List[str]]
            Provide IDs to align with images; UUIDs will be created if omitted.
        document_ids : Optional[List[str]]
            Document UUIDs for organizing storage (required for new structure).
        page_numbers : Optional[List[int]]
            Page numbers within each document (required for new structure).
        max_workers : int
            Number of parallel upload threads.
        retries : int
            Retry attempts per object (total attempts = retries + 1).
        fail_fast : bool
            If True, raises at first failure; otherwise returns successes only.

        Returns
        -------
        Dict[str, str]
            Mapping of image_id -> public URL for successfully uploaded items.
        """
        self._require_bucket()
        n = len(processed_images)
        if image_ids is None:
            image_ids = [str(uuid.uuid4()) for _ in range(n)]
        if len(image_ids) != n:
            raise ValueError(
                "Number of processed images must match number of image IDs"
            )

        # Require document_ids and page_numbers
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
                    # Use pre-processed data directly
                    buf = processed.to_buffer()
                    size = processed.size
                    used_fmt = processed.format
                    content_type = processed.content_type

                    # Storage structure: {doc_uuid}/{page_num}/image/{uuid}.{ext}
                    ext = used_fmt.lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    object_name = f"{doc_id}/{page_num}/image/{img_id}.{ext}"

                    self.service.put_object(
                        bucket_name=self.bucket_name,
                        object_name=object_name,
                        data=buf,
                        length=size,
                        content_type=content_type,
                    )
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
        Persist a JSON payload to MinIO and return its public URL.

        Parameters
        ----------
        payload : Dict[str, Any]
            JSON-serialisable dictionary to store.
        page_number : int
            Page number for hierarchical structure (required).
        document_id : str
            Document UUID for organizing storage (required).
        json_filename : str
            Filename for the JSON file (default: "data.json").
        content_type : str
            MIME type for the stored object. Defaults to ``application/json; charset=utf-8``.
        """
        self._require_bucket()
        # Require document_id and page_number
        if document_id is None:
            raise ValueError("document_id is required for storing JSON")
        if page_number is None:
            raise ValueError("page_number is required for storing JSON")

        # Storage structure: {doc_uuid}/{page_num}/{json_filename}
        final_object_name = f"{document_id}/{page_number}/{json_filename}"

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        stream = io.BytesIO(data)
        length = len(data)
        try:
            self.service.put_object(
                bucket_name=self.bucket_name,
                object_name=final_object_name,
                data=stream,
                length=length,
                content_type=content_type,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            raise Exception(
                f"Failed to store JSON payload at {final_object_name}: {exc}"
            ) from exc

        return self._get_image_url(final_object_name)

    def delete_images_batch(self, image_urls: List[str]) -> Dict[str, str]:
        """
        Delete many images using MinIO's streaming batch delete.

        Returns
        -------
        Dict[str, str]
            {url: 'deleted' | 'error: <msg>'}
        """
        result: Dict[str, str] = {u: "pending" for u in image_urls}
        objects: List[DeleteObject] = []
        mapping: Dict[str, str] = {}

        for u in image_urls:
            try:
                obj = self._extract_object_name_from_url(u)
                objects.append(DeleteObject(obj))
                mapping[obj] = u
            except Exception as e:
                result[u] = f"error: {e}"

        if not objects:
            return result

        errors_iter: Iterable[Any] = self.service.remove_objects(
            self.bucket_name, objects
        )
        failed: set[str] = set()
        for err in errors_iter:  # generator yields failures
            object_name = getattr(err, "object_name", None)
            mapped_url = (
                mapping.get(object_name) if isinstance(object_name, str) else None
            )
            key = mapped_url or (
                str(object_name) if object_name is not None else str(err)
            )
            result[key] = f"error: {err}"
            failed.add(key)

        for u in list(result.keys()):
            if result[u] == "pending" and u not in failed:
                result[u] = "deleted"
        return result

    # -------------------------------------------------------------------
    # URL Helpers & Health
    # -------------------------------------------------------------------
    def _get_image_url(self, object_name: str) -> str:
        """
        Generate a public URL for the given object name.

        This uses the original MINIO_URL's scheme/host and preserves any path
        prefix (e.g., if you're serving MinIO behind a reverse proxy at /minio).
        """
        base = self._public_base_url.rstrip("/")
        bucket_suffix = f"/{self.bucket_name}"
        if base.endswith(bucket_suffix):
            return f"{base}/{object_name}"
        return f"{base}{bucket_suffix}/{object_name}"

    def _extract_object_name_from_url(self, image_url: str) -> str:
        """
        Extract object name from a public MinIO URL.

        Supports URLs with optional path prefixes, e.g.:
        https://host[:port]/prefix/bucket/objects/... -> objects/...
        """
        parsed = urlparse(image_url)
        path = parsed.path.strip("/")  # e.g., 'prefix/bucket/objects/x.png'
        parts = path.split("/", 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid MinIO URL format (no bucket): {image_url}")

        # If there's a path prefix, the first item might be a prefix; find bucket
        # Search for the bucket_name in the path components and take the remainder
        components = path.split("/")
        try:
            b_idx = components.index(self.bucket_name)
        except ValueError:
            raise ValueError(
                f"URL does not contain expected bucket '{self.bucket_name}': {image_url}"
            )
        if b_idx == len(components) - 1:
            raise ValueError(f"Invalid MinIO URL format (no object): {image_url}")
        object_name = "/".join(components[b_idx + 1 :])
        return object_name

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """Generate a presigned URL for secure access to an object."""
        try:
            url = self.service.presigned_get_object(
                self.bucket_name, object_name, expires=timedelta(seconds=expires)
            )
            return url
        except Exception as e:
            raise Exception(
                f"Error generating presigned URL for {object_name}: {e}"
            ) from e

    def health_check(self) -> bool:
        """Check if MinIO service is healthy and accessible."""
        try:
            _ = self.service.list_buckets()
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False

    def set_public_policy(self) -> None:
        """Sets a public read-only policy on the bucket."""
        try:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"],
                    },
                ],
            }
            self.service.set_bucket_policy(self.bucket_name, json.dumps(policy))
            logger.info(f"Public read policy set for bucket '{self.bucket_name}'.")
        except S3Error as e:
            raise Exception(
                f"Error setting public policy for bucket '{self.bucket_name}': {e}"
            ) from e

    # -------------------------------------------------------------------
    # Bulk Maintenance Helpers
    # -------------------------------------------------------------------
    def list_object_names(self, prefix: str = "", recursive: bool = True) -> List[str]:
        """List object names in the bucket under an optional prefix."""
        if not self.service.bucket_exists(self.bucket_name):
            return []
        try:
            objs = self.service.list_objects(
                self.bucket_name, prefix=prefix or None, recursive=recursive
            )
            names: List[str] = []
            for obj in objs:
                object_name = getattr(obj, "object_name", None)
                if isinstance(object_name, str):
                    names.append(object_name)
            return names
        except Exception as e:
            raise Exception(f"Error listing objects with prefix='{prefix}': {e}") from e

    def clear_prefix(self, prefix: str = "") -> dict:
        """Delete all objects under the given prefix. Returns summary dict."""
        names = self.list_object_names(prefix=prefix, recursive=True)
        if not names:
            return {"deleted": 0, "failed": 0}

        objects = [DeleteObject(n) for n in names]
        errors_iter: Iterable[Any] = self.service.remove_objects(
            self.bucket_name, objects
        )
        errors = list(errors_iter)
        failed = len(errors)
        deleted = max(0, len(names) - failed)

        if failed:
            for err in errors:
                object_name = getattr(err, "object_name", "<unknown>")
                logger.error(f"Failed to delete {object_name}: {err}")

        logger.info(
            f"Cleared prefix '{prefix}' in bucket '{self.bucket_name}': deleted={deleted}, failed={failed}"
        )
        return {"deleted": deleted, "failed": failed}

    def clear_images(self) -> dict:
        """Convenience helper: delete all stored content in the bucket.

        Clears the entire bucket (hierarchical document/page structure).
        """
        # Clear all content in bucket
        result = self.clear_prefix("")
        return result
