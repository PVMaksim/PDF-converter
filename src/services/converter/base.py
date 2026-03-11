"""
Base converter abstract class.
All PDF converters inherit from this base class.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseConverter(ABC):
    """
    Abstract base class for all PDF converters.
    
    Each converter implements conversion from PDF to a specific format
    or set of formats (e.g., PNG, DOCX, TXT).
    
    Example:
        class MyConverter(BaseConverter):
            async def convert(self, input_path, output_path, **kwargs):
                # Implementation here
                return output_path
    """

    @abstractmethod
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: dict,
    ) -> Path:
        """
        Convert input PDF to target format.
        
        Args:
            input_path: Path to source PDF file
            output_path: Desired output path (includes target extension)
            **kwargs: Format-specific options (e.g., dpi for images)
        
        Returns:
            Path to the resulting file (may differ from output_path for multi-page)
        
        Raises:
            ConversionError: If conversion fails
        
        Example:
            converter = GotenbergConverter()
            result_path = await converter.convert(
                input_path=Path("input.pdf"),
                output_path=Path("output.docx"),
            )
        """
        ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """
        List of file formats this converter can produce.
        
        Returns:
            List of format extensions without dot (e.g., ['docx', 'xlsx'])
        """
        ...


class ConversionError(Exception):
    """
    Raised when a PDF conversion fails.
    
    Attributes:
        message: Error message describing the failure
    """
    pass
