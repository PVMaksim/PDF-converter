from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseConverter(ABC):
    """Abstract base class for all PDF converters."""

    @abstractmethod
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs,
    ) -> Path:
        """
        Convert input file to target format.

        Args:
            input_path: Path to source PDF
            output_path: Desired output path
            **kwargs: Format-specific options

        Returns:
            Path to the resulting file

        Raises:
            ConversionError: on failure
        """
        ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Formats this converter can produce."""
        ...


class ConversionError(Exception):
    """Raised when a conversion fails."""
    pass
