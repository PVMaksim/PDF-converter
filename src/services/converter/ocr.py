"""
OCR converter for scanned PDFs.
Extracts text from scanned documents using Tesseract.
"""
import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)

# Default OCR settings
DEFAULT_DPI = 300  # Higher DPI = better OCR accuracy
DEFAULT_LANG = "rus+eng"  # Bilingual OCR (Russian + English)


class OCRConverter(BaseConverter):
    """
    Converts scanned PDFs to text using Tesseract OCR.
    
    Each page is rasterized with PyMuPDF, then processed by Tesseract.
    Best for scanned documents without text layer.
    
    Example:
        converter = OCRConverter()
        result = await converter.convert(
            input_path=Path("scanned.pdf"),
            output_path=Path("output.txt"),
            lang="rus+eng",  # Russian and English
            dpi=300,  # High quality
        )
    
    Requirements:
        - Tesseract OCR installed on system
        - pytesseract Python package
        - Tesseract language packs (e.g., tesseract-ocr-rus)
    """

    @property
    def supported_formats(self) -> list[str]:
        """Formats supported by OCR converter (text only)."""
        return ["txt"]

    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        lang: str = DEFAULT_LANG,
        dpi: int = DEFAULT_DPI,
        **kwargs,
    ) -> Path:
        """
        Extract text from scanned PDF using OCR.
        
        Args:
            input_path: Path to source PDF
            output_path: Path for output text file
            lang: Tesseract language code (default: rus+eng)
            dpi: Resolution for rasterization (default: 300)
            **kwargs: Additional Tesseract options
        
        Returns:
            Path to text file with extracted text
        
        Raises:
            ConversionError: If Tesseract not available or OCR fails
        
        Example:
            text_path = await converter.convert(
                input_path=Path("scan.pdf"),
                output_path=Path("text.txt"),
                lang="eng",  # English only
                dpi=400,  # Higher quality for small text
            )
        """
        doc = fitz.open(str(input_path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pages_text = []

        for i, page in enumerate(doc):
            # Растеризуем страницу
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # Распознаём текст
            text = pytesseract.image_to_string(img, lang=lang)
            pages_text.append(text)
            
            logger.debug(f"OCR processed page {i + 1}/{len(doc)}")

        doc.close()

        full_text = "\n\n--- Page Break ---\n\n".join(pages_text)
        output_path.write_text(full_text, encoding="utf-8")
        logger.info(f"OCR complete: {output_path.name} ({len(pages_text)} pages)")
        return output_path

    @staticmethod
    def is_available() -> bool:
        """
        Check if Tesseract OCR is installed.
        
        Returns:
            True if Tesseract binary is available
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
