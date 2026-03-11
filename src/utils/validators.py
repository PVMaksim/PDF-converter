"""Input validation utilities."""
import re
from uuid import UUID

SUPPORTED_FORMATS = {"docx", "xlsx", "pptx", "rtf", "html", "png", "jpeg", "jpg", "txt"}


def is_valid_format(fmt: str) -> bool:
    return fmt.lower() in SUPPORTED_FORMATS


def is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
