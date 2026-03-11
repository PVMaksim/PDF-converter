"""
FileRecord model.
Tracks uploaded and generated files in storage.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class FileRecord(Base):
    """
    File metadata record.
    
    Stores information about uploaded source files and generated result files.
    Files are automatically deleted after expires_at via Celery beat task.
    """
    __tablename__ = "file_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Информация о файле
    storage_path = Column(String, nullable=False, index=True)  # путь в MinIO или локальной ФС
    original_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    
    # Дедупликация
    sha256_hash = Column(String(64), nullable=True, index=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # автоудаление через Celery beat

    def __repr__(self) -> str:
        return f"<FileRecord(id={self.id}, name={self.original_name})>"
