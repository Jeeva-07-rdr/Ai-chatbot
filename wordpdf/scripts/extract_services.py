"""Extract service modules from monolithic views.py."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWS = (ROOT / "pdfapp" / "views.py").read_text(encoding="utf-8")

# Service file definitions: (filename, function names in order)
SERVICES = {
    "editor.py": [
        "_read_docx_theme_colors", "_apply_color_mod", "prepare_editor_html_from_docx",
        "prepare_editor_html_from_pdf", "docx_to_editor_html", "post_process_docx_layout",
    ],
    "compression.py": [
        "compress_docx", "compress_pdf", "compress_powerpoint",
        "compress_image", "compress_excel",
    ],
    "pdf_service.py": [
        "_parse_pdf_color", "_pdf_num", "_add_pdf_text_annotation", "safe_edit_pdf",
        "safe_pdf_to_excel", "safe_image_to_pdf",
    ],
    "conversion.py": [
        "safe_docx_to_pdf", "safe_excel_to_pdf", "safe_powerpoint_to_pdf",
        "safe_powerpoint_to_word", "safe_pdf_to_powerpoint", "safe_word_to_powerpoint",
        "safe_image_convert", "merge_excel_files", "split_excel_file",
    ],
}

services_dir = ROOT / "pdfapp" / "services"
services_dir.mkdir(parents=True, exist_ok=True)

def extract_function(name):
    pattern = rf"^def {re.escape(name)}\("
    match = re.search(pattern, VIEWS, re.MULTILINE)
    if not match:
        raise ValueError(f"Function {name} not found")
    start = match.start()
    rest = VIEWS[match.end():]
    # Find next top-level def
    next_def = re.search(r"^def ", rest, re.MULTILINE)
    end = match.end() + next_def.start() if next_def else len(VIEWS)
    return VIEWS[start:end].rstrip() + "\n\n"

COMMON_IMPORTS = '''import html as html_module
import json
import os
import shutil
import urllib.parse

try:
    from docx2pdf import convert
except Exception:
    convert = None

try:
    from pdf2docx import Converter
except Exception:
    Converter = None

try:
    import mammoth
except Exception:
    mammoth = None

try:
    from htmldocx import HtmlToDocx
except Exception:
    HtmlToDocx = None

'''

(services_dir / "__init__.py").write_text("", encoding="utf-8")

for filename, funcs in SERVICES.items():
    body = COMMON_IMPORTS if filename != "editor.py" else COMMON_IMPORTS
    for fn in funcs:
        body += extract_function(fn)
    (services_dir / filename).write_text(body, encoding="utf-8")
    print(f"Wrote {filename}")

print("Service extraction complete.")
