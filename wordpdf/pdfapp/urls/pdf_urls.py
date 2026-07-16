from django.urls import path

from pdfapp.views import pdf_views

urlpatterns = [
    path("", pdf_views.pdf_dashboard, name="pdf_dashboard"),
    path("pdf-to-word/", pdf_views.pdf_to_word, name="pdf_to_word"),
    path("pdf-merge/", pdf_views.pdf_merge, name="pdf_merge"),
    path("pdf-split/", pdf_views.pdf_split, name="pdf_split"),
    path("pdf-compress/", pdf_views.pdf_compress, name="pdf_compress"),
    path("pdf-to-excel/", pdf_views.pdf_to_excel, name="pdf_to_excel"),
    path("pdf-edit/", pdf_views.pdf_edit, name="pdf_edit"),
    path("image-to-pdf/", pdf_views.image_to_pdf, name="image_to_pdf"),
]
