"""
Gotenberg converter for Office formats.
Converts PDF to DOCX, XLSX, PPTX, RTF, HTML via LibreOffice.
"""
import logging
from pathlib import Path

import httpx

from ...config import settings
from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)

# Gotenberg endpoint for LibreOffice conversions
LIBREOFFICE_CONVERT_URL = "/forms/libreoffice/convert"


class GotenbergConverter(BaseConverter):
    """
    Converts PDF to Office formats via Gotenberg Docker service.
    
    Gotenberg runs LibreOffice in headless mode and provides a REST API.
    Supports: DOCX, XLSX, PPTX, RTF, HTML
    
    Example:
        converter = GotenbergConverter()
        output_path = await converter.convert(
            input_path=Path("document.pdf"),
            output_path=Path("document.docx"),
        )
    """

    def __init__(self, base_url: str = None):
        """
        Initialize Gotenberg converter.
        
        Args:
            base_url: Gotenberg service URL (default from settings)
        """
        self.base_url = (base_url or settings.GOTENBERG_URL).rstrip("/")

    @property
    def supported_formats(self) -> list[str]:
        """Formats supported by Gotenberg (LibreOffice)."""
        return ["docx", "xlsx", "pptx", "rtf", "html"]

    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs,
    ) -> Path:
        """
        Convert PDF to Office format via Gotenberg.
        
        Args:
            input_path: Path to source PDF
            output_path: Desired output path (extension determines format)
            **kwargs: Optional parameters (e.g., page_ranges)
        
        Returns:
            Path to converted file
        
        Raises:
            ConversionError: If Gotenberg returns error or format not supported
        
        Example:
            result = await converter.convert(
                input_path=Path("input.pdf"),
                output_path=Path("output.docx"),
                page_ranges="1-3",  # Convert only pages 1-3
            )
        """
        target_format = output_path.suffix.lstrip(".")
        if target_format not in self.supported_formats:
            raise ConversionError(f"Gotenberg does not support format: {target_format}")

        url = f"{self.base_url}{LIBREOFFICE_CONVERT_URL}"
        logger.info(f"Converting via Gotenberg: {input_path.name} → {target_format}")

        async with httpx.AsyncClient(timeout=120) as client:
            with open(input_path, "rb") as f:
                response = await client.post(
                    url,
                    files={"files": (input_path.name, f, "application/pdf")},
                    data={"nativePageRanges": kwargs.get("page_ranges", "")},
                )

        if response.status_code != 200:
            raise ConversionError(
                f"Gotenberg returned {response.status_code}: {response.text[:300]}"
            )

        output_path.write_bytes(response.content)
        logger.info(f"Gotenberg conversion complete: {output_path.name} ({len(response.content)} bytes)")
        return output_path

    async def health_check(self) -> bool:
        """
        Check if Gotenberg service is available.
        
        Returns:
            True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False
