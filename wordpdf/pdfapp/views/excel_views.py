from .dashboard import tool_page


def excel_dashboard(request):
    return tool_page(request, "excel/dashboard.html", "excel")


def excel_to_pdf(request):
    return tool_page(request, "excel/excel_to_pdf.html", "excel", "excel-to-pdf")


def excel_merge(request):
    return tool_page(request, "excel/excel_merge.html", "excel", "excel-merge")


def excel_split(request):
    return tool_page(request, "excel/excel_split.html", "excel", "excel-split")


def excel_compress(request):
    return tool_page(request, "excel/excel_compress.html", "excel", "excel-compress")
