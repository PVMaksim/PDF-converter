"""
User model.
Represents a user of the PDF Converter service.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, BigInteger, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class UserPlan(str, enum.Enum):
    """User subscription plan."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    """
    User model for authentication and rate limiting.
    
    Users can be identified by either Telegram ID (tg_id) or email.
    Telegram users have tg_id set, web users have email set.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Идентификаторы
    tg_id = Column(BigInteger, unique=True, nullable=True, index=True)   # null для веб-пользователей
    email = Column(String(255), unique=True, nullable=True, index=True)  # null для Telegram-пользователей
    
    # Аутентификация (только для веб-пользователей)
    hashed_password = Column(String, nullable=True)
    
    # Подписка и лимиты
    plan = Column(SQLEnum(UserPlan), default=UserPlan.FREE, nullable=False)
    daily_limit = Column(Integer, default=10, nullable=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    conversion_jobs = relationship(
        "ConversionJob",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, plan={self.plan.value})>"
