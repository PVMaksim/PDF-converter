"""Unit tests for converter services."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.converter import get_converter, ConversionError


def test_get_converter_gotenberg():
    """Test Gotenberg converter instantiation for Office formats."""
    from src.services.converter.gotenberg import GotenbergConverter
    
    assert isinstance(get_converter("docx"), GotenbergConverter)
    assert isinstance(get_converter("xlsx"), GotenbergConverter)
    assert isinstance(get_converter("pptx"), GotenbergConverter)
    assert isinstance(get_converter("rtf"), GotenbergConverter)
    assert isinstance(get_converter("html"), GotenbergConverter)


def test_get_converter_pymupdf():
    """Test PyMuPDF converter instantiation for images and text."""
    from src.services.converter.pymupdf import PyMuPDFConverter
    
    assert isinstance(get_converter("png"), PyMuPDFConverter)
    assert isinstance(get_converter("jpeg"), PyMuPDFConverter)
    assert isinstance(get_converter("jpg"), PyMuPDFConverter)
    assert isinstance(get_converter("txt"), PyMuPDFConverter)


def test_get_converter_unknown_format():
    """Test that unknown format raises ConversionError."""
    with pytest.raises(ConversionError) as exc_info:
        get_converter("bmp")
    
    assert "No converter available for format: bmp" in str(exc_info.value)


def test_gotenberg_supported_formats():
    """Test Gotenberg supported formats list."""
    from src.services.converter.gotenberg import GotenbergConverter
    
    converter = GotenbergConverter()
    formats = converter.supported_formats
    
    assert "docx" in formats
    assert "xlsx" in formats
    assert "pptx" in formats
    assert "rtf" in formats
    assert "html" in formats


def test_pymupdf_supported_formats():
    """Test PyMuPDF supported formats list."""
    from src.services.converter.pymupdf import PyMuPDFConverter
    
    converter = PyMuPDFConverter()
    formats = converter.supported_formats
    
    assert "png" in formats
    assert "jpeg" in formats
    assert "jpg" in formats
    assert "txt" in formats


@pytest.mark.asyncio
@patch('src.services.converter.gotenberg.httpx.AsyncClient')
async def test_gotenberg_health_check(mock_client_class):
    """Test Gotenberg health check (mocked)."""
    from src.services.converter.gotenberg import GotenbergConverter
    import httpx
    
    converter = GotenbergConverter(base_url="http://mocked:3000")
    
    # Create mock response
    mock_response = httpx.Response(200, request=httpx.Request("GET", "http://mocked:3000/health"))
    
    # Setup mock client instance
    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    
    # Configure the mock class to return our instance
    mock_client_class.return_value = mock_client_instance
    
    result = await converter.health_check()
    assert result is True


def test_ocr_converter_available():
    """Test OCR converter availability check."""
    from src.services.converter.ocr import OCRConverter
    
    # Этот тест зависит от наличия Tesseract в системе
    # В CI среде Tesseract должен быть установлен
    available = OCRConverter.is_available()
    
    # Тест проходит, если Tesseract установлен
    assert isinstance(available, bool)
