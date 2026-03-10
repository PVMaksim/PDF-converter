import logging
from pathlib import Path

import httpx

from ...config import settings
from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)

# Gotenberg endpoints for LibreOffice conversions
LIBREOFFICE_CONVERT_URL = "/forms/libreoffice/convert"


class GotenbergConverter(BaseConverter):
    """
    Converts PDF → DOCX / XLSX / PPTX / RTF / HTML
    via Gotenberg Docker service (LibreOffice headless).

    Docs: https://gotenberg.dev/docs/routes#libreoffice-route
    """

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or settings.GOTENBERG_URL).rstrip("/")

    @property
    def supported_formats(self) -> list[str]:
        return ["docx", "xlsx", "pptx", "rtf", "html"]

    async def convert(self, input_path: Path, output_path: Path, **kwargs) -> Path:
        target_format = output_path.suffix.lstrip(".")
        if target_format not in self.supported_formats:
            raise ConversionError(f"Gotenberg does not support format: {target_format}")

        url = f"{self.base_url}{LIBREOFFICE_CONVERT_URL}"
        logger.info(f"Gotenberg convert: {input_path.name} → {target_format}")

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
        logger.info(f"Gotenberg done: {output_path.name} ({len(response.content)} bytes)")
        return output_path

    async def health_check(self) -> bool:
        """Ping Gotenberg /health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False
