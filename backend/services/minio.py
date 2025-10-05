import io
import json
import uuid
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from typing import Iterable, Tuple, Dict, List, Optional
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error
from minio.deleteobjects import DeleteObject
from PIL import Image
import urllib3

from config import (
    MINIO_URL,
    MINIO_PUBLIC_URL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET_NAME,
    LOG_LEVEL,
    MINIO_WORKERS,
    MINIO_RETRIES,
    MINIO_FAIL_FAST,
    MINIO_PUBLIC_READ,
    MINIO_IMAGE_FMT,
    get_pipeline_max_concurrency,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class MinioService:
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
            max_pool_connections = max(50, MINIO_WORKERS * get_pipeline_max_concurrency() + 10)  # +10 for overhead
            http_client = urllib3.PoolManager(
                maxsize=max_pool_connections,
                cert_reqs='CERT_REQUIRED' if self.secure else 'CERT_NONE',
                timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
                retries=urllib3.Retry(
                    total=0,  # Retries handled by our logic
                    connect=None,
                    read=False,
                    redirect=False,
                )
            )

            self.service = Minio(
                self.endpoint,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=self.secure,
                http_client=http_client,
            )

            self.bucket_name = MINIO_BUCKET_NAME
            self._create_bucket_if_not_exists()
            logger.info(
                f"MinIO service initialized with bucket: {self.bucket_name}, "
                f"connection pool size: {max_pool_connections}"
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

    # -------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------
    def store_images_batch(
        self,
        images: Iterable[Image.Image],
        image_ids: Optional[List[str]] = None,
        fmt: str = MINIO_IMAGE_FMT,
        max_workers: int = MINIO_WORKERS,
        retries: int = MINIO_RETRIES,
        fail_fast: bool = MINIO_FAIL_FAST,
        **save_kwargs,
    ) -> Dict[str, str]:
        """
        Upload many images concurrently with retries.

        Parameters
        ----------
        images : Iterable[PIL.Image.Image]
        image_ids : Optional[List[str]]
            Provide IDs to align with images; UUIDs will be created if omitted.
        fmt : str
            Output format (PNG/JPEG/WEBP) applied to all images.
        max_workers : int
            Number of parallel upload threads.
        retries : int
            Retry attempts per object (total attempts = retries + 1).
        fail_fast : bool
            If True, raises at first failure; otherwise returns successes only.
        save_kwargs : dict
            Extra PIL save parameters (e.g., quality=90).

        Returns
        -------
        Dict[str, str]
            Mapping of image_id -> public URL for successfully uploaded items.
        """
        images = list(images)
        n = len(images)
        if image_ids is None:
            image_ids = [str(uuid.uuid4()) for _ in range(n)]
        if len(image_ids) != n:
            raise ValueError("Number of images must match number of image IDs")

        successes: Dict[str, str] = {}
        errors: Dict[str, Exception] = {}

        def upload_one(idx: int):
            img = images[idx]
            img_id = image_ids[idx]
            attempt = 0
            while True:
                attempt += 1
                try:
                    buf, size, used_fmt, content_type = self._encode_image_to_bytes(
                        img, fmt=fmt, **save_kwargs
                    )
                    object_name = f"images/{img_id}.{used_fmt.lower()}"
                    self.service.put_object(
                        bucket_name=self.bucket_name,
                        object_name=object_name,
                        data=buf,
                        length=size,
                        content_type=content_type,
                    )
                    return img_id, self._get_image_url(object_name)
                except Exception as e:
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

        errors = self.service.remove_objects(self.bucket_name, objects)
        failed = set()
        for err in errors:  # generator yields failures
            url = mapping.get(err.object_name, err.object_name)
            result[url] = f"error: {err}"
            failed.add(url)

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
        return f"{self._public_base_url}/{self.bucket_name}/{object_name}"

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
        try:
            objs = self.service.list_objects(
                self.bucket_name, prefix=prefix or None, recursive=recursive
            )
            return [o.object_name for o in objs]
        except Exception as e:
            raise Exception(f"Error listing objects with prefix='{prefix}': {e}") from e

    def clear_prefix(self, prefix: str = "") -> dict:
        """Delete all objects under the given prefix. Returns summary dict."""
        names = self.list_object_names(prefix=prefix, recursive=True)
        if not names:
            return {"deleted": 0, "failed": 0}

        objects = [DeleteObject(n) for n in names]
        errors = list(self.service.remove_objects(self.bucket_name, objects))
        failed = len(errors)
        deleted = max(0, len(names) - failed)

        if failed:
            for err in errors:
                logger.error(f"Failed to delete {err.object_name}: {err}")

        logger.info(
            f"Cleared prefix '{prefix}' in bucket '{self.bucket_name}': deleted={deleted}, failed={failed}"
        )
        return {"deleted": deleted, "failed": failed}

    def clear_images(self) -> dict:
        """Convenience helper: delete all stored images under 'images/'."""
        return self.clear_prefix("images/")
