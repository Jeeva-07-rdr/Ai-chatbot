"""Word document services."""
from pdfapp.views_legacy import compress_docx
from .conversion import safe_docx_to_pdf, safe_word_to_powerpoint
from .editor import prepare_editor_html_from_docx, docx_to_editor_html, post_process_docx_layout

__all__ = [
    "compress_docx",
    "safe_docx_to_pdf",
    "safe_word_to_powerpoint",
    "prepare_editor_html_from_docx",
    "docx_to_editor_html",
    "post_process_docx_layout",
]
