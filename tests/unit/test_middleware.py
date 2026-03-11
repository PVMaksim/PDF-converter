"""Unit tests for middleware."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile, HTTPException

from src.middleware.file_validator import validate_upload, ALLOWED_MIME_TYPES


@pytest.mark.asyncio
async def test_validate_upload_pdf_success():
    """Test successful PDF file validation."""
    # Создаём mock PDF файла
    pdf_content = b'%PDF-1.4 fake pdf content'
    
    file = UploadFile(
        filename="test.pdf",
        file=MagicMock(read=AsyncMock(return_value=pdf_content)),
    )
    file.read = AsyncMock(return_value=pdf_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        result = await validate_upload(file, is_pro=False)
        
        assert result == pdf_content


@pytest.mark.asyncio
async def test_validate_upload_wrong_mime_type():
    """Test validation fails for non-PDF files."""
    # Создаём mock не-PDF файла
    txt_content = b'This is a text file'
    
    file = UploadFile(filename="test.txt")
    file.read = AsyncMock(return_value=txt_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'text/plain'
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file, is_pro=False)
        
        assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_validate_upload_file_too_large():
    """Test validation fails for files exceeding size limit."""
    # Создаём большой файл (больше 50 МБ)
    large_content = b'x' * (51 * 1024 * 1024)  # 51 MB
    
    file = UploadFile(filename="large.pdf")
    file.read = AsyncMock(return_value=large_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload(file, is_pro=False)
        
        assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_upload_pro_user_higher_limit():
    """Test PRO users have higher file size limit."""
    # Создаём файл 100 МБ (больше free лимита, меньше pro)
    large_content = b'x' * (100 * 1024 * 1024)  # 100 MB
    
    file = UploadFile(filename="large.pdf")
    file.read = AsyncMock(return_value=large_content)
    
    with patch('src.middleware.file_validator.magic.from_buffer') as mock_magic:
        mock_magic.return_value = 'application/pdf'
        
        # PRO пользователь должен пройти валидацию
        result = await validate_upload(file, is_pro=True)
        assert result == large_content


from unittest.mock import patch
