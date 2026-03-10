import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ConversionJob(Base):
    __tablename__ = "conversion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    source_format = Column(String(16), default="pdf", nullable=False)
    target_format = Column(String(16), nullable=False)  # docx / xlsx / png / ...

    source_file_id = Column(UUID(as_uuid=True), ForeignKey("file_records.id"), nullable=True)
    result_file_id = Column(UUID(as_uuid=True), ForeignKey("file_records.id"), nullable=True)

    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # TTL for result file

    # Relationships
    user = relationship("User", back_populates="conversion_jobs")
    source_file = relationship("FileRecord", foreign_keys=[source_file_id])
    result_file = relationship("FileRecord", foreign_keys=[result_file_id])
