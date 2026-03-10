from .base import BaseConverter, ConversionError
from .gotenberg import GotenbergConverter
from .pymupdf import PyMuPDFConverter
from .ocr import OCRConverter

# Format → converter mapping (used by Celery task)
GOTENBERG_FORMATS = {"docx", "xlsx", "pptx", "rtf", "html"}
PYMUPDF_FORMATS = {"png", "jpeg", "jpg", "txt"}
OCR_FORMATS = {"txt"}   # used only when PDF is a scan


def get_converter(target_format: str, use_ocr: bool = False) -> BaseConverter:
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
]
