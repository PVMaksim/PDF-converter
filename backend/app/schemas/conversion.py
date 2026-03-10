from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConversionCreate(BaseModel):
    """Schema for creating a conversion job"""
    output_format: str = Field(..., min_length=3, max_length=10)
    start_page: Optional[int] = Field(None, ge=0)
    end_page: Optional[int] = Field(None, ge=0)


class ConversionResponse(BaseModel):
    """Schema for conversion job response"""
    id: int
    user_id: int
    input_filename: str
    output_filename: Optional[str]
    input_format: str
    output_format: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConversionStatus(BaseModel):
    """Schema for job status check"""
    job_id: int
    status: str
    progress: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None