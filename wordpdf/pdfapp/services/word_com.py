"""Microsoft Word COM automation helpers for high-fidelity conversions."""
import base64
import logging
import mimetypes
import os
import re
import tempfile

from pdfapp.services.exceptions import ConversionError


logger = logging.getLogger(__name__)

WORD_REQUIRED_MESSAGE = "Microsoft Word is required for high-fidelity document conversion."

WD_FORMAT_DOCUMENT_DEFAULT = 16
WD_FORMAT_PDF = 17
WD_FORMAT_FILTERED_HTML = 10
WD_EXPORT_FORMAT_PDF = 17

_word_com_checked = False
_word_com_available = False


class WordComUnavailable(ConversionError):
    """Microsoft Word COM automation is not available on this machine."""


def _normalize_path(path):
    return os.path.abspath(os.fspath(path))


def _import_com():
    if os.name != "nt":
        raise WordComUnavailable(WORD_REQUIRED_MESSAGE)
    try:
        import pythoncom
        import win32com.client
    except Exception as exc:
        raise WordComUnavailable(WORD_REQUIRED_MESSAGE) from exc
    return pythoncom, win32com.client


def is_word_com_available(force=False):
    """Return True when Microsoft Word can be started through COM."""
    global _word_com_checked, _word_com_available
    if _word_com_checked and not force:
        return _word_com_available

    _word_com_checked = True
    _word_com_available = False
    try:
        pythoncom, win32_client = _import_com()
        pythoncom.CoInitialize()
        word = None
        try:
            word = win32_client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            _word_com_available = True
        finally:
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    logger.debug("Could not close Word during COM availability check.", exc_info=True)
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
    except Exception:
        logger.info("Microsoft Word COM automation is unavailable.", exc_info=True)
    return _word_com_available


def require_word_com():
    if not is_word_com_available():
        raise WordComUnavailable(WORD_REQUIRED_MESSAGE)
    return True


def _run_with_word(callback, operation):
    """Run a callback with a hidden Word instance and guaranteed cleanup."""
    pythoncom, win32_client = _import_com()
    pythoncom.CoInitialize()
    word = None
    try:
        word = win32_client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        return callback(word)
    except WordComUnavailable:
        raise
    except Exception as exc:
        logger.exception("Microsoft Word COM operation failed: %s", operation)
        raise ConversionError(f"{operation} failed in Microsoft Word.") from exc
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                logger.debug("Could not close Microsoft Word after %s.", operation, exc_info=True)
        word = None
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _close_document(doc, save_changes=False, operation="Word COM operation"):
    if doc is None:
        return
    try:
        doc.Close(SaveChanges=save_changes)
    except Exception:
        logger.debug("Could not close Word document after %s.", operation, exc_info=True)


def open_document(word, input_path, *, read_only=True):
    abs_path = _normalize_path(input_path)
    
    # PDF files require special handling - use ConfirmConversions to allow Word to handle format conversion
    is_pdf = abs_path.lower().endswith('.pdf')
    
    return word.Documents.Open(
        FileName=abs_path,
        ConfirmConversions=False,  # Never allow dialogs in headless server context
        ReadOnly=read_only,
        AddToRecentFiles=False,
        OpenAndRepair=not is_pdf,  # Don't use OpenAndRepair for PDFs
    )


def convert_pdf_to_docx(pdf_path, docx_path):
    """Use Microsoft Word's PDF import engine and save the result as DOCX."""
    require_word_com()
    pdf_abs = _normalize_path(pdf_path)
    docx_abs = _normalize_path(docx_path)

    def _convert(word):
        doc = None
        try:
            doc = open_document(word, pdf_abs, read_only=True)
            doc.SaveAs2(docx_abs, FileFormat=WD_FORMAT_DOCUMENT_DEFAULT)
            _close_document(doc, save_changes=False, operation="PDF to Word conversion")
            doc = None
            return True
        finally:
            _close_document(doc, save_changes=False, operation="PDF to Word conversion")

    try:
        return _run_with_word(_convert, "PDF to Word conversion")
    except Exception as exc:
        logger.warning("Word COM PDF import failed, attempting pdf2docx fallback.", exc_info=True)
        # Fallback to pdf2docx for better compatibility
        try:
            import time
            from pdf2docx import convert as pdf2docx_convert
            
            # Use a temporary file to avoid permission issues
            temp_docx_fallback = docx_abs + ".pdf2docx.tmp"
            if os.path.exists(temp_docx_fallback):
                try:
                    os.remove(temp_docx_fallback)
                except OSError:
                    pass
            
            pdf2docx_convert(pdf_abs, temp_docx_fallback, pages=None)
            
            # Wait a moment for file handles to be released
            time.sleep(0.1)
            
            # Move temp file to final location
            if os.path.exists(docx_abs):
                try:
                    os.remove(docx_abs)
                except OSError:
                    pass
            
            # Retry move if it fails due to locking
            for attempt in range(3):
                try:
                    os.replace(temp_docx_fallback, docx_abs)
                    return True
                except (OSError, PermissionError) as move_exc:
                    if attempt < 2:
                        time.sleep(0.2)
                    else:
                        raise move_exc
                        
        except ImportError:
            logger.error("pdf2docx not available as fallback for PDF to Word conversion.")
            raise ConversionError("PDF import in Microsoft Word failed. Please ensure the PDF is valid and try again.") from exc
        except Exception as fallback_exc:
            logger.error("pdf2docx fallback also failed for PDF to Word conversion.", exc_info=True)
            raise ConversionError("PDF import failed. Please ensure the PDF is valid and try again.") from fallback_exc


def convert_word_to_pdf(input_path, pdf_path):
    """Export DOC/DOCX to PDF using Microsoft Word."""
    require_word_com()
    input_abs = _normalize_path(input_path)
    pdf_abs = _normalize_path(pdf_path)

    def _convert(word):
        doc = None
        try:
            doc = open_document(word, input_abs, read_only=True)
            try:
                doc.ExportAsFixedFormat(
                    OutputFileName=pdf_abs,
                    ExportFormat=WD_EXPORT_FORMAT_PDF,
                    OpenAfterExport=False,
                    OptimizeFor=0,
                    Range=0,
                    Item=0,
                    IncludeDocProps=True,
                    KeepIRM=True,
                    CreateBookmarks=1,
                    DocStructureTags=True,
                    BitmapMissingFonts=True,
                    UseISO19005_1=False,
                )
            except Exception:
                logger.info("Word ExportAsFixedFormat failed; trying SaveAs2 PDF.", exc_info=True)
                doc.SaveAs2(pdf_abs, FileFormat=WD_FORMAT_PDF)
            _close_document(doc, save_changes=False, operation="Word to PDF conversion")
            doc = None
            return True
        finally:
            _close_document(doc, save_changes=False, operation="Word to PDF conversion")

    return _run_with_word(_convert, "Word to PDF conversion")


def save_word_document_as_docx(input_path, docx_path):
    """Open a Word-supported document and save it as DOCX."""
    require_word_com()
    input_abs = _normalize_path(input_path)
    docx_abs = _normalize_path(docx_path)

    def _save(word):
        doc = None
        try:
            doc = open_document(word, input_abs, read_only=False)
            doc.SaveAs2(docx_abs, FileFormat=WD_FORMAT_DOCUMENT_DEFAULT)
            _close_document(doc, save_changes=False, operation="DOCX save")
            doc = None
            return True
        finally:
            _close_document(doc, save_changes=False, operation="DOCX save")

    return _run_with_word(_save, "DOCX save")


def _read_text_file(path):
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding, errors="strict") as handle:
                return handle.read()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _embed_local_html_assets(html_content, html_path):
    base_dir = os.path.dirname(_normalize_path(html_path))

    def replace_src(match):
        quote = match.group(1)
        ref = match.group(2)
        if re.match(r"^(?:https?:|data:|#|mailto:)", ref, flags=re.I):
            return match.group(0)
        asset_path = _normalize_path(os.path.join(base_dir, ref.replace("/", os.sep)))
        if os.path.commonpath([base_dir, asset_path]) != base_dir or not os.path.exists(asset_path):
            return match.group(0)
        mime_type = mimetypes.guess_type(asset_path)[0] or "application/octet-stream"
        try:
            with open(asset_path, "rb") as handle:
                encoded = base64.b64encode(handle.read()).decode("ascii")
            return f"src={quote}data:{mime_type};base64,{encoded}{quote}"
        except OSError:
            logger.debug("Could not embed Word HTML asset: %s", asset_path, exc_info=True)
            return match.group(0)

    return re.sub(r"src=(['\"])([^'\"]+)\1", replace_src, html_content or "", flags=re.I)


def export_word_html(input_path):
    """Render a Word document to HTML using Word's own layout export."""
    require_word_com()
    input_abs = _normalize_path(input_path)

    with tempfile.TemporaryDirectory(prefix="docuconverter_word_html_") as temp_dir:
        html_path = os.path.join(temp_dir, "preview.html")

        def _export(word):
            doc = None
            try:
                doc = open_document(word, input_abs, read_only=True)
                doc.SaveAs2(_normalize_path(html_path), FileFormat=WD_FORMAT_FILTERED_HTML)
                _close_document(doc, save_changes=False, operation="Word HTML export")
                doc = None
                return True
            finally:
                _close_document(doc, save_changes=False, operation="Word HTML export")

        _run_with_word(_export, "Word HTML export")
        return _embed_local_html_assets(_read_text_file(html_path), html_path)


def _clean_word_text(value):
    return re.sub(r"\s+", " ", (value or "").replace("\x07", " ").replace("\r", " ")).strip()


def extract_word_paragraph_texts(input_path):
    """Read editable paragraph text in Word's document order."""
    require_word_com()
    input_abs = _normalize_path(input_path)

    def _extract(word):
        doc = None
        try:
            doc = open_document(word, input_abs, read_only=True)
            blocks = []
            for idx in range(1, doc.Paragraphs.Count + 1):
                text = _clean_word_text(doc.Paragraphs(idx).Range.Text)
                if text:
                    blocks.append((idx, text))
            _close_document(doc, save_changes=False, operation="Word paragraph extraction")
            doc = None
            return blocks
        finally:
            _close_document(doc, save_changes=False, operation="Word paragraph extraction")

    return _run_with_word(_extract, "Word paragraph extraction")


def _trim_range_end(range_obj):
    while range_obj.End > range_obj.Start:
        text = range_obj.Text or ""
        if not text or text[-1] not in ("\r", "\x07"):
            break
        range_obj.End = range_obj.End - 1
    return range_obj


def replace_word_paragraph_texts(docx_path, replacements):
    """Replace paragraph text in-place through Word while retaining document structure."""
    require_word_com()
    docx_abs = _normalize_path(docx_path)
    replacements = [(int(index), text) for index, text in replacements if index]
    if not replacements:
        return 0

    def _replace(word):
        doc = None
        changed = 0
        try:
            doc = open_document(word, docx_abs, read_only=False)
            paragraph_count = doc.Paragraphs.Count
            for paragraph_index, new_text in replacements:
                if paragraph_index < 1 or paragraph_index > paragraph_count:
                    logger.warning("Skipping editor change for missing paragraph %s.", paragraph_index)
                    continue
                paragraph = doc.Paragraphs(paragraph_index)
                rng = _trim_range_end(paragraph.Range.Duplicate)
                if _clean_word_text(rng.Text) == _clean_word_text(new_text):
                    continue
                rng.Text = new_text
                changed += 1
            if changed:
                doc.SaveAs2(docx_abs, FileFormat=WD_FORMAT_DOCUMENT_DEFAULT)
            _close_document(doc, save_changes=False, operation="Word paragraph replacement")
            doc = None
            return changed
        finally:
            _close_document(doc, save_changes=False, operation="Word paragraph replacement")

    return _run_with_word(_replace, "Word paragraph replacement")
