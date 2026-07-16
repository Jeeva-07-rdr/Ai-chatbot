from django.urls import path

from pdfapp.views import excel_views

urlpatterns = [
    path("", excel_views.excel_dashboard, name="excel_dashboard"),
    path("excel-to-pdf/", excel_views.excel_to_pdf, name="excel_to_pdf"),
    path("excel-merge/", excel_views.excel_merge, name="excel_merge"),
    path("excel-split/", excel_views.excel_split, name="excel_split"),
    path("excel-compress/", excel_views.excel_compress, name="excel_compress"),
]
