from django.shortcuts import render
from django.http import FileResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
try:
    from docx2pdf import convert
except Exception:
    convert = None

try:
    from pdf2docx import Converter
except Exception:
    Converter = None

import html as html_module
import os
import urllib.parse
import json
import shutil

try:
    import mammoth
except Exception:
    mammoth = None

try:
    from htmldocx import HtmlToDocx
except Exception:
    HtmlToDocx = None


def _read_docx_theme_colors(docx_path):
    """Read accent/theme colors from the DOCX package."""
    import zipfile
    import xml.etree.ElementTree as ET

    defaults = {
        "dark1": "#000000", "light1": "#FFFFFF",
        "dark2": "#44546A", "light2": "#E7E6E6",
        "accent1": "#4472C4", "accent2": "#ED7D31",
        "accent3": "#A5A5A5", "accent4": "#FFC000",
        "accent5": "#5B9BD5", "accent6": "#70AD47",
    }
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    tag_map = {
        "dk1": "dark1", "lt1": "light1", "dk2": "dark2", "lt2": "light2",
        "accent1": "accent1", "accent2": "accent2", "accent3": "accent3",
        "accent4": "accent4", "accent5": "accent5", "accent6": "accent6",
    }
    try:
        with zipfile.ZipFile(docx_path) as zf:
            if "word/theme/theme1.xml" not in zf.namelist():
                return defaults
            root = ET.fromstring(zf.read("word/theme/theme1.xml"))
            scheme = root.find(".//a:themeElements/a:clrScheme", ns)
            if scheme is None:
                return defaults
            for child in scheme:
                key = tag_map.get(child.tag.split("}")[-1])
                if not key:
                    continue
                rgb = child.find("a:srgbClr", ns)
                if rgb is not None and rgb.get("val"):
                    defaults[key] = "#" + rgb.get("val").upper()
    except Exception as exc:
        print("Theme read error:", exc)
    return defaults


def _apply_color_mod(hex_color, tint=None, shade=None):
    if not hex_color or not hex_color.startswith("#"):
        return hex_color
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    if tint is not None:
        t = int(tint) / 255.0
        r = int(r + (255 - r) * (1 - t))
        g = int(g + (255 - g) * (1 - t))
        b = int(b + (255 - b) * (1 - t))
    if shade is not None:
        s = int(shade) / 255.0
        r = int(r * s)
        g = int(g * s)
        b = int(b * s)
    return f"#{r:02X}{g:02X}{b:02X}"


def prepare_editor_html_from_docx(docx_path):
    """Apply resume layout fixes, then convert DOCX to styled HTML."""
    import tempfile
    fd, work_path = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    try:
        shutil.copy2(docx_path, work_path)
        post_process_docx_layout(work_path)
        return docx_to_editor_html(work_path)
    finally:
        if os.path.exists(work_path):
            os.remove(work_path)


def prepare_editor_html_from_pdf(pdf_path):
    """Convert PDF to DOCX, then to styled HTML for the Word-style editor."""
    base = os.path.splitext(pdf_path)[0]
    docx_tmp = base + ".__pdf_edit__.docx"
    if os.path.exists(docx_tmp):
        os.remove(docx_tmp)
    cv = Converter(pdf_path)
    cv.convert(docx_tmp)
    cv.close()
    try:
        return prepare_editor_html_from_docx(docx_tmp)
    finally:
        if os.path.exists(docx_tmp):
            os.remove(docx_tmp)


def docx_to_editor_html(file_path):
    """Convert DOCX to HTML with inline styles so the in-browser editor keeps layout."""
    import docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn

    theme_colors = _read_docx_theme_colors(file_path)

    def _cell_shading(cell):
        tcPr = cell._tc.tcPr
        if tcPr is None:
            return None
        shd = tcPr.find(qn("w:shd"))
        if shd is None:
            return None
        fill = shd.get(qn("w:fill"))
        if fill and fill.lower() not in ("auto", "ffffff"):
            fill = fill.strip().lstrip("#")
            if len(fill) == 6:
                return f"#{fill.upper()}"
        theme = shd.get(qn("w:themeFill"))
        if theme:
            base = theme_colors.get(theme, theme_colors.get("accent1"))
            tint = shd.get(qn("w:themeFillTint"))
            shade = shd.get(qn("w:themeFillShade"))
            return _apply_color_mod(base, tint, shade)
        return None

    def _cell_border_styles(cell):
        tcPr = cell._tc.tcPr
        if tcPr is None:
            return []
        borders = tcPr.find(qn("w:tcBorders"))
        if borders is None:
            return []
        styles = []
        for side in ("top", "left", "bottom", "right"):
            el = borders.find(qn(f"w:{side}"))
            if el is None:
                continue
            val = el.get(qn("w:val"))
            if not val or val in ("none", "nil", "dashed"):
                continue
            color = el.get(qn("w:color"), "000000")
            if color in ("auto", "FFFFFF", "ffffff"):
                continue
            sz = el.get(qn("w:sz"), "4")
            try:
                width_pt = max(0.25, float(sz) / 8)
            except (TypeError, ValueError):
                width_pt = 0.5
            styles.append(f"border-{side}:{width_pt}pt solid #{color.lstrip('#')}")
        return styles

    def _grid_span(cell):
        tcPr = cell._tc.tcPr
        if tcPr is None:
            return 1
        gs = tcPr.find(qn("w:gridSpan"))
        if gs is not None:
            val = gs.get(qn("w:val"))
            if val:
                return int(val)
        return 1

    def _run_to_html(run):
        text = html_module.escape(run.text)
        if not text:
            return ""
        styles = []
        font = run.font
        if font is not None and font.name:
            styles.append(f"font-family:{html_module.escape(font.name)}, Calibri, sans-serif")
        if font is not None and font.size:
            styles.append(f"font-size:{font.size.pt}pt")
        if font is not None and font.color and font.color.rgb:
            styles.append(f"color:#{font.color.rgb}")
        if run.bold:
            styles.append("font-weight:bold")
        if run.italic:
            styles.append("font-style:italic")
        if run.underline:
            styles.append("text-decoration:underline")
        if font is not None and font.highlight_color:
            styles.append("background-color:#FFFF00")
        if styles:
            return f'<span style="{"; ".join(styles)}">{text}</span>'
        return text

    def _para_to_html(paragraph):
        inner = "".join(_run_to_html(r) for r in paragraph.runs)
        if not inner:
            inner = "<br>"

        styles = []
        pf = paragraph.paragraph_format
        if pf.alignment is not None:
            align_map = {
                WD_ALIGN_PARAGRAPH.LEFT: "left",
                WD_ALIGN_PARAGRAPH.CENTER: "center",
                WD_ALIGN_PARAGRAPH.RIGHT: "right",
                WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
            }
            align = align_map.get(pf.alignment)
            if align:
                styles.append(f"text-align:{align}")
        if pf.space_before:
            styles.append(f"margin-top:{pf.space_before.pt}pt")
        if pf.space_after:
            styles.append(f"margin-bottom:{pf.space_after.pt}pt")
        if pf.left_indent:
            styles.append(f"margin-left:{pf.left_indent.inches}in")

        para_style = paragraph.style
        style_name = (para_style.name if para_style is not None else "") or ""
        style_name = style_name.lower()
        if "heading 1" in style_name:
            tag = "h1"
            styles.append("font-weight:bold")
        elif "heading 2" in style_name:
            tag = "h2"
            styles.append("font-weight:bold")
        elif "heading 3" in style_name:
            tag = "h3"
            styles.append("font-weight:bold")
        else:
            tag = "p"

        style_attr = f' style="{"; ".join(styles)}"' if styles else ""
        return f"<{tag}{style_attr}>{inner}</{tag}>"

    def _cell_content_html(cell):
        parts = []
        for p in cell.paragraphs:
            parts.append(_para_to_html(p))
        for nested in cell.tables:
            parts.append(_table_to_html(nested))
        return "".join(parts) if parts else "<p><br></p>"

    def _cell_to_html(cell):
        styles = ["padding:6px 10px", "vertical-align:top"]
        bg = _cell_shading(cell)
        if bg:
            styles.append(f"background-color:{bg}")
            if bg.upper() in ("#1A5276", "#4472C4", "#2F5496", "#1F3864"):
                styles.append("color:#FFFFFF")
        styles.extend(_cell_border_styles(cell))
        if not _cell_border_styles(cell):
            styles.append("border:none")
        if cell.width is not None:
            try:
                styles.append(f"width:{cell.width.inches:.3f}in")
            except Exception:
                pass

        colspan = _grid_span(cell)
        colspan_attr = f' colspan="{colspan}"' if colspan > 1 else ""
        return f'<td{colspan_attr} style="{"; ".join(styles)}">{_cell_content_html(cell)}</td>'

    def _table_to_html(table):
        colgroup = ""
        tbl = table._tbl
        grid = tbl.find(qn("w:tblGrid"))
        if grid is not None:
            cols = []
            for col in grid.findall(qn("w:gridCol")):
                w = col.get(qn("w:w"))
                if w:
                    inches = int(w) / 1440.0
                    cols.append(f'<col style="width:{inches:.3f}in">')
            if cols:
                colgroup = "<colgroup>" + "".join(cols) + "</colgroup>"

        rows = []
        for row in table.rows:
            cells = []
            seen = set()
            for cell in row.cells:
                tc_id = id(cell._tc)
                if tc_id in seen:
                    continue
                seen.add(tc_id)
                cells.append(_cell_to_html(cell))
            if cells:
                rows.append(f'<tr>{"".join(cells)}</tr>')
        return (
            '<table style="width:100%;border-collapse:collapse;border:none;margin:0;table-layout:fixed;">'
            f'{colgroup}{"".join(rows)}</table>'
        )

    doc = docx.Document(file_path)
    tbl_map = {id(t._tbl): t for t in doc.tables}
    para_map = {id(p._p): p for p in doc.paragraphs}

    parts = []
    for child in doc.element.body:
        if child.tag.endswith("tbl"):
            table = tbl_map.get(id(child))
            if table:
                parts.append(_table_to_html(table))
        elif child.tag.endswith("p"):
            para = para_map.get(id(child))
            if para:
                parts.append(_para_to_html(para))

    return "".join(parts) if parts else "<p><br></p>"


def safe_docx_to_pdf(docx_path, pdf_path=None):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        if pdf_path:
            convert(docx_path, pdf_path)
        else:
            convert(docx_path)
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def compress_docx(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("word/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing docx: {e}")
        return False

def compress_pdf(input_path, output_path):
    try:
        import fitz
        doc = fitz.open(input_path)
        doc.scrub(
            metadata=True,
            xml_metadata=True,
            attached_files=True,
            embedded_files=True,
            thumbnails=True,
            reset_fields=False,
            reset_responses=False
        )
        doc.ez_save(
            output_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            use_objstms=True
        )
        doc.close()
        return True
    except Exception as e:
        print(f"Error compressing pdf: {e}")
        return False

def _parse_pdf_color(hex_color, fallback=(0, 0, 0)):
    val = (hex_color or "").strip().lstrip("#")
    if len(val) == 3:
        val = "".join(c * 2 for c in val)
    if len(val) != 6:
        return fallback
    try:
        return tuple(int(val[i:i+2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return fallback

def _pdf_num(value, default=0, lo=None, hi=None):
    try:
        n = float(value)
    except (TypeError, ValueError):
        n = default
    if lo is not None: n = max(lo, n)
    if hi is not None: n = min(hi, n)
    return n


def _add_pdf_text_annotation(page, rect, text, color=(0, 0, 0), fontsize=12):
    try:
        annot = page.add_freetext_annot(
            rect,
            text,
            fontsize=fontsize,
            fontname="helv",
            text_color=color,
            align=0,
        )
        annot.set_opacity(1.0)
        annot.update()
        return True
    except Exception as e:
        print(f"Failed to add text annotation: {e}")
        return False


def safe_edit_pdf(input_path, output_path, actions_json):
    """Apply text / highlight / whiteout / draw annotations to a PDF."""
    import fitz
    try:
        actions = json.loads(actions_json or "[]")
    except (json.JSONDecodeError, TypeError):
        actions = []
    if not isinstance(actions, list) or not actions:
        raise Exception("Please add at least one edit before saving.")
    doc = fitz.open(input_path)
    if doc.is_encrypted:
        doc.close()
        raise Exception("Encrypted PDFs cannot be edited.")
    applied = 0
    for item in actions:
        if not isinstance(item, dict):
            continue
        page_idx = int(_pdf_num(item.get("page"), 1, 1, len(doc))) - 1
        page = doc[page_idx]
        pw, ph = page.rect.width, page.rect.height
        x = _pdf_num(item.get("x"), 0, 0, pw)
        y = _pdf_num(item.get("y"), 0, 0, ph)
        w = _pdf_num(item.get("width"), 0, 0, pw - x)
        h = _pdf_num(item.get("height"), 0, 0, ph - y)
        kind = item.get("type")
        if kind == "text":
            text = (item.get("text") or "").strip()
            if not text:
                continue
            fs = max(8, min(96, int(_pdf_num(item.get("fontSize"), 18))))
            color = _parse_pdf_color(item.get("color"), (0, 0, 0))
            rect = fitz.Rect(x, max(0, y - fs), x + (max(40, len(text) * fs * 0.55)), y + fs)
            if _add_pdf_text_annotation(page, rect, text, color=color, fontsize=fs):
                applied += 1
        elif kind in ("highlight", "whiteout"):
            if w <= 0 or h <= 0:
                continue
            rect = fitz.Rect(x, y, x + w, y + h)
            if kind == "whiteout":
                page.draw_rect(rect, color=(1,1,1), fill=(1,1,1), overlay=True)
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
            lw = _pdf_num(item.get("lineWidth"), 2, 1, 24)
            clean = []
            for p in points:
                if isinstance(p, list) and len(p) == 2:
                    clean.append((_pdf_num(p[0], 0, 0, pw), _pdf_num(p[1], 0, 0, ph)))
            for s, e in zip(clean, clean[1:]):
                page.draw_line(s, e, color=color, width=lw, overlay=True)
            applied += 1
        elif kind == "rotate":
            degrees = int(_pdf_num(item.get("degrees"), 90))
            degrees = degrees if degrees in (90, 180, 270) else 90
            page.set_rotation((page.rotation + degrees) % 360)
            applied += 1
        elif kind == "replace":
            find_str = item.get("find")
            replace_str = item.get("replace") or ""
            if find_str:
                color = _parse_pdf_color(item.get("color"), (0, 0, 0))
                rects = page.search_for(find_str)
                for rect in rects:
                    fs = max(6, rect.y1 - rect.y0)
                    rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
                    _add_pdf_text_annotation(page, rect, replace_str, color=color, fontsize=fs)
                applied += 1
        elif kind == "edit_text_span":
            replace_str = item.get("replace") or ""
            x = _pdf_num(item.get("x"), 0)
            y = _pdf_num(item.get("y"), 0)
            w = _pdf_num(item.get("width"), 0)
            h = _pdf_num(item.get("height"), 0)
            fs = _pdf_num(item.get("fontSize"), h)
            color = _parse_pdf_color(item.get("color"), (0, 0, 0))
            rect = fitz.Rect(x, y, x + max(w, 20), y + max(h, fs))
            if replace_str:
                _add_pdf_text_annotation(page, rect, replace_str, color=color, fontsize=fs)
            applied += 1
    if applied == 0:
        doc.close()
        raise Exception("No valid edits were applied.")
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return True

def safe_pdf_to_excel(pdf_path, excel_path):
    try:
        import pdfplumber
        import openpyxl
        
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                ws = wb.create_sheet(title=f"Page_{i+1}")
                tables = page.extract_tables()
                
                row_idx = 1
                if tables:
                    for table in tables:
                        for row in table:
                            for col_idx, val in enumerate(row):
                                ws.cell(row=row_idx, column=col_idx + 1, value=val)
                            row_idx += 1
                        row_idx += 2
                else:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            ws.cell(row=row_idx, column=1, value=line)
                            row_idx += 1
        wb.save(excel_path)
        return True
    except Exception as e:
        print(f"Error converting PDF to Excel: {e}")
        return False

def safe_image_to_pdf(image_paths, pdf_path):
    try:
        from PIL import Image
        img_list = []
        for path in image_paths:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_list.append(img)
            
        if not img_list:
            return False
            
        img_list[0].save(pdf_path, save_all=True, append_images=img_list[1:])
        return True
    except Exception as e:
        print(f"Error converting Images to PDF: {e}")
        return False

def safe_excel_to_pdf(excel_path, pdf_path):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        import win32com.client
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel_abs = os.path.abspath(excel_path)
        pdf_abs = os.path.abspath(pdf_path)
        wb = excel.Workbooks.Open(excel_abs)
        # xlTypePDF = 0
        wb.ExportAsFixedFormat(0, pdf_abs)
        wb.Close(False)
        excel.Quit()
        return True
    except Exception as e:
        print(f"Error converting Excel to PDF: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def safe_powerpoint_to_pdf(ppt_path, pdf_path):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        import win32com.client
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        ppt_abs = os.path.abspath(ppt_path)
        pdf_abs = os.path.abspath(pdf_path)
        pres = powerpoint.Presentations.Open(ppt_abs, WithWindow=False)
        # ppSaveAsPDF = 32
        pres.SaveAs(pdf_abs, 32)
        pres.Close()
        powerpoint.Quit()
        return True
    except Exception as e:
        print(f"Error converting PowerPoint to PDF: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def safe_powerpoint_to_word(ppt_path, word_path):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        import docx
        doc = docx.Document()
        
        import win32com.client
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        ppt_abs = os.path.abspath(ppt_path)
        pres = powerpoint.Presentations.Open(ppt_abs, WithWindow=False)
        
        doc.add_heading("Extracted Presentation Outline", 0)
        
        for i, slide in enumerate(pres.Slides):
            doc.add_heading(f"Slide {i+1}", level=1)
            for shape in slide.Shapes:
                if shape.HasTextFrame and shape.TextFrame.HasText:
                    text = shape.TextFrame.TextRange.Text.strip()
                    if text:
                        doc.add_paragraph(text)
            doc.add_page_break()
                        
        pres.Close()
        powerpoint.Quit()
        doc.save(word_path)
        return True
    except Exception as e:
        print(f"Error converting PowerPoint to Word: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def safe_pdf_to_powerpoint(pdf_path, ppt_path):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        import fitz
        doc_pdf = fitz.open(pdf_path)
        
        import win32com.client
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        pres = powerpoint.Presentations.Add(WithWindow=False)
        
        for i, page in enumerate(doc_pdf):
            pix = page.get_pixmap(dpi=150)
            temp_img_path = os.path.splitext(pdf_path)[0] + f"_temp_page_{i}.png"
            pix.save(temp_img_path)
            
            # ppLayoutBlank = 12
            slide = pres.Slides.Add(i + 1, 12)
            
            slide_abs_img = os.path.abspath(temp_img_path)
            slide.Shapes.AddPicture(
                FileName=slide_abs_img,
                LinkToFile=False,
                SaveWithDocument=True,
                Left=0,
                Top=0,
                Width=pres.PageSetup.SlideWidth,
                Height=pres.PageSetup.SlideHeight
            )
            
            os.remove(temp_img_path)
            
        ppt_abs = os.path.abspath(ppt_path)
        pres.SaveAs(ppt_abs)
        pres.Close()
        powerpoint.Quit()
        doc_pdf.close()
        return True
    except Exception as e:
        print(f"Error converting PDF to PowerPoint: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def safe_word_to_powerpoint(word_path, ppt_path):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print("CoInitialize failed or already initialized:", e)
        
    try:
        import docx
        doc = docx.Document(word_path)
        
        import win32com.client
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        pres = powerpoint.Presentations.Add(WithWindow=False)
        
        slide_index = 0
        slide = None
        
        for p in doc.paragraphs:
            style_name = p.style.name.lower()
            text = p.text.strip()
            if not text:
                continue
                
            if "heading 1" in style_name or "heading 2" in style_name:
                slide_index += 1
                layout = 1 if slide_index == 1 else 2
                slide = pres.Slides.Add(slide_index, layout)
                
                if len(slide.Shapes) > 0 and slide.Shapes.Title:
                    slide.Shapes.Title.TextFrame.TextRange.Text = text
            else:
                if slide is None:
                    slide_index += 1
                    slide = pres.Slides.Add(slide_index, 2)
                    
                body_shape = None
                for s in slide.Shapes:
                    if s.HasTextFrame and s != slide.Shapes.Title:
                        body_shape = s
                        break
                        
                if body_shape:
                    tr = body_shape.TextFrame.TextRange
                    if tr.Text:
                        tr.Text = tr.Text + "\n" + text
                    else:
                        tr.Text = text
                        
        ppt_abs = os.path.abspath(ppt_path)
        pres.SaveAs(ppt_abs)
        pres.Close()
        powerpoint.Quit()
        return True
    except Exception as e:
        print(f"Error converting Word to PowerPoint: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def compress_powerpoint(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("ppt/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress presentation image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing powerpoint: {e}")
        return False

def safe_image_convert(input_path, output_path):
    try:
        from PIL import Image
        img = Image.open(input_path)
        if img.mode != 'RGB' and (output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg')):
            img = img.convert('RGB')
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error converting image: {e}")
        return False

def compress_image(input_path, output_path, quality=70, max_width=1920):
    try:
        from PIL import Image
        img = Image.open(input_path)
        # Resize if wider than max_width
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        # Determine output format from extension
        ext = os.path.splitext(output_path)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
        elif ext == '.png':
            img.save(output_path, format='PNG', optimize=True)
        else:
            img.save(output_path, optimize=True)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def compress_excel(input_path, output_path, image_quality=70, max_width=1200):
    try:
        import zipfile
        import io
        from PIL import Image
        
        with zipfile.ZipFile(input_path, 'r') as yin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename.startswith("xl/media/") and any(item.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.width > max_width:
                                ratio = max_width / float(img.width)
                                new_height = int(float(img.height) * ratio)
                                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                            
                            out_bytes = io.BytesIO()
                            img_format = img.format if img.format else "JPEG"
                            if img_format == "PNG" and img.mode in ('RGBA', 'LA'):
                                img.save(out_bytes, format="PNG", optimize=True)
                            else:
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.save(out_bytes, format="JPEG", quality=image_quality, optimize=True)
                                
                            compressed_data = out_bytes.getvalue()
                            if len(compressed_data) < len(data):
                                data = compressed_data
                        except Exception as img_err:
                            print(f"Failed to compress Excel image {item.filename}: {img_err}")
                    yout.writestr(item, data)
        return True
    except Exception as e:
        print(f"Error compressing excel: {e}")
        return False

def merge_excel_files(file_paths, output_path):
    try:
        import openpyxl
        wb_master = openpyxl.Workbook()
        wb_master.remove(wb_master.active)
        
        for path in file_paths:
            wb_sub = openpyxl.load_workbook(path, data_only=True)
            base_name = os.path.splitext(os.path.basename(path))[0]
            for sheet_name in wb_sub.sheetnames:
                ws_sub = wb_sub[sheet_name]
                new_title = f"{base_name}_{sheet_name}"[:30]
                
                cnt = 1
                temp_title = new_title
                while temp_title in wb_master.sheetnames:
                    temp_title = f"{new_title[:27]}_{cnt}"
                    cnt += 1
                
                ws_master = wb_master.create_sheet(title=temp_title)
                
                for r in range(1, ws_sub.max_row + 1):
                    for c in range(1, ws_sub.max_column + 1):
                        cell_val = ws_sub.cell(row=r, column=c).value
                        ws_master.cell(row=r, column=c, value=cell_val)
                        
        wb_master.save(output_path)
        return True
    except Exception as e:
        print(f"Error merging Excel files: {e}")
        return False

def split_excel_file(file_path, page_range_str, fs):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        sheet_names = wb.sheetnames
        
        target_sheets = []
        if not page_range_str or page_range_str.lower() == "all":
            target_sheets = sheet_names
        else:
            parts = page_range_str.split(",")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(sheet_names):
                        target_sheets.append(sheet_names[idx])
                except ValueError:
                    if part in sheet_names:
                        target_sheets.append(part)
        
        if not target_sheets:
            target_sheets = sheet_names
            
        output_paths = []
        for sheet_name in target_sheets:
            wb_new = openpyxl.Workbook()
            wb_new.remove(wb_new.active)
            
            wb_source = openpyxl.load_workbook(file_path, data_only=False)
            ws_source = wb_source[sheet_name]
            ws_new = wb_new.create_sheet(title=sheet_name)
            
            for r in range(1, ws_source.max_row + 1):
                for c in range(1, ws_source.max_column + 1):
                    cell = ws_source.cell(row=r, column=c)
                    ws_new.cell(row=r, column=c, value=cell.value)
            
            base = os.path.splitext(os.path.basename(file_path))[0]
            output_filename = f"{base}_{sheet_name}.xlsx"
            output_path = fs.path(output_filename)
            output_path = fs.get_available_name(output_path)
            wb_new.save(output_path)
            output_paths.append(output_path)
            
        return output_paths
    except Exception as e:
        print(f"Error splitting Excel file: {e}")
        return []

def post_process_docx_layout(file_path):
    try:
        import docx
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls

        def set_cell_shading(cell, color_hex):
            shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
            tcPr = cell._tc.get_or_add_tcPr()
            shd = tcPr.find(docx.oxml.ns.qn('w:shd'))
            if shd is not None:
                tcPr.remove(shd)
            tcPr.append(parse_xml(shading_xml))

        def copy_paragraph(src_p, dst_p):
            if src_p.style is not None:
                dst_p.style = src_p.style
            dst_p.paragraph_format.alignment = src_p.paragraph_format.alignment
            dst_p.paragraph_format.space_before = src_p.paragraph_format.space_before
            dst_p.paragraph_format.space_after = src_p.paragraph_format.space_after
            dst_p.paragraph_format.line_spacing = src_p.paragraph_format.line_spacing
            dst_p.paragraph_format.left_indent = src_p.paragraph_format.left_indent
            dst_p.paragraph_format.right_indent = None
            dst_p.text = ""
            for run in src_p.runs:
                new_run = dst_p.add_run(run.text)
                new_run.bold = run.bold
                new_run.italic = run.italic
                new_run.underline = run.underline
                if run.font is not None:
                    if run.font.name:
                        new_run.font.name = run.font.name
                    if run.font.size:
                        new_run.font.size = run.font.size
                    if run.font.color and run.font.color.rgb:
                        new_run.font.color.rgb = run.font.color.rgb

        def copy_cell_paragraphs(src_cell, dst_cell):
            for i, src_p in enumerate(src_cell.paragraphs):
                if i == 0:
                    dst_p = dst_cell.paragraphs[0]
                else:
                    dst_p = dst_cell.add_paragraph()
                copy_paragraph(src_p, dst_p)

        doc = docx.Document(file_path)
        if len(doc.tables) >= 2:
            doc.tables[0]
            table1 = doc.tables[1]

            # Only apply layout merge if it matches the 3-column Modern resume template layout
            if len(table1.rows) > 0 and len(table1.rows[0].cells) >= 3:
                w0, w1, w2 = None, None, None
                for row in table1.rows:
                    if len(row.cells) >= 3 and row.cells[1]._tc != row.cells[2]._tc:
                        w0 = row.cells[0].width
                        w1 = row.cells[1].width
                        w2 = row.cells[2].width
                        break
                if w0 is None:
                    w0 = table1.rows[0].cells[0].width
                    w1 = table1.rows[0].cells[1].width
                    w2 = table1.rows[0].cells[2].width

                sidebar_color = "1a5276"
                for row in table1.rows:
                    cell = row.cells[0]
                    tcPr = cell._tc.get_or_add_tcPr()
                    shd = tcPr.find(docx.oxml.ns.qn('w:shd'))
                    if shd is not None:
                        fill = shd.get(docx.oxml.ns.qn('w:fill'))
                        if fill and fill != "auto":
                            sidebar_color = fill
                            break

                body = doc.element.body
                table1_element = table1._tbl

                elements_before = []
                for child in body:
                    if child == table1_element:
                        break
                    elements_before.append(child)

                elements_after = []
                found_table1 = False
                for child in body:
                    if child == table1_element:
                        found_table1 = True
                        continue
                    if found_table1:
                        elements_after.append(child)

                elements_to_remove = []
                table0_obj = None
                intermediate_p_obj = None
                for elem in elements_before:
                    tag = elem.tag
                    if tag.endswith('tbl'):
                        for t in doc.tables:
                            if t._tbl == elem:
                                table0_obj = t
                                break
                        elements_to_remove.append(elem)
                    elif tag.endswith('p'):
                        for p in doc.paragraphs:
                            if p._p == elem:
                                intermediate_p_obj = p
                                break
                        elements_to_remove.append(elem)

                items_after = []
                for elem in elements_after:
                    tag = elem.elem if hasattr(elem, 'elem') else elem
                    tag_name = tag.tag
                    if tag_name.endswith('tbl'):
                        tbl_obj = None
                        for t in doc.tables:
                            if t._tbl == elem:
                                tbl_obj = t
                                break
                        if tbl_obj:
                            paras = []
                            for row in tbl_obj.rows:
                                for cell in row.cells:
                                    for p in cell.paragraphs:
                                        paras.append(p)
                            if any(p.text.strip() for p in paras):
                                items_after.append((paras, elem))
                            elements_to_remove.append(elem)
                    elif tag_name.endswith('p'):
                        p_obj = None
                        for p in doc.paragraphs:
                            if p._p == elem:
                                p_obj = p
                                break
                        if p_obj:
                            if p_obj.text.strip():
                                items_after.append(([p_obj], elem))
                            elements_to_remove.append(elem)

                # 1. Insert Row A
                if table0_obj and len(table0_obj.rows) > 0:
                    row_a = table1.add_row()
                    table1.rows[0]._tr.addprevious(row_a._tr)
                    row_a.cells[0].width = w0
                    row_a.cells[1].width = w1
                    row_a.cells[2].width = w2
                    row_a.cells[1].merge(row_a.cells[2])
                    copy_cell_paragraphs(table0_obj.rows[0].cells[0], row_a.cells[0])
                    copy_cell_paragraphs(table0_obj.rows[0].cells[1], row_a.cells[1])
                    set_cell_shading(row_a.cells[0], sidebar_color)
                    for c in row_a.cells[1:]:
                        tcPr = c._tc.get_or_add_tcPr()
                        shd = tcPr.find(docx.oxml.ns.qn('w:shd'))
                        if shd is not None:
                            tcPr.remove(shd)

                # 2. Insert Row B
                if intermediate_p_obj:
                    row_b = table1.add_row()
                    table1.rows[1]._tr.addprevious(row_b._tr)
                    row_b.cells[0].width = w0
                    row_b.cells[1].width = w1
                    row_b.cells[2].width = w2
                    row_b.cells[1].merge(row_b.cells[2])
                    dst_p = row_b.cells[1].paragraphs[0]
                    copy_paragraph(intermediate_p_obj, dst_p)
                    set_cell_shading(row_b.cells[0], sidebar_color)
                    for c in row_b.cells[1:]:
                        tcPr = c._tc.get_or_add_tcPr()
                        shd = tcPr.find(docx.oxml.ns.qn('w:shd'))
                        if shd is not None:
                            tcPr.remove(shd)

                # 3. Append trailing elements
                for paras, _ in items_after:
                    new_row = table1.add_row()
                    new_row.cells[0].width = w0
                    new_row.cells[1].width = w1
                    new_row.cells[2].width = w2
                    new_row.cells[1].merge(new_row.cells[2])
                    cell_0 = new_row.cells[0]
                    for i, src_p in enumerate(paras):
                        if i == 0:
                            dst_p = cell_0.paragraphs[0]
                        else:
                            dst_p = cell_0.add_paragraph()
                        copy_paragraph(src_p, dst_p)
                    set_cell_shading(cell_0, sidebar_color)
                    for c in new_row.cells[1:]:
                        tcPr = c._tc.get_or_add_tcPr()
                        shd = tcPr.find(docx.oxml.ns.qn('w:shd'))
                        if shd is not None:
                            tcPr.remove(shd)

                for elem in elements_to_remove:
                    body.remove(elem)

                doc.save(file_path)
    except Exception as e:
        print("Error during post_process_docx_layout:", e)

def home(request):

    download_url = None
    error = None

    if request.method == "POST":

        try:
            action_type = request.POST.get("action_type", "convert")
            fs = FileSystemStorage(
                location="media/uploads"
            )

            # Helper: build output path from the user's original filename
            def make_output(orig_name, new_ext):
                base = os.path.splitext(orig_name)[0]
                out_name = base + new_ext
                out_path = fs.path(out_name)
                return fs.get_available_name(out_path)

            # Helper: build download URL with clean filename for browser
            def dl_url(stored_path, clean_name):
                return "/download/" + urllib.parse.quote(os.path.basename(stored_path)) + "?name=" + urllib.parse.quote(clean_name)

            if action_type == "word_edit":
                try:
                    uploaded_file = request.FILES.get("editwordfile")
                    if not uploaded_file:
                        raise Exception("No Word document uploaded.")
                    original_name = uploaded_file.name
                    filename = fs.save(original_name, uploaded_file)
                    file_path = fs.path(filename)
                    html = prepare_editor_html_from_docx(file_path)
                    return JsonResponse({
                        "success": True,
                        "html": html,
                        "filename": filename,
                        "original_name": original_name
                    })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "error": str(e)
                    })

            elif action_type == "pdf_edit_load":
                try:
                    uploaded_file = request.FILES.get("editfile")
                    if not uploaded_file:
                        raise Exception("No PDF file uploaded.")
                    original_name = uploaded_file.name
                    filename = fs.save(original_name, uploaded_file)
                    file_path = fs.path(filename)
                    html = prepare_editor_html_from_pdf(file_path)
                    return JsonResponse({
                        "success": True,
                        "html": html,
                        "filename": filename,
                        "original_name": original_name
                    })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "error": str(e)
                    })

            elif action_type == "word_edit_save":
                try:
                    html_content = request.POST.get("html_content", "")
                    original_name = request.POST.get("original_name", "document.docx")
                    
                    base = os.path.splitext(original_name)[0]
                    output_name = base + "_edited.docx"
                    output_path = fs.path(output_name)
                    output_file = fs.get_available_name(output_path)
                    
                    from docx import Document
                    doc = Document()
                    new_parser = HtmlToDocx()
                    new_parser.add_html_to_document(html_content, doc)
                    doc.save(output_file)
                    
                    download_url = dl_url(output_file, os.path.basename(output_file))
                    
                    return JsonResponse({
                        "success": True,
                        "download_url": download_url
                    })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "error": str(e)
                    })

            elif action_type == "pdf_edit_save":
                try:
                    html_content = request.POST.get("html_content", "")
                    original_name = request.POST.get("original_name", "document.pdf")

                    base = os.path.splitext(original_name)[0]
                    docx_tmp = fs.get_available_name(fs.path(base + "_edited_temp.docx"))
                    pdf_out = fs.get_available_name(fs.path(base + "_edited.pdf"))

                    from docx import Document
                    doc = Document()
                    new_parser = HtmlToDocx()
                    new_parser.add_html_to_document(html_content, doc)
                    doc.save(docx_tmp)
                    safe_docx_to_pdf(docx_tmp, pdf_out)
                    if os.path.exists(docx_tmp):
                        os.remove(docx_tmp)

                    clean = os.path.basename(pdf_out)
                    download_url = dl_url(pdf_out, clean)
                    return JsonResponse({
                        "success": True,
                        "download_url": download_url
                    })
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "error": str(e)
                    })

            elif action_type == "convert":
                uploaded_file = request.FILES["documentfile"]
                conversion_type = request.POST.get(
                    "conversion_type"
                )

                # Capture original name BEFORE Django may rename it
                original_name = uploaded_file.name
                filename = fs.save(original_name, uploaded_file)
                file_path = fs.path(filename)

                if conversion_type == "word_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(original_name, ".pdf")
                    safe_docx_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(original_name, ".docx")
                    cv = Converter(file_path)
                    cv.convert(output_file)
                    cv.close()
                    post_process_docx_layout(output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "excel_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(original_name, ".pdf")
                    safe_excel_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_excel":
                    clean = os.path.splitext(original_name)[0] + ".xlsx"
                    output_file = make_output(original_name, ".xlsx")
                    safe_pdf_to_excel(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "image_to_pdf":
                    uploaded_files = request.FILES.getlist("documentfile")
                    if not uploaded_files:
                        raise Exception("Please select at least one image file to convert.")
                    first_orig_name = uploaded_files[0].name
                    temp_paths = []
                    for f in uploaded_files:
                        fn = fs.save(f.name, f)
                        temp_paths.append(fs.path(fn))
                    base = os.path.splitext(first_orig_name)[0]
                    clean = base + ".pdf"
                    output_file = fs.get_available_name(fs.path(clean))
                    success = safe_image_to_pdf(temp_paths, output_file)
                    if not success:
                        raise Exception("Image to PDF conversion failed.")
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "powerpoint_to_pdf":
                    clean = os.path.splitext(original_name)[0] + ".pdf"
                    output_file = make_output(original_name, ".pdf")
                    safe_powerpoint_to_pdf(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "powerpoint_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(original_name, ".docx")
                    safe_powerpoint_to_word(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "pdf_to_powerpoint":
                    clean = os.path.splitext(original_name)[0] + ".pptx"
                    output_file = make_output(original_name, ".pptx")
                    safe_pdf_to_powerpoint(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "word_to_powerpoint":
                    clean = os.path.splitext(original_name)[0] + ".pptx"
                    output_file = make_output(original_name, ".pptx")
                    safe_word_to_powerpoint(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "jpeg_to_png":
                    clean = os.path.splitext(original_name)[0] + ".png"
                    output_file = make_output(original_name, ".png")
                    safe_image_convert(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "png_to_jpeg":
                    clean = os.path.splitext(original_name)[0] + ".jpg"
                    output_file = make_output(original_name, ".jpg")
                    safe_image_convert(file_path, output_file)
                    download_url = dl_url(output_file, clean)

                elif conversion_type == "image_compress":
                    orig_ext = os.path.splitext(original_name)[1].lower()
                    base = os.path.splitext(original_name)[0]
                    clean = original_name
                    out_name = base + "_compressed" + orig_ext
                    output_file = fs.get_available_name(fs.path(out_name))
                    success = compress_image(file_path, output_file)
                    if not success:
                        raise Exception("Image compression failed.")
                    download_url = dl_url(output_file, clean)

            elif action_type == "edit_pdf":
                uploaded_file = request.FILES.get("editfile")
                if not uploaded_file:
                    raise Exception("Please select a PDF file to edit.")
                original_name = uploaded_file.name
                filename = fs.save(original_name, uploaded_file)
                file_path = fs.path(filename)
                base = os.path.splitext(original_name)[0]
                output_file = fs.get_available_name(fs.path(base + "_edited.pdf"))
                safe_edit_pdf(file_path, output_file, request.POST.get("pdf_edit_actions", "[]"))
                download_url = dl_url(output_file, original_name)

            elif action_type == "merge":
                merge_files = request.FILES.getlist("mergefiles")
                merge_format = request.POST.get("merge_format", "pdf")

                if not merge_files or len(merge_files) < 2:
                    raise Exception("Please select at least 2 files to merge.")


                # Capture original names BEFORE saving
                merge_orig_names = [f.name for f in merge_files]
                temp_paths = []
                for f in merge_files:
                    fn = fs.save(f.name, f)
                    temp_paths.append(fs.path(fn))

                def make_merged_name(orig_names, ext):
                    base = os.path.splitext(orig_names[0])[0]
                    out_name = base + ext
                    return fs.get_available_name(fs.path(out_name))

                if merge_format == "pdf":
                    import fitz
                    merged_doc = fitz.open()
                    for path in temp_paths:
                        sub_doc = fitz.open(path)
                        merged_doc.insert_pdf(sub_doc)
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".pdf"
                    output_path = make_merged_name(merge_orig_names, ".pdf")
                    merged_doc.save(output_path)
                    merged_doc.close()
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

                elif merge_format == "docx":
                    import docx
                    from docxcompose.composer import Composer
                    master = docx.Document(temp_paths[0])
                    composer = Composer(master)
                    for path in temp_paths[1:]:
                        doc_temp = docx.Document(path)
                        master.add_page_break()
                        composer.append(doc_temp)
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".docx"
                    output_path = make_merged_name(merge_orig_names, ".docx")
                    composer.save(output_path)
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

                elif merge_format == "xlsx":
                    clean = os.path.splitext(merge_orig_names[0])[0] + ".xlsx"
                    output_path = make_merged_name(merge_orig_names, ".xlsx")
                    success = merge_excel_files(temp_paths, output_path)
                    if not success:
                        raise Exception("Excel merging failed.")
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_path)) + "?name=" + urllib.parse.quote(clean)

            elif action_type == "split":
                uploaded_files = request.FILES.getlist("splitfile")
                page_range_str = request.POST.get("page_range", "all").strip()

                if not uploaded_files:
                    raise Exception("Please select at least one file to split.")

                # Capture original names BEFORE saving
                split_orig_names = [f.name for f in uploaded_files]
                temp_paths = []
                for f in uploaded_files:
                    fn = fs.save(f.name, f)
                    temp_paths.append(fs.path(fn))

                def parse_page_ranges_to_groups(range_str, max_pages):
                    if not range_str or range_str.lower() == "all":
                        return [(f"page_{p+1}", [p]) for p in range(max_pages)]
                    groups = []
                    parts = range_str.split(",")
                    for part in parts:
                        part = part.strip().lower()
                        if not part:
                            continue
                        if part == "odd":
                            pages = [p for p in range(max_pages) if p % 2 == 0]
                            if pages:
                                groups.append(("odd_pages", pages))
                        elif part == "even":
                            pages = [p for p in range(max_pages) if p % 2 != 0]
                            if pages:
                                groups.append(("even_pages", pages))
                        elif "-" in part:
                            try:
                                start, end = part.split("-")
                                s = int(start.strip()) - 1
                                e = int(end.strip()) - 1
                                pages = [p for p in range(s, e + 1) if 0 <= p < max_pages]
                                if pages:
                                    groups.append((f"pages_{start.strip()}-{end.strip()}", pages))
                            except ValueError:
                                pass
                        else:
                            try:
                                p_num = int(part)
                                p = p_num - 1
                                if 0 <= p < max_pages:
                                    groups.append((f"page_{p_num}", [p]))
                            except ValueError:
                                pass
                    return groups

                output_paths = []

                for idx, file_path in enumerate(temp_paths):
                    # Use original uploaded name for output naming
                    orig_name = split_orig_names[idx] if idx < len(split_orig_names) else os.path.basename(file_path)
                    is_pdf = file_path.lower().endswith(".pdf")
                    is_docx = file_path.lower().endswith(".docx")
                    is_xlsx = file_path.lower().endswith(".xlsx") or file_path.lower().endswith(".xls")

                    if not is_pdf and not is_docx and not is_xlsx:
                        continue

                    if is_pdf:
                        import fitz
                        doc = fitz.open(file_path)
                        groups = parse_page_ranges_to_groups(page_range_str, len(doc))
                        if not groups:
                            doc.close()
                            raise Exception(f"Invalid page range specified for {orig_name}.")
                        
                        for group_name, pages in groups:
                            sub_doc = fitz.open(file_path)
                            sub_doc.select(pages)
                            base, ext = os.path.splitext(orig_name)
                            output_filename = f"{base}_{group_name}{ext}"
                            output_path = fs.path(output_filename)
                            output_path = fs.get_available_name(output_path)
                            sub_doc.save(output_path)
                            sub_doc.close()
                            output_paths.append(output_path)
                        doc.close()

                    elif is_docx:
                        temp_pdf_path = os.path.splitext(file_path)[0] + "_temp.pdf"
                        safe_docx_to_pdf(file_path, temp_pdf_path)

                        import fitz
                        doc = fitz.open(temp_pdf_path)
                        groups = parse_page_ranges_to_groups(page_range_str, len(doc))
                        doc.close()

                        if not groups:
                            os.remove(temp_pdf_path)
                            raise Exception(f"Invalid page range specified for {orig_name}.")

                        for group_name, pages in groups:
                            pdf_doc = fitz.open(temp_pdf_path)
                            pdf_doc.select(pages)
                            split_pdf_path = os.path.splitext(file_path)[0] + f"_{group_name}_split_temp.pdf"
                            pdf_doc.save(split_pdf_path)
                            pdf_doc.close()

                            base, ext = os.path.splitext(orig_name)
                            output_filename = f"{base}_{group_name}{ext}"
                            output_path = fs.path(output_filename)
                            output_path = fs.get_available_name(output_path)

                            cv = Converter(split_pdf_path)
                            cv.convert(output_path)
                            cv.close()

                            os.remove(split_pdf_path)

                            post_process_docx_layout(output_path)
                            output_paths.append(output_path)

                        os.remove(temp_pdf_path)

                    elif is_xlsx:
                        excel_outputs = split_excel_file(file_path, page_range_str, fs)
                        output_paths.extend(excel_outputs)

                if not output_paths:
                    raise Exception("No files were successfully split.")

                if len(output_paths) == 1:
                    # Single split file: serve with clean name (no random suffix)
                    base, ext = os.path.splitext(os.path.basename(output_paths[0]))
                    # Strip any Django random suffix — use the stored name as-is from our output_filename var
                    clean_split = split_orig_names[0] if split_orig_names else os.path.basename(output_paths[0])
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_paths[0])) + "?name=" + urllib.parse.quote(clean_split)
                else:
                    import zipfile
                    if len(split_orig_names) == 1:
                        base = os.path.splitext(split_orig_names[0])[0]
                        zip_clean = os.path.splitext(split_orig_names[0])[0] + ".zip"
                    else:
                        zip_clean = "split_results.zip"
                    zip_path = fs.get_available_name(fs.path(zip_clean))
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for path in output_paths:
                            zipf.write(path, os.path.basename(path))
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(zip_path)) + "?name=" + urllib.parse.quote(zip_clean)

            elif action_type == "compress":
                uploaded_files = request.FILES.getlist("compressfiles")
                if not uploaded_files:
                    raise Exception("Please select at least one file to compress.")

                # Capture original names BEFORE saving
                compress_orig_names = [f.name for f in uploaded_files]
                temp_paths = []
                for f in uploaded_files:
                    fn = fs.save(f.name, f)
                    temp_paths.append(fs.path(fn))

                output_paths = []
                for cidx, file_path in enumerate(temp_paths):
                    orig_name = compress_orig_names[cidx] if cidx < len(compress_orig_names) else os.path.basename(file_path)
                    is_pdf = file_path.lower().endswith(".pdf")
                    is_docx = file_path.lower().endswith(".docx")
                    is_xlsx = file_path.lower().endswith(".xlsx") or file_path.lower().endswith(".xls")
                    is_pptx = file_path.lower().endswith(".pptx") or file_path.lower().endswith(".ppt")

                    if not is_pdf and not is_docx and not is_xlsx and not is_pptx:
                        continue

                    base, ext = os.path.splitext(orig_name)
                    output_filename = base + "_compressed" + ext
                    output_path = fs.get_available_name(fs.path(output_filename))

                    success = False
                    if is_pdf:
                        success = compress_pdf(file_path, output_path)
                    elif is_docx:
                        success = compress_docx(file_path, output_path)
                    elif is_xlsx:
                        success = compress_excel(file_path, output_path)
                    elif is_pptx:
                        success = compress_powerpoint(file_path, output_path)

                    if success:
                        output_paths.append(output_path)

                if not output_paths:
                    raise Exception("No files were successfully compressed.")

                if len(output_paths) == 1:
                    orig_name_0 = compress_orig_names[0] if compress_orig_names else os.path.basename(output_paths[0])
                    base0, ext0 = os.path.splitext(orig_name_0)
                    clean_c = orig_name_0
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(output_paths[0])) + "?name=" + urllib.parse.quote(clean_c)
                else:
                    import zipfile
                    if len(compress_orig_names) == 1:
                        base = os.path.splitext(compress_orig_names[0])[0]
                        zip_clean = os.path.splitext(compress_orig_names[0])[0] + ".zip"
                    else:
                        zip_clean = "compressed_results.zip"
                    zip_path = fs.get_available_name(fs.path(zip_clean))
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for path in output_paths:
                            zipf.write(path, os.path.basename(path))
                    download_url = "/download/" + urllib.parse.quote(os.path.basename(zip_path)) + "?name=" + urllib.parse.quote(zip_clean)

        except Exception as e:
            error = str(e)

    return render(
        request,
        "index.html",
        {
            "download_url": download_url,
            "error": error
        }
    )

def download_file(request, filename):
    file_path = os.path.join(
        "media",
        "uploads",
        filename
    )
    # Use the ?name= query param as the browser-facing filename if provided
    display_name = request.GET.get("name", filename)
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=display_name
    )
