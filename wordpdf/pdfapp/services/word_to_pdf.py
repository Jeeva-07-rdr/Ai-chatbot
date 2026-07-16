"""Word to PDF conversion through Microsoft Word COM automation."""
import logging
import os

from pdfapp.services.exceptions import ConversionError, FileValidationError
from pdfapp.services.word_com import (
    WORD_REQUIRED_MESSAGE,
    WordComUnavailable,
    convert_word_to_pdf,
    is_word_com_available,
)
from pdfapp.utils.validators import validate_docx_file, validate_pdf_file


logger = logging.getLogger(__name__)


def _validate_word_input(path):
    ext = os.path.splitext(path or "")[1].lower()
    if ext == ".docx":
        return validate_docx_file(path)
    if ext == ".doc":
        if not path or not os.path.exists(path):
            raise FileValidationError("Please upload a Word document.")
        if os.path.getsize(path) == 0:
            raise FileValidationError("The uploaded Word document is empty.")
        return True
    raise FileValidationError("Please upload a DOCX or DOC Word document.")


def detect_word_to_pdf_engines():
    """Return the configured Word to PDF engine list in quality order."""
    return ["word_com"] if is_word_com_available() else []


def detect_word_to_pdf_engine():
    engines = detect_word_to_pdf_engines()
    return engines[0] if engines else None


def word_to_pdf_word_com(docx_path, pdf_path):
    """Convert DOC/DOCX to PDF using Microsoft Word's native PDF exporter."""
    convert_word_to_pdf(docx_path, pdf_path)
    validate_pdf_file(pdf_path)
    return True


def safe_docx_to_pdf(docx_path, pdf_path=None):
    """Validate and convert DOC/DOCX to PDF using Microsoft Word COM."""
    _validate_word_input(docx_path)

    if pdf_path is None:
        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

    if not is_word_com_available():
        raise ConversionError(WORD_REQUIRED_MESSAGE)

    temp_pdf = pdf_path + ".word_com.tmp.pdf"
    if os.path.exists(temp_pdf):
        try:
            os.remove(temp_pdf)
        except OSError:
            logger.debug("Could not remove stale Word to PDF temp file %s.", temp_pdf, exc_info=True)

    try:
        logger.info("Converting Word to PDF with Microsoft Word COM: %s", docx_path)
        word_to_pdf_word_com(docx_path, temp_pdf)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        os.replace(temp_pdf, pdf_path)
        validate_pdf_file(pdf_path)
        logger.info("Word to PDF conversion completed with Microsoft Word COM: %s", pdf_path)
        return True
    except FileValidationError:
        raise
    except WordComUnavailable as exc:
        raise ConversionError(WORD_REQUIRED_MESSAGE) from exc
    except ConversionError as exc:
        raise ConversionError(
            "Microsoft Word could not export this document as PDF. "
            "Please make sure the document is not corrupted or password-protected."
        ) from exc
    except Exception as exc:
        logger.exception("Word to PDF conversion failed.")
        raise ConversionError(
            "Microsoft Word could not export this document as PDF. "
            "Please make sure the document is not corrupted or password-protected."
        ) from exc
    finally:
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except OSError:
                logger.debug("Could not remove Word to PDF temp file %s.", temp_pdf, exc_info=True)
