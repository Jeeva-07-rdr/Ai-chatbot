"""Excel document services."""
from pdfapp.views_legacy import compress_excel
from .conversion import safe_excel_to_pdf, merge_excel_files, split_excel_file

__all__ = [
    "compress_excel",
    "safe_excel_to_pdf",
    "merge_excel_files",
    "split_excel_file",
]
