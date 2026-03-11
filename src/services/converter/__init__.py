"""
Converter services for PDF transformation.
Supports multiple output formats via different engines.
"""
from .base import BaseConverter, ConversionError
from .gotenberg import GotenbergConverter
from .pymupdf import PyMuPDFConverter
from .ocr import OCRConverter

# Format → converter mapping
GOTENBERG_FORMATS = {"docx", "xlsx", "pptx", "rtf", "html"}
PYMUPDF_FORMATS = {"png", "jpeg", "jpg", "txt"}
OCR_FORMATS = {"txt"}  # Используется только для сканированных PDF


def get_converter(target_format: str, use_ocr: bool = False) -> BaseConverter:
    """
    Get appropriate converter for target format.
    
    Args:
        target_format: Output format (docx, png, txt, etc.)
        use_ocr: If True, use OCR converter for text extraction
    
    Returns:
        Converter instance for the specified format
    
    Raises:
        ConversionError: If no converter available for format
    
    Example:
        converter = get_converter("docx")
        await converter.convert(input_path, output_path)
    """
    fmt = target_format.lower()
    
    if use_ocr and fmt in OCR_FORMATS:
        return OCRConverter()
    if fmt in GOTENBERG_FORMATS:
        return GotenbergConverter()
    if fmt in PYMUPDF_FORMATS:
        return PyMuPDFConverter()
    
    raise ConversionError(f"No converter available for format: {fmt}")


__all__ = [
    "BaseConverter",
    "ConversionError",
    "GotenbergConverter",
    "PyMuPDFConverter",
    "OCRConverter",
    "get_converter",
    "GOTENBERG_FORMATS",
    "PYMUPDF_FORMATS",
    "OCR_FORMATS",
]
