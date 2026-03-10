import io
import logging
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)

DPI = 200  # dots per inch for rasterisation


class PyMuPDFConverter(BaseConverter):
    """
    Converts PDF → PNG / JPEG / TXT
    using PyMuPDF (fitz) and Pillow.
    """

    @property
    def supported_formats(self) -> list[str]:
        return ["png", "jpeg", "jpg", "txt"]

    async def convert(self, input_path: Path, output_path: Path, **kwargs) -> Path:
        fmt = output_path.suffix.lstrip(".").lower()

        if fmt == "txt":
            return await self._to_text(input_path, output_path)
        elif fmt in ("png", "jpeg", "jpg"):
            return await self._to_images(input_path, output_path, fmt, **kwargs)
        else:
            raise ConversionError(f"PyMuPDF converter does not support: {fmt}")

    async def _to_text(self, input_path: Path, output_path: Path) -> Path:
        doc = fitz.open(str(input_path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        full_text = "\n\n--- Page Break ---\n\n".join(text_parts)
        output_path.write_text(full_text, encoding="utf-8")
        logger.info(f"PDF→TXT done: {output_path.name}")
        return output_path

    async def _to_images(
        self,
        input_path: Path,
        output_path: Path,
        fmt: str,
        dpi: int = DPI,
        **kwargs,
    ) -> Path:
        doc = fitz.open(str(input_path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        if len(doc) == 1:
            # Single page → single file
            pix = doc[0].get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img.save(output_path, format=fmt.upper())
            doc.close()
            logger.info(f"PDF→{fmt.upper()} (1 page): {output_path.name}")
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

        logger.info(f"PDF→{fmt.upper()} ({len(doc)} pages zipped): {zip_path.name}")
        return zip_path
