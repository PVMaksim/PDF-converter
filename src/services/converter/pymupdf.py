"""
PyMuPDF converter for images and text.
Converts PDF to PNG, JPEG, TXT using PyMuPDF (fitz).
"""
import io
import logging
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)

# Default DPI for rasterization (higher = better quality, larger files)
DEFAULT_DPI = 200


class PyMuPDFConverter(BaseConverter):
    """
    Converts PDF to images (PNG, JPEG) or text using PyMuPDF.
    
    For images: renders each page at specified DPI.
    For text: extracts text content from all pages.
    
    Example:
        converter = PyMuPDFConverter()
        # Convert to PNG images
        result = await converter.convert(
            input_path=Path("document.pdf"),
            output_path=Path("output.png"),
            dpi=300,  # High quality
        )
    """

    @property
    def supported_formats(self) -> list[str]:
        """Formats supported by PyMuPDF converter."""
        return ["png", "jpeg", "jpg", "txt"]

    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs,
    ) -> Path:
        """
        Convert PDF to image(s) or text.
        
        Args:
            input_path: Path to source PDF
            output_path: Desired output path
            **kwargs: Format-specific options:
                - dpi: Dots per inch for images (default: 200)
        
        Returns:
            Path to result file (or ZIP for multi-page images)
        
        Raises:
            ConversionError: If format not supported or conversion fails
        """
        fmt = output_path.suffix.lstrip(".").lower()

        if fmt == "txt":
            return await self._to_text(input_path, output_path)
        elif fmt in ("png", "jpeg", "jpg"):
            dpi = kwargs.get("dpi", DEFAULT_DPI)
            return await self._to_images(input_path, output_path, fmt, dpi)
        else:
            raise ConversionError(f"PyMuPDF converter does not support: {fmt}")

    async def _to_text(self, input_path: Path, output_path: Path) -> Path:
        """
        Extract text from PDF.
        
        Args:
            input_path: Path to source PDF
            output_path: Path for output text file
        
        Returns:
            Path to text file
        """
        doc = fitz.open(str(input_path))
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        doc.close()

        full_text = "\n\n--- Page Break ---\n\n".join(text_parts)
        output_path.write_text(full_text, encoding="utf-8")
        logger.info(f"Text extraction complete: {output_path.name}")
        return output_path

    async def _to_images(
        self,
        input_path: Path,
        output_path: Path,
        fmt: str,
        dpi: int = DEFAULT_DPI,
    ) -> Path:
        """
        Convert PDF pages to images.
        
        Single page → single image file.
        Multiple pages → ZIP archive with images.
        
        Args:
            input_path: Path to source PDF
            output_path: Base output path (extension used for format)
            fmt: Image format (png, jpeg, jpg)
            dpi: Resolution in dots per inch
        
        Returns:
            Path to image file or ZIP archive
        """
        doc = fitz.open(str(input_path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        if len(doc) == 1:
            # Single page → single file
            pix = doc[0].get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img.save(output_path, format=fmt.upper())
            doc.close()
            logger.info(f"Image conversion complete: {output_path.name} (1 page)")
            return output_path

        # Multiple pages → ZIP archive
        zip_path = output_path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=mat)
                img_bytes = io.BytesIO()
                Image.open(io.BytesIO(pix.tobytes("png"))).save(img_bytes, format=fmt.upper())
                zf.writestr(f"page_{i + 1:03d}.{fmt}", img_bytes.getvalue())
        
        doc.close()
        logger.info(f"Image conversion complete: {zip_path.name} ({len(doc)} pages)")
        return zip_path
