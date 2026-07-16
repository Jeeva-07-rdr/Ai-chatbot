"""Build views/dashboard.py from legacy views.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
legacy = (ROOT / "pdfapp" / "views.py").read_text(encoding="utf-8")
lines = legacy.splitlines(keepends=True)

home_block = "".join(lines[1204:1713])
download_block = "".join(lines[1714:1727])

header = '''from django.shortcuts import render
from django.http import FileResponse, JsonResponse
import os
import urllib.parse
import zipfile

from docx import Document

from pdfapp.services.editor import (
    prepare_editor_html_from_docx,
    prepare_editor_html_from_pdf,
)
from pdfapp.services.conversion import (
    safe_docx_to_pdf,
    safe_excel_to_pdf,
    safe_powerpoint_to_pdf,
    safe_powerpoint_to_word,
    safe_pdf_to_powerpoint,
    safe_word_to_powerpoint,
    safe_image_convert,
    merge_excel_files,
    split_excel_file,
)
from pdfapp.services.compression import (
    compress_docx,
    compress_pdf,
    compress_powerpoint,
    compress_image,
    compress_excel,
)
from pdfapp.services.pdf_service import (
    safe_edit_pdf,
    safe_pdf_to_excel,
    safe_image_to_pdf,
)
from pdfapp.services.pdf_to_word import safe_pdf_to_word
from pdfapp.utils.helpers import make_output, dl_url, get_file_storage

try:
    from htmldocx import HtmlToDocx
except Exception:
    HtmlToDocx = None

'''

replacements = [
    (
        'fs = FileSystemStorage(\n                location="media/uploads"\n            )',
        'fs = get_file_storage()',
    ),
    (
        """            def make_output(orig_name, new_ext):
                base = os.path.splitext(orig_name)[0]
                out_name = base + new_ext
                out_path = fs.path(out_name)
                return fs.get_available_name(out_path)

            # Helper: build download URL with clean filename for browser
            def dl_url(stored_path, clean_name):
                return "/download/" + urllib.parse.quote(os.path.basename(stored_path)) + "?name=" + urllib.parse.quote(clean_name)

""",
        "",
    ),
    (
        'output_file = make_output(original_name,',
        'output_file = make_output(fs, original_name,',
    ),
    (
        """                elif conversion_type == "pdf_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(fs, original_name, ".docx")
                    cv = Converter(file_path)
                    cv.convert(output_file)
                    cv.close()
                    post_process_docx_layout(output_file)
                    download_url = dl_url(output_file, clean)""",
        """                elif conversion_type == "pdf_to_word":
                    clean = os.path.splitext(original_name)[0] + ".docx"
                    output_file = make_output(fs, original_name, ".docx")
                    safe_pdf_to_word(file_path, output_file)
                    download_url = dl_url(output_file, clean)""",
    ),
    (
        """                            cv = Converter(split_pdf_path)
                            cv.convert(output_path)
                            cv.close()

                            os.remove(split_pdf_path)

                            post_process_docx_layout(output_path)""",
        """                            safe_pdf_to_word(split_pdf_path, output_path)

                            os.remove(split_pdf_path)""",
    ),
    ('def home(request):', 'def home(request, template_name="dashboard/home.html", active_category="all", active_tool_id=None):'),
    (
        """    return render(
        request,
        "index.html",
        {
            "download_url": download_url,
            "error": error
        }
    )""",
        """    return render(
        request,
        template_name,
        {
            "download_url": download_url,
            "error": error,
            "active_category": active_category,
            "active_tool_id": active_tool_id,
        }
    )""",
    ),
]

for old, new in replacements:
    home_block = home_block.replace(old, new)

tool_page_fn = '''

def tool_page(request, template_name, active_category, active_tool_id=None):
    """Render a category or tool page; POST handling is identical to the home dashboard."""
    return home(
        request,
        template_name=template_name,
        active_category=active_category,
        active_tool_id=active_tool_id,
    )
'''

views_dir = ROOT / "pdfapp" / "views"
views_dir.mkdir(parents=True, exist_ok=True)
(views_dir / "__init__.py").write_text(
    "from .dashboard import home, download_file, tool_page\n",
    encoding="utf-8",
)
(views_dir / "dashboard.py").write_text(
    header + home_block + download_block + tool_page_fn,
    encoding="utf-8",
)
print("Created views/dashboard.py")
