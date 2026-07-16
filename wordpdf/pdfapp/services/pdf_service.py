"""PDF-specific backend services."""
import json
import logging
import os
import tempfile

from pdfapp.views_legacy import (
    _parse_pdf_color,
    _pdf_num,
    safe_pdf_to_excel,
    safe_image_to_pdf,
)
from .pdf_to_word import safe_pdf_to_word, detect_pdf_to_word_engine
from .compression import compress_pdf
from .exceptions import ConversionError
from pdfapp.utils.validators import validate_pdf_file


logger = logging.getLogger(__name__)


def _add_pdf_text_annotation(page, rect, text, color=(0, 0, 0), fontsize=12):
    """Add visible editable FreeText text, falling back to page text insertion."""
    try:
        annot = page.add_freetext_annot(
            rect,
            text,
            fontsize=fontsize,
            fontname="helv",
            text_color=color,
            align=0,
        )
        try:
            annot.set_border(width=0)
        except Exception:
            pass
        annot.set_opacity(1.0)
        annot.update()
        return True
    except Exception:
        logger.exception("FreeText annotation failed; falling back to inserted text.")
        try:
            page.insert_textbox(
                rect,
                text,
                fontsize=fontsize,
                fontname="helv",
                color=color,
                align=0,
                overlay=True,
            )
            return True
        except Exception:
            logger.exception("PDF text insertion fallback failed.")
            return False


def _cover_pdf_rect(page, rect):
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)


def safe_edit_pdf(input_path, output_path, actions_json):
    """Apply PDF edit actions directly to the original PDF without DOCX conversion."""
    import fitz

    validate_pdf_file(input_path)

    try:
        actions = json.loads(actions_json or "[]")
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid PDF edit payload for %s: %s", input_path, exc)
        raise ConversionError("The PDF edit data was invalid. Please reopen the editor and try again.") from exc

    if not isinstance(actions, list) or not actions:
        raise ConversionError("Please add at least one edit before saving the PDF.")

    output_dir = os.path.dirname(os.path.abspath(output_path)) or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    fd, temp_output = tempfile.mkstemp(prefix="pdf_edit_", suffix=".pdf", dir=output_dir)
    os.close(fd)

    doc = None
    applied = 0
    try:
        doc = fitz.open(input_path)
        if doc.is_encrypted or doc.needs_pass:
            raise ConversionError("Encrypted or password-protected PDFs cannot be edited.")

        for item in actions:
            if not isinstance(item, dict):
                continue

            page_idx = int(_pdf_num(item.get("page"), 1, 1, len(doc))) - 1
            page = doc[page_idx]
            pw, ph = page.rect.width, page.rect.height
            kind = item.get("type")

            x = _pdf_num(item.get("x"), 0, 0, pw)
            y = _pdf_num(item.get("y"), 0, 0, ph)
            w = _pdf_num(item.get("width"), 0, 0, pw - x)
            h = _pdf_num(item.get("height"), 0, 0, ph - y)

            if kind == "text":
                text = (item.get("text") or "").strip()
                if not text:
                    continue
                fs = max(8, min(96, int(_pdf_num(item.get("fontSize"), 18))))
                color = _parse_pdf_color(item.get("color"), (0, 0, 0))
                rect = fitz.Rect(x, max(0, y), min(pw, x + max(80, len(text) * fs * 0.62)), min(ph, y + fs * 1.45))
                if _add_pdf_text_annotation(page, rect, text, color=color, fontsize=fs):
                    applied += 1

            elif kind in ("highlight", "whiteout"):
                if w <= 0 or h <= 0:
                    continue
                rect = fitz.Rect(x, y, x + w, y + h)
                if kind == "whiteout":
                    _cover_pdf_rect(page, rect)
                else:
                    color = _parse_pdf_color(item.get("color"), (1, 0.9, 0))
                    annot = page.add_rect_annot(rect)
                    annot.set_colors(stroke=color, fill=color)
                    annot.set_opacity(0.35)
                    annot.update()
                applied += 1

            elif kind == "draw":
                points = item.get("points") or []
                if len(points) < 2:
                    continue
                color = _parse_pdf_color(item.get("color"), (0.9, 0.1, 0.1))
                line_width = _pdf_num(item.get("lineWidth"), 2, 1, 24)
                clean_points = []
                for point in points:
                    if isinstance(point, list) and len(point) == 2:
                        clean_points.append((
                            _pdf_num(point[0], 0, 0, pw),
                            _pdf_num(point[1], 0, 0, ph),
                        ))
                for start, end in zip(clean_points, clean_points[1:]):
                    page.draw_line(start, end, color=color, width=line_width, overlay=True)
                applied += 1

            elif kind == "rotate":
                degrees = int(_pdf_num(item.get("degrees"), 90))
                degrees = degrees if degrees in (90, 180, 270) else 90
                page.set_rotation((page.rotation + degrees) % 360)
                applied += 1

            elif kind == "replace":
                find_text = (item.get("find") or "").strip()
                if not find_text:
                    continue
                replace_text = item.get("replace") or ""
                color = _parse_pdf_color(item.get("color"), (0, 0, 0))
                matches = page.search_for(find_text)
                for rect in matches:
                    rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
                    fs = max(6, min(96, rect.height * 0.9))
                    _cover_pdf_rect(page, rect)
                    if replace_text:
                        _add_pdf_text_annotation(page, rect, replace_text, color=color, fontsize=fs)
                if matches:
                    applied += 1

            elif kind == "edit_text_span":
                replace_text = item.get("replace") or ""
                if w <= 0 or h <= 0:
                    continue
                fs = max(6, min(96, _pdf_num(item.get("fontSize"), h)))
                color = _parse_pdf_color(item.get("color"), (0, 0, 0))
                rect = fitz.Rect(x, y, min(pw, x + max(w, 20)), min(ph, y + max(h, fs * 1.2)))
                _cover_pdf_rect(page, rect)
                if replace_text:
                    _add_pdf_text_annotation(page, rect, replace_text, color=color, fontsize=fs)
                applied += 1

        if applied == 0:
            raise ConversionError("No valid PDF edits were applied. Please make an edit and try again.")

        doc.save(temp_output, garbage=4, deflate=True)
        doc.close()
        doc = None
        validate_pdf_file(temp_output)
        os.replace(temp_output, output_path)
        logger.info("PDF edited successfully: %s -> %s (%s actions)", input_path, output_path, applied)
        return True
    except ConversionError:
        logger.exception("PDF edit failed with a user-facing error.")
        raise
    except Exception as exc:
        logger.exception("PDF edit failed for %s", input_path)
        raise ConversionError("Could not save the edited PDF. Please try another valid PDF file.") from exc
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                logger.warning("Could not remove temporary PDF edit file: %s", temp_output)

__all__ = [
    "_parse_pdf_color",
    "_pdf_num",
    "_add_pdf_text_annotation",
    "safe_edit_pdf",
    "safe_pdf_to_excel",
    "safe_image_to_pdf",
    "safe_pdf_to_word",
    "detect_pdf_to_word_engine",
    "compress_pdf",
]
