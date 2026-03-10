"""Unit tests for converters."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.services.converter import get_converter, ConversionError


def test_get_converter_gotenberg():
    from app.services.converter.gotenberg import GotenbergConverter
    assert isinstance(get_converter("docx"), GotenbergConverter)
    assert isinstance(get_converter("xlsx"), GotenbergConverter)
    assert isinstance(get_converter("pptx"), GotenbergConverter)


def test_get_converter_pymupdf():
    from app.services.converter.pymupdf import PyMuPDFConverter
    assert isinstance(get_converter("png"), PyMuPDFConverter)
    assert isinstance(get_converter("txt"), PyMuPDFConverter)


def test_get_converter_unknown():
    with pytest.raises(ConversionError):
        get_converter("bmp")
