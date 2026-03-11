"""
Storage service abstraction.
Supports MinIO (S3-compatible) with local filesystem fallback.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional
import shutil

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Abstraction over file storage.
    Uses MinIO (S3-compatible) in production, local filesystem in development.
    """

    def __init__(self):
        self.use_local = settings.USE_LOCAL_STORAGE
        
        if not self.use_local:
            # Инициализация MinIO клиента
            try:
                self._client = boto3.client(
                    "s3",
                    endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
                    aws_access_key_id=settings.MINIO_ACCESS_KEY,
                    aws_secret_access_key=settings.MINIO_SECRET_KEY,
                )
                self.bucket = settings.MINIO_BUCKET
                self._ensure_bucket()
                logger.info("Storage: MinIO initialized")
            except Exception as e:
                logger.warning(f"MinIO unavailable ({e}), falling back to local storage")
                self.use_local = True
        
        if self.use_local:
            # Создаём локальные директории
            self.upload_dir = Path(settings.UPLOAD_DIR)
            self.output_dir = Path(settings.OUTPUT_DIR)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Storage: Local filesystem initialized")

    def _ensure_bucket(self):
        """Create MinIO bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self.bucket)
            logger.info(f"Created MinIO bucket: {self.bucket}")

    def upload(self, file_path: Path, object_key: str) -> str:
        """
        Upload file to storage.
        
        Args:
            file_path: Path to file to upload
            object_key: Storage key (path in bucket or filename)
        
        Returns:
            Storage path (object_key)
        """
        if self.use_local:
            # Локальное хранилище
            dest = self.upload_dir / object_key.replace("/", "_")
            shutil.copy2(file_path, dest)
            logger.info(f"Uploaded {file_path.name} → {dest}")
        else:
            # MinIO
            self._client.upload_file(str(file_path), self.bucket, object_key)
            logger.info(f"Uploaded {file_path.name} → {object_key}")
        return object_key

    def download(self, object_key: str, dest_path: Path) -> Path:
        """
        Download file from storage to local path.
        
        Args:
            object_key: Storage key
            dest_path: Destination local path
        
        Returns:
            Path to downloaded file
        """
        if self.use_local:
            # Локальное хранилище
            src = self.upload_dir / object_key.replace("/", "_")
            if not src.exists():
                raise FileNotFoundError(f"File not found: {src}")
            shutil.copy2(src, dest_path)
        else:
            # MinIO
            self._client.download_file(self.bucket, object_key, str(dest_path))
        return dest_path

    def delete(self, object_key: str):
        """
        Delete file from storage.
        
        Args:
            object_key: Storage key to delete
        """
        if self.use_local:
            # Локальное хранилище
            local_path = self.upload_dir / object_key.replace("/", "_")
            if local_path.exists():
                local_path.unlink()
                logger.info(f"Deleted local file: {local_path}")
        else:
            # MinIO
            try:
                self._client.delete_object(Bucket=self.bucket, Key=object_key)
                logger.info(f"Deleted {object_key} from MinIO")
            except ClientError as e:
                logger.warning(f"Failed to delete {object_key}: {e}")

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned download URL (MinIO only).
        
        Args:
            object_key: Storage key
            expires_in: URL expiration time in seconds
        
        Returns:
            Presigned URL string
        
        Raises:
            NotImplementedError: If using local storage
        """
        if self.use_local:
            raise NotImplementedError("Presigned URLs not available for local storage")
        
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def exists(self, object_key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            object_key: Storage key
        
        Returns:
            True if file exists
        """
        if self.use_local:
            local_path = self.upload_dir / object_key.replace("/", "_")
            return local_path.exists()
        else:
            try:
                self._client.head_object(Bucket=self.bucket, Key=object_key)
                return True
            except ClientError:
                return False

    @staticmethod
    def sha256(file_path: Path) -> str:
        """
        Compute SHA-256 hash of a file (for deduplication).
        
        Args:
            file_path: Path to file
        
        Returns:
        SHA-256 hash as hex string
        """
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()


# Singleton instance
storage_service = StorageService()
