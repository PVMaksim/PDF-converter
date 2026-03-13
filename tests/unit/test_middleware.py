"""Unit tests for middleware."""
import pytest
import io
from unittest.mock import patch
from fastapi import UploadFile, HTTPException

from src.middleware.file_validator import validate_upload


def create_upload_file(filename: str, content: bytes) -> UploadFile:
    """Helper to create UploadFile for testing."""
    file = io.BytesIO(content)
    file.seek(0)
    return UploadFile(filename=filename, file=file)


@pytest.mark.asyncio
async def test_validate_upload_pdf_success():
    """Test successful PDF file validation."""
    pdf_content = b'%PDF-1.4 fake pdf content'
    file = create_upload_file("test.pdf", pdf_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        result = await validate_upload(file, is_pro=False)
        
        assert result == pdf_content


@pytest.mark.asyncio
async def test_validate_upload_wrong_mime_type():
    """Test validation fails for non-PDF files."""
    txt_content = b'This is a text file'
    file = create_upload_file("test.txt", txt_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'text/plain'
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file, is_pro=False)
        
        assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_validate_upload_file_too_large():
    """Test validation fails for files exceeding size limit."""
    large_content = b'x' * (51 * 1024 * 1024)  # 51 MB
    file = create_upload_file("large.pdf", large_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file, is_pro=False)
        
        assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_upload_pro_user_higher_limit():
    """Test PRO users have higher file size limit."""
    large_content = b'x' * (100 * 1024 * 1024)  # 100 MB
    file = create_upload_file("large.pdf", large_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        # PRO пользователь должен пройти валидацию
        result = await validate_upload(file, is_pro=True)
        assert result == large_content
