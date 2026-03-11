"""
ConversionJob model.
Tracks PDF conversion tasks and their status.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class JobStatus(str, enum.Enum):
    """Conversion job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ConversionJob(Base):
    """
    Conversion job model.
    
    Represents a single PDF conversion task from source format to target format.
    Status progresses: PENDING → PROCESSING → DONE/FAILED
    """
    __tablename__ = "conversion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Владелец задачи
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Статус и прогресс
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Форматы
    source_format = Column(String(16), default="pdf", nullable=False)
    target_format = Column(String(16), nullable=False)  # docx / xlsx / png / etc.
    
    # Связи с файлами
    source_file_id = Column(UUID(as_uuid=True), ForeignKey("file_records.id"), nullable=True)
    result_file_id = Column(UUID(as_uuid=True), ForeignKey("file_records.id"), nullable=True)
    
    # Ошибки
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # TTL для результирующего файла

    # Relationships
    user = relationship("User", back_populates="conversion_jobs")
    source_file = relationship("FileRecord", foreign_keys=[source_file_id])
    result_file = relationship("FileRecord", foreign_keys=[result_file_id])

    # Индексы для частых запросов
    __table_args__ = (
        Index('ix_jobs_user_status', 'user_id', 'status'),
        Index('ix_jobs_created', 'created_at', postgresql_using='brin'),
    )

    def __repr__(self) -> str:
        return f"<ConversionJob(id={self.id}, status={self.status.value})>"
