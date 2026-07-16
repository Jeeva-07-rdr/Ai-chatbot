"""In-browser document editor services backed by Microsoft Word COM."""
import logging
import os
import re
from difflib import SequenceMatcher
from html.parser import HTMLParser

from pdfapp.services.exceptions import ConversionError
from pdfapp.services.word_com import (
    WORD_REQUIRED_MESSAGE,
    WordComUnavailable,
    export_word_html,
    extract_word_paragraph_texts,
)
from pdfapp.utils.validators import validate_docx_file


logger = logging.getLogger(__name__)


def _read_docx_theme_colors(docx_path):
    """Compatibility helper retained for imports from older service modules."""
    validate_docx_file(docx_path)
    return {}


def _apply_color_mod(hex_color, tint=None, shade=None):
    """Compatibility helper retained for imports from older service modules."""
    return hex_color


def post_process_docx_layout(file_path):
    """Do not mutate DOCX layout after Word COM processing."""
    validate_docx_file(file_path)
    return True


class _EditorTextParser(HTMLParser):
    block_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._current = []
        self._depth = 0
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self.block_tags:
            if self._depth == 0:
                self._current = []
            self._depth += 1
        elif tag == "br" and self._depth:
            self._current.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in self.block_tags and self._depth:
            self._depth -= 1
            if self._depth == 0:
                text = _clean_text("".join(self._current))
                if text:
                    self.blocks.append(text)
                self._current = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._depth:
            self._current.append(data)


def _clean_text(value):
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def _strip_exported_list_marker(value):
    return re.sub(r"^(?:[\u2022\u25aa\u25cf\u2013\u2014-]|\d+[.)])\s+", "", _clean_text(value))


def _extract_html_text_blocks(html_content):
    parser = _EditorTextParser()
    parser.feed(html_content or "")
    return parser.blocks


def _html_body_fragment(html_content):
    style_blocks = "".join(re.findall(r"<style[\s\S]*?</style>", html_content or "", flags=re.I))
    match = re.search(r"<body[^>]*>([\s\S]*?)</body>", html_content or "", flags=re.I)
    body = match.group(1) if match else html_content
    return style_blocks + body


def _build_editor_replacements(base_docx_path, html_content):
    source_records = extract_word_paragraph_texts(base_docx_path)
    edited_blocks = _extract_html_text_blocks(html_content)

    if not source_records:
        logger.info("No source text blocks were found in DOCX.")
        return []
    if not edited_blocks:
        logger.info("No editable text blocks were found in submitted editor HTML.")
        return []

    source_blocks = [record[1] for record in source_records]
    source_match_blocks = [_strip_exported_list_marker(text) for text in source_blocks]
    edited_match_blocks = [_strip_exported_list_marker(text) for text in edited_blocks]
    replacements = []

    matcher = SequenceMatcher(None, source_match_blocks, edited_match_blocks, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        source_count = i2 - i1
        edited_count = j2 - j1
        if tag == "replace" and source_count == edited_count:
            for source_record, old_text, new_text in zip(
                source_records[i1:i2],
                source_match_blocks[i1:i2],
                edited_match_blocks[j1:j2],
            ):
                if old_text != new_text:
                    replacements.append((source_record[0], new_text))
        else:
            logger.warning(
                "Skipped unsupported structural editor change: %s source=%s edited=%s",
                tag,
                source_count,
                edited_count,
            )

    return replacements


def prepare_editor_html_from_docx(docx_path):
    """Return editor HTML rendered by Microsoft Word."""
    validate_docx_file(docx_path)
    try:
        return _html_body_fragment(export_word_html(docx_path))
    except WordComUnavailable as exc:
        raise ConversionError(WORD_REQUIRED_MESSAGE) from exc
    except ConversionError:
        raise
    except Exception as exc:
        logger.exception("Word COM HTML preview failed.")
        raise ConversionError(
            "Microsoft Word could not open this document for editing. "
            "Please make sure it is not corrupted or password-protected."
        ) from exc


def docx_to_editor_html(file_path):
    return prepare_editor_html_from_docx(file_path)


def prepare_editor_html_from_pdf(pdf_path):
    """Convert PDF to DOCX with Word COM, then render the DOCX editor preview."""
    from .pdf_to_word import safe_pdf_to_word

    base = os.path.splitext(pdf_path)[0]
    docx_tmp = base + ".__pdf_edit__.docx"
    if os.path.exists(docx_tmp):
        os.remove(docx_tmp)
    safe_pdf_to_word(pdf_path, docx_tmp)
    try:
        return prepare_editor_html_from_docx(docx_tmp)
    finally:
        if os.path.exists(docx_tmp):
            try:
                os.remove(docx_tmp)
            except OSError:
                logger.debug("Could not remove PDF editor temp DOCX %s.", docx_tmp, exc_info=True)


def _replace_base64_images_with_temp_files(html_content):
    """Find all base64 data URIs in img tags, write them to temp files, and return modified HTML + file paths."""
    import base64
    import tempfile
    
    temp_files = []
    
    def replace_match(match):
        img_format = match.group(1) # png, jpeg, etc.
        base64_data = match.group(2)
        try:
            image_bytes = base64.b64decode(base64_data)
            suffix = f".{img_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(image_bytes)
                temp_path = f.name
            temp_files.append(temp_path)
            return f'src="{temp_path}"'
        except Exception:
            return match.group(0)
            
    # Pattern to match src="data:image/png;base64,..."
    pattern = r'src="data:image/(png|jpeg|jpg|gif|webp);base64,([^"]+)"'
    html_content = re.sub(pattern, replace_match, html_content)
    
    # Also support single quotes
    pattern_sq = r"src='data:image/(png|jpeg|jpg|gif|webp);base64,([^']+)'"
    html_content = re.sub(pattern_sq, replace_match, html_content)
    
    return html_content, temp_files


def html_to_docx_preserving_layout(html_content, output_path, base_docx_path=None):
    """Save editor changes. Preserves original DOCX styling and layout by using OLE automation InsertFile to replace document body with edited HTML content, falling back to htmldocx."""
    import shutil
    import tempfile
    import pythoncom
    import win32com.client

    # 1. Clean HTML: strip style blocks and HTML comments which get serialized as plain text
    html_content = re.sub(r"<style[\s\S]*?</style>", "", html_content or "", flags=re.I)
    html_content = re.sub(r"<!--[\s\S]*?-->", "", html_content)

    # 2. Try using Word COM OLE InsertFile body replacement to keep all layout & visual styling
    if base_docx_path and os.path.exists(base_docx_path):
        try:
            logger.info("Using Word COM OLE InsertFile replacement to preserve original styling...")
            validate_docx_file(base_docx_path)
            shutil.copy2(base_docx_path, output_path)

            # Wrap in proper HTML structure to force Word to parse it as HTML instead of plain text
            wrapped_html = (
                "<!DOCTYPE html>\n"
                "<html>\n"
                "<head>\n"
                '<meta charset="utf-8">\n'
                "</head>\n"
                "<body>\n"
                f"{html_content}\n"
                "</body>\n"
                "</html>"
            )

            # Write clean HTML content to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
                f.write(wrapped_html)
                temp_html_path = f.name

            pythoncom.CoInitialize()
            word = None
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                
                doc = word.Documents.Open(FileName=os.path.abspath(output_path), ReadOnly=False, AddToRecentFiles=False)
                
                # Replace the document body range with the HTML file contents
                doc.Content.InsertFile(FileName=temp_html_path)
                
                doc.SaveAs2(os.path.abspath(output_path), FileFormat=16) # WD_FORMAT_DOCUMENT_DEFAULT
                doc.Close(SaveChanges=False)
                logger.info("Word COM OLE InsertFile replacement completed successfully.")
            finally:
                if word is not None:
                    try:
                        word.Quit()
                    except Exception:
                        pass
                pythoncom.CoUninitialize()
                
            # Clean up temp HTML file
            if os.path.exists(temp_html_path):
                try:
                    os.remove(temp_html_path)
                except OSError:
                    pass
                
            validate_docx_file(output_path)
            return True
        except Exception as e:
            logger.warning("Word COM OLE InsertFile replacement failed, falling back to htmldocx compile. Error: %s", e, exc_info=True)

    # 3. Fallback: compile HTML to DOCX using htmldocx parser
    temp_image_files = []
    try:
        from docx import Document
        from htmldocx import HtmlToDocx
        logger.info("Compiling HTML to DOCX using htmldocx parser...")
        
        # Pre-process HTML: convert base64 image URIs to temporary files
        html_content, temp_image_files = _replace_base64_images_with_temp_files(html_content)
        
        # If template is provided, load and clear body content (keeps headers/footers)
        if base_docx_path and os.path.exists(base_docx_path):
            validate_docx_file(base_docx_path)
            doc = Document(base_docx_path)
            for p in list(doc.paragraphs):
                parent = p._element.getparent()
                if parent is not None:
                    parent.remove(p._element)
            for t in list(doc.tables):
                parent = t._element.getparent()
                if parent is not None:
                    parent.remove(t._element)
        else:
            doc = Document()

        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html_content, doc)
        doc.save(output_path)
        logger.info("Saved edited HTML to DOCX (htmldocx): %s", output_path)
    except Exception as exc:
        logger.exception("Could not save submitted editor changes via htmldocx fallback.")
        raise ConversionError(
            "Could not save the edited Word document. Please try again."
        ) from exc
    finally:
        for temp_file in temp_image_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    validate_docx_file(output_path)
    return True


__all__ = [
    "_read_docx_theme_colors",
    "_apply_color_mod",
    "prepare_editor_html_from_docx",
    "prepare_editor_html_from_pdf",
    "html_to_docx_preserving_layout",
    "docx_to_editor_html",
    "post_process_docx_layout",
]
