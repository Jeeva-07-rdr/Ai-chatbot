from .dashboard import tool_page


def powerpoint_dashboard(request):
    return tool_page(request, "powerpoint/dashboard.html", "powerpoint")


def ppt_to_pdf(request):
    return tool_page(request, "powerpoint/ppt_to_pdf.html", "powerpoint", "powerpoint-to-pdf")


def ppt_to_word(request):
    return tool_page(request, "powerpoint/ppt_to_word.html", "powerpoint", "powerpoint-to-word")


def pdf_to_ppt(request):
    return tool_page(request, "powerpoint/pdf_to_ppt.html", "powerpoint", "pdf-to-powerpoint")


def word_to_ppt(request):
    return tool_page(request, "powerpoint/word_to_ppt.html", "powerpoint", "word-to-powerpoint")


def ppt_compress(request):
    return tool_page(request, "powerpoint/ppt_compress.html", "powerpoint", "powerpoint-compress")
