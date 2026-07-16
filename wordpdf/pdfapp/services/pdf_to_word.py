"""PDF to Word conversion through Microsoft Word COM automation."""
import logging
import os

from pdfapp.services.exceptions import ConversionError, FileValidationError
from pdfapp.services.word_com import (
    WORD_REQUIRED_MESSAGE,
    WordComUnavailable,
    convert_pdf_to_docx,
    is_word_com_available,
)
from pdfapp.utils.validators import validate_docx_file, validate_pdf_file


logger = logging.getLogger(__name__)


def detect_pdf_to_word_engines():
    """Return the configured PDF to Word engine list in quality order."""
    return ["word_com"] if is_word_com_available() else []


def detect_pdf_to_word_engine():
    engines = detect_pdf_to_word_engines()
    return engines[0] if engines else None


def pdf_to_word_word_com(pdf_path, docx_path):
    """Convert PDF to DOCX using Microsoft Word's native PDF import engine."""
    convert_pdf_to_docx(pdf_path, docx_path)
    validate_docx_file(docx_path)
    return True


def safe_pdf_to_word(pdf_path, docx_path):
    """Validate and convert PDF to DOCX using Microsoft Word COM.

    Word COM is intentionally the only live backend for PDF to Word because the
    previous parser-based fallbacks flattened resumes, tables, columns, shapes,
    headers, footers, and other layout data.
    """
    validate_pdf_file(pdf_path)

    if not is_word_com_available():
        raise ConversionError(WORD_REQUIRED_MESSAGE)

    temp_docx = docx_path + ".word_com.tmp.docx"
    if os.path.exists(temp_docx):
        try:
            os.remove(temp_docx)
        except OSError:
            logger.debug("Could not remove stale PDF to Word temp file %s.", temp_docx, exc_info=True)

    try:
        logger.info("Converting PDF to Word with Microsoft Word COM: %s", pdf_path)
        pdf_to_word_word_com(pdf_path, temp_docx)
        if os.path.exists(docx_path):
            os.remove(docx_path)
        os.replace(temp_docx, docx_path)
        validate_docx_file(docx_path)
        logger.info("PDF to Word conversion completed with Microsoft Word COM: %s", docx_path)
        return True
    except FileValidationError:
        raise
    except WordComUnavailable as exc:
        raise ConversionError(WORD_REQUIRED_MESSAGE) from exc
    except ConversionError as exc:
        raise ConversionError(
            "Microsoft Word could not convert this PDF to Word. "
            "Please make sure the PDF is not scanned, corrupted, encrypted, or password-protected."
        ) from exc
    except Exception as exc:
        logger.exception("PDF to Word conversion failed.")
        raise ConversionError(
            "Microsoft Word could not convert this PDF to Word. "
            "Please make sure the PDF is not scanned, corrupted, encrypted, or password-protected."
        ) from exc
    finally:
        if os.path.exists(temp_docx):
            try:
                os.remove(temp_docx)
            except OSError:
                logger.debug("Could not remove PDF to Word temp file %s.", temp_docx, exc_info=True)
