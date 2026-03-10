import io
import logging
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)


class OCRConverter(BaseConverter):
    """
    Converts scanned PDFs → TXT using Tesseract OCR.
    Each page is rasterised with PyMuPDF then passed to pytesseract.
    """

    @property
    def supported_formats(self) -> list[str]:
        return ["txt"]

    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        lang: str = "rus+eng",
        dpi: int = 300,
        **kwargs,
    ) -> Path:
        doc = fitz.open(str(input_path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pages_text = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang=lang)
            pages_text.append(text)
            logger.debug(f"OCR page {i + 1}/{len(doc)}")

        doc.close()

        full_text = "\n\n--- Page Break ---\n\n".join(pages_text)
        output_path.write_text(full_text, encoding="utf-8")
        logger.info(f"OCR done: {output_path.name} ({len(pages_text)} pages)")
        return output_path

    @staticmethod
    def is_available() -> bool:
        """Check if Tesseract binary is installed."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
