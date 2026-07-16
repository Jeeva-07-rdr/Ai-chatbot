"""Split monolithic index.html into Django template modules."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "templates" / "index.html"
TPL = ROOT / "templates"

lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)

def slice_lines(start, end):
    return "".join(lines[start - 1 : end])

# Line numbers are 1-based inclusive
styles = slice_lines(14, 1443)  # <style>...</style>
sidebar = slice_lines(1449, 1513)
upload_panel = slice_lines(1518, 1552)
loader = slice_lines(1554, 1558)
success_msg = slice_lines(1560, 1581)
error_msg = slice_lines(1583, 1587)
tool_cards = slice_lines(1591, 1823)
footer = slice_lines(1825, 1827)
word_modal = slice_lines(1832, 1989)
acrobat_modal = slice_lines(1990, 2162)
app_scripts = slice_lines(2168, 4255)

(TPL / "includes").mkdir(parents=True, exist_ok=True)
(TPL / "dashboard").mkdir(parents=True, exist_ok=True)
for cat in ("pdf", "word", "excel", "powerpoint", "image"):
    (TPL / cat).mkdir(parents=True, exist_ok=True)

(TPL / "includes" / "styles.html").write_text(styles, encoding="utf-8")
(TPL / "includes" / "sidebar.html").write_text(sidebar, encoding="utf-8")
(TPL / "includes" / "header.html").write_text(
    "{# Page header placeholder — upload panel title is in upload_modal.html #}\n",
    encoding="utf-8",
)
(TPL / "includes" / "upload_modal.html").write_text(upload_panel, encoding="utf-8")
(TPL / "includes" / "upload_form.html").write_text(
    "{% include \"includes/upload_modal.html\" %}\n", encoding="utf-8"
)
(TPL / "includes" / "loader.html").write_text(loader, encoding="utf-8")
(TPL / "includes" / "recent_history.html").write_text(
    """        <!-- Recent history list -->
        <div class="recent-history mt-4">
            <h6 class="recent-title">
                <i class="fas fa-history"></i> Recent History
            </h6>
            <div id="recentHistoryList" class="recent-list">
                <!-- Downloads will be dynamically rendered here as simple text logs -->
            </div>
        </div>
""",
    encoding="utf-8",
)
(TPL / "includes" / "success_message.html").write_text(success_msg, encoding="utf-8")
(TPL / "includes" / "error_message.html").write_text(error_msg, encoding="utf-8")
(TPL / "includes" / "footer.html").write_text(footer, encoding="utf-8")
(TPL / "includes" / "word_modal.html").write_text(word_modal, encoding="utf-8")
(TPL / "includes" / "acrobat_modal.html").write_text(acrobat_modal, encoding="utf-8")
(TPL / "includes" / "app_scripts.html").write_text(app_scripts, encoding="utf-8")
(TPL / "includes" / "tool_cards.html").write_text(tool_cards, encoding="utf-8")

base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuConverter Pro | Premium Document Utility Suite</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- FontAwesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <!-- Google Fonts (Outfit) -->
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap">
    {% include "includes/styles.html" %}
    {% block extra_head %}{% endblock %}
</head>
<body>
{% block body %}{% endblock %}
{% include "includes/word_modal.html" %}
{% include "includes/acrobat_modal.html" %}
<!-- Bootstrap 5 JS Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
{% block page_init %}{% endblock %}
{% include "includes/app_scripts.html" %}
</body>
</html>
"""
(TPL / "base.html").write_text(base_html, encoding="utf-8")

home_html = """{% extends "base.html" %}
{% block body %}
<div class="app-container">
    {% include "includes/sidebar.html" %}
    <main class="main-wrapper">
        {% include "includes/header.html" %}
        {% include "includes/upload_form.html" %}
        {% include "includes/loader.html" %}
        {% include "includes/success_message.html" %}
        {% include "includes/error_message.html" %}
        {% include "includes/tool_cards.html" %}
        {% include "includes/footer.html" %}
    </main>
</div>
{% endblock %}
{% block page_init %}
{% if active_tool_id %}
<script>
window.__INIT_TOOL__ = "{{ active_tool_id }}";
window.__INIT_CATEGORY__ = "{{ active_category|default:'all' }}";
</script>
{% endif %}
{% endblock %}
"""
(TPL / "dashboard" / "home.html").write_text(home_html, encoding="utf-8")

TOOL_PAGES = {
    "pdf/dashboard.html": ("pdf", None),
    "pdf/pdf_to_word.html": ("pdf", "pdf-to-word"),
    "pdf/pdf_merge.html": ("pdf", "pdf-merge"),
    "pdf/pdf_split.html": ("pdf", "pdf-split"),
    "pdf/pdf_compress.html": ("pdf", "pdf-compress"),
    "pdf/pdf_to_excel.html": ("pdf", "pdf-to-excel"),
    "pdf/pdf_edit.html": ("pdf", "pdf-edit"),
    "pdf/image_to_pdf.html": ("pdf", "image-to-pdf"),
    "word/dashboard.html": ("word", None),
    "word/word_to_pdf.html": ("word", "word-to-pdf"),
    "word/word_merge.html": ("word", "word-merge"),
    "word/word_split.html": ("word", "word-split"),
    "word/word_compress.html": ("word", "word-compress"),
    "word/word_edit.html": ("word", "word-edit"),
    "excel/dashboard.html": ("excel", None),
    "excel/excel_to_pdf.html": ("excel", "excel-to-pdf"),
    "excel/excel_merge.html": ("excel", "excel-merge"),
    "excel/excel_split.html": ("excel", "excel-split"),
    "excel/excel_compress.html": ("excel", "excel-compress"),
    "powerpoint/dashboard.html": ("powerpoint", None),
    "powerpoint/ppt_to_pdf.html": ("powerpoint", "powerpoint-to-pdf"),
    "powerpoint/ppt_to_word.html": ("powerpoint", "powerpoint-to-word"),
    "powerpoint/pdf_to_ppt.html": ("powerpoint", "pdf-to-powerpoint"),
    "powerpoint/word_to_ppt.html": ("powerpoint", "word-to-powerpoint"),
    "powerpoint/ppt_compress.html": ("powerpoint", "powerpoint-compress"),
    "image/dashboard.html": ("image", None),
    "image/jpeg_to_png.html": ("image", "jpeg-to-png"),
    "image/png_to_jpeg.html": ("image", "png-to-jpeg"),
    "image/image_compress.html": ("image", "image-compress"),
}

for rel_path, (category, tool_id) in TOOL_PAGES.items():
    content = '{% extends "dashboard/home.html" %}\n'
    (TPL / rel_path).write_text(content, encoding="utf-8")

print("Templates split successfully.")
