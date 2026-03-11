"""General helper utilities."""
from pathlib import Path


def build_object_key(prefix: str, filename: str, identifier: str) -> str:
    """Build a MinIO object key: prefix/identifier/filename"""
    return f"{prefix}/{identifier}/{filename}"


def human_size(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
