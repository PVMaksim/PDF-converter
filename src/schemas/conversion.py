"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# =============================================================================
# File schemas
# =============================================================================

class FileUploadResponse(BaseModel):
    """Response for file upload endpoint."""
    file_id: str
    filename: str
    size_bytes: int
    duplicate: bool = False


class FileDownloadResponse(BaseModel):
    """Response for file download endpoint."""
    download_url: str
    filename: str
    expires_in: int = 3600


# =============================================================================
# Conversion schemas
# =============================================================================

class ConversionCreate(BaseModel):
    """Request to create a conversion job."""
    file_id: UUID = Field(..., description="UUID of uploaded source file")
    target_format: str = Field(..., min_length=3, max_length=10, description="Target format (docx, xlsx, png, etc.)")


class ConversionResponse(BaseModel):
    """Response with conversion job info."""
    job_id: str
    status: str
    target_format: str


class JobStatusResponse(BaseModel):
    """Response with detailed job status."""
    job_id: str
    status: str
    result_file_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# =============================================================================
# Auth schemas
# =============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    """User registration request."""
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., description="Email address")
    password: str


# =============================================================================
# Error schemas
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str


class RateLimitResponse(BaseModel):
    """Rate limit exceeded response."""
    detail: str
    retry_after: str
