from .dashboard import tool_page


def word_dashboard(request):
    return tool_page(request, "word/dashboard.html", "word")


def word_to_pdf(request):
    return tool_page(request, "word/word_to_pdf.html", "word", "word-to-pdf")


def word_merge(request):
    return tool_page(request, "word/word_merge.html", "word", "word-merge")


def word_split(request):
    return tool_page(request, "word/word_split.html", "word", "word-split")


def word_compress(request):
    return tool_page(request, "word/word_compress.html", "word", "word-compress")


def word_edit(request):
    return tool_page(request, "word/word_edit.html", "word", "word-edit")
