import io
import json
import uuid
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from PIL import Image
import logging

from config import (
    MINIO_URL, 
    MINIO_ACCESS_KEY, 
    MINIO_SECRET_KEY, 
    MINIO_BUCKET_NAME,
    LOG_LEVEL
)

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

class MinioService:
    """Service for storing and retrieving images from MinIO object storage"""
    
    def __init__(self):
        """Initialize MinIO client and create bucket if it doesn't exist"""
        try:
            # Parse MinIO URL to get endpoint
            url_parts = MINIO_URL.replace("http://", "").replace("https://", "")
            self.endpoint = url_parts
            self.secure = MINIO_URL.startswith("https://")
            
            # Initialize MinIO client
            self.client = Minio(
                self.endpoint,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=self.secure
            )
            
            self.bucket_name = MINIO_BUCKET_NAME
            
            # Create bucket if it doesn't exist
            self._create_bucket_if_not_exists()
            
            logger.info(f"MinIO service initialized with bucket: {self.bucket_name}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize MinIO service: {e}")
    
    def _create_bucket_if_not_exists(self):
        """Create MinIO bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
            self.set_public_policy()
        except S3Error as e:
            raise Exception(f"Error creating bucket {self.bucket_name}: {e}")
    
    def store_image(self, image: Image.Image, image_id: str = None) -> str:
        """
        Store a PIL Image in MinIO and return the object URL
        
        Args:
            image: PIL Image object to store
            image_id: Optional custom ID for the image, generates UUID if not provided
            
        Returns:
            str: URL to access the stored image
        """
        if image_id is None:
            image_id = str(uuid.uuid4())
        
        try:
            # Convert PIL Image to bytes
            img_buffer = io.BytesIO()
            # Save as PNG to preserve quality
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Generate object name with PNG extension
            object_name = f"images/{image_id}.png"
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=img_buffer,
                length=len(img_buffer.getvalue()),
                content_type='image/png'
            )
            
            # Generate URL to access the image
            image_url = self._get_image_url(object_name)
            
            logger.info(f"Stored image {image_id} at {image_url}")
            return image_url
            
        except Exception as e:
            raise Exception(f"Error storing image {image_id}: {e}")
    
    def store_images_batch(self, images: list, image_ids: list = None) -> list:
        """
        Store a batch of images in MinIO
        
        Args:
            images: List of PIL Image objects
            image_ids: Optional list of custom IDs, generates UUIDs if not provided
            
        Returns:
            list: URLs to access the stored images
        """
        if image_ids is None:
            image_ids = [str(uuid.uuid4()) for _ in images]
        
        if len(images) != len(image_ids):
            raise ValueError("Number of images must match number of image IDs")
        
        urls = []
        for image, image_id in zip(images, image_ids):
            try:
                url = self.store_image(image, image_id)
                urls.append(url)
            except Exception as e:
                raise Exception(f"Failed to store image {image_id}: {e}")
        
        return urls
    
    def get_image(self, image_url: str) -> Image.Image:
        """
        Retrieve an image from MinIO by URL
        
        Args:
            image_url: URL of the image to retrieve
            
        Returns:
            PIL Image object
        """
        try:
            # Extract object name from URL
            object_name = self._extract_object_name_from_url(image_url)
            
            # Get object from MinIO
            response = self.client.get_object(self.bucket_name, object_name)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(response.read()))
            response.close()
            response.release_conn()
            
            return image
            
        except Exception as e:
            raise Exception(f"Error retrieving image from {image_url}: {e}")
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from MinIO
        
        Args:
            image_url: URL of the image to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            object_name = self._extract_object_name_from_url(image_url)
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted image: {image_url}")
            return True
        except Exception as e:
            raise Exception(f"Error deleting image {image_url}: {e}")
    
    def _get_image_url(self, object_name: str) -> str:
        """
        Generate URL for an object in MinIO
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            str: URL to access the object
        """
        # For simplicity, return a direct URL
        # In production, you might want to use presigned URLs for security
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket_name}/{object_name}"
    
    def _extract_object_name_from_url(self, image_url: str) -> str:
        """
        Extract object name from MinIO URL
        
        Args:
            image_url: Full URL to the image
            
        Returns:
            str: Object name/path within the bucket
        """
        # Remove protocol and endpoint, then remove bucket name
        url_parts = image_url.replace("http://", "").replace("https://", "")
        path_parts = url_parts.split("/", 1)
        if len(path_parts) > 1:
            # Remove endpoint part, then bucket name
            remaining_path = path_parts[1]
            bucket_and_object = remaining_path.split("/", 1)
            if len(bucket_and_object) > 1:
                return bucket_and_object[1]  # Return object path
        
        raise ValueError(f"Invalid MinIO URL format: {image_url}")
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL for secure access to an object
        
        Args:
            object_name: Name of the object in MinIO
            expires: Expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name, 
                object_name, 
                expires=timedelta(seconds=expires)
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating presigned URL for {object_name}: {e}")
    
    def health_check(self) -> bool:
        """
        Check if MinIO service is healthy and accessible
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            # Try to list buckets as a health check
            buckets = self.client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False

    def set_public_policy(self):
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
            self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
            logger.info(f"Public read policy set for bucket '{self.bucket_name}'.")
        except S3Error as e:
            raise Exception(f"Error setting public policy for bucket '{self.bucket_name}': {e}")