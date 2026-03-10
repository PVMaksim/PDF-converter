import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, BigInteger, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class UserPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tg_id = Column(BigInteger, unique=True, nullable=True, index=True)   # null for web users
    email = Column(String(255), unique=True, nullable=True, index=True)  # null for TG users
    hashed_password = Column(String, nullable=True)                      # only for web users
    plan = Column(SQLEnum(UserPlan), default=UserPlan.FREE, nullable=False)
    daily_limit = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversion_jobs = relationship("ConversionJob", back_populates="user", lazy="select")
