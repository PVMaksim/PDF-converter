import hashlib
import logging
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Abstraction over MinIO (S3-compatible) storage.
    Falls back to local filesystem in dev if MINIO_ENDPOINT is not reachable.
    """

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self.bucket)
            logger.info(f"Created MinIO bucket: {self.bucket}")

    def upload(self, file_path: Path, object_key: str) -> str:
        """Upload file to MinIO. Returns storage path (object_key)."""
        self._client.upload_file(str(file_path), self.bucket, object_key)
        logger.info(f"Uploaded {file_path.name} → {object_key}")
        return object_key

    def download(self, object_key: str, dest_path: Path) -> Path:
        """Download file from MinIO to local path."""
        self._client.download_file(self.bucket, object_key, str(dest_path))
        return dest_path

    def delete(self, object_key: str):
        """Delete object from MinIO."""
        self._client.delete_object(Bucket=self.bucket, Key=object_key)
        logger.info(f"Deleted {object_key} from MinIO")

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned download URL."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

    @staticmethod
    def sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of a file (for deduplication)."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()


storage_service = StorageService()
