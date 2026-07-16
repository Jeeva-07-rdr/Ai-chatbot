from .dashboard import tool_page


def pdf_dashboard(request):
    return tool_page(request, "pdf/dashboard.html", "pdf")


def pdf_to_word(request):
    return tool_page(request, "pdf/pdf_to_word.html", "pdf", "pdf-to-word")


def pdf_merge(request):
    return tool_page(request, "pdf/pdf_merge.html", "pdf", "pdf-merge")


def pdf_split(request):
    return tool_page(request, "pdf/pdf_split.html", "pdf", "pdf-split")


def pdf_compress(request):
    return tool_page(request, "pdf/pdf_compress.html", "pdf", "pdf-compress")


def pdf_to_excel(request):
    return tool_page(request, "pdf/pdf_to_excel.html", "pdf", "pdf-to-excel")


def pdf_edit(request):
    return tool_page(request, "pdf/pdf_edit.html", "pdf", "pdf-edit")


def image_to_pdf(request):
    return tool_page(request, "pdf/image_to_pdf.html", "pdf", "image-to-pdf")
