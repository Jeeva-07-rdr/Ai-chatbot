"""PowerPoint document services."""
from pdfapp.views_legacy import compress_powerpoint
from .conversion import (
    safe_powerpoint_to_pdf,
    safe_powerpoint_to_word,
    safe_pdf_to_powerpoint,
    safe_word_to_powerpoint,
)

__all__ = [
    "compress_powerpoint",
    "safe_powerpoint_to_pdf",
    "safe_powerpoint_to_word",
    "safe_pdf_to_powerpoint",
    "safe_word_to_powerpoint",
]
