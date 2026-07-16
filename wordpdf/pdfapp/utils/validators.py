"""Upload and output file validation helpers."""
import logging
import os
import zipfile

from pdfapp.services.exceptions import FileValidationError


logger = logging.getLogger(__name__)


def validate_pdf_file(pdf_path, *, require_pages=True):
    """Validate that a file is a readable, unencrypted PDF."""
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileValidationError("Please upload a PDF file.")

    if os.path.getsize(pdf_path) == 0:
        raise FileValidationError("The uploaded PDF is empty.")

    try:
        with open(pdf_path, "rb") as handle:
            header = handle.read(5)
    except OSError:
        logger.exception("Could not read uploaded PDF: %s", pdf_path)
        raise FileValidationError("We could not read the uploaded PDF.")

    if header != b"%PDF-":
        raise FileValidationError("This file is not a valid PDF.")

    try:
        import fitz

        doc = fitz.open(pdf_path)
        try:
            if doc.is_encrypted or doc.needs_pass:
                raise FileValidationError(
                    "This PDF is encrypted or password-protected. Please unlock it and upload it again."
                )
            if require_pages and len(doc) == 0:
                raise FileValidationError("This PDF has no readable pages.")
            if require_pages:
                doc.load_page(0)
        finally:
            doc.close()
    except FileValidationError:
        raise
    except Exception as exc:
        logger.exception("PDF validation failed for %s", pdf_path)
        raise FileValidationError(
            "This PDF appears to be corrupted or unsupported. Please re-export it as a standard PDF and try again."
        ) from exc

    return True


def validate_docx_file(docx_path):
    """Validate that a file is a readable DOCX package."""
    if not docx_path or not os.path.exists(docx_path):
        raise FileValidationError("Please upload a Word document.")

    if os.path.getsize(docx_path) == 0:
        raise FileValidationError("The uploaded Word document is empty.")

    try:
        with zipfile.ZipFile(docx_path) as package:
            names = set(package.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise FileValidationError("This file is not a valid DOCX document.")
            bad_member = package.testzip()
            if bad_member:
                logger.warning("Corrupted DOCX member %s in %s", bad_member, docx_path)
                raise FileValidationError("This Word document appears to be corrupted.")
    except FileValidationError:
        raise
    except zipfile.BadZipFile as exc:
        raise FileValidationError("This file is not a valid DOCX document.") from exc
    except Exception as exc:
        logger.exception("DOCX validation failed for %s", docx_path)
        raise FileValidationError("We could not read this Word document.") from exc

    return True
