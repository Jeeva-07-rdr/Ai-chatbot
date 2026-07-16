from django.urls import path

from pdfapp.views import powerpoint_views

urlpatterns = [
    path("", powerpoint_views.powerpoint_dashboard, name="powerpoint_dashboard"),
    path("ppt-to-pdf/", powerpoint_views.ppt_to_pdf, name="ppt_to_pdf"),
    path("ppt-to-word/", powerpoint_views.ppt_to_word, name="ppt_to_word"),
    path("pdf-to-ppt/", powerpoint_views.pdf_to_ppt, name="pdf_to_ppt"),
    path("word-to-ppt/", powerpoint_views.word_to_ppt, name="word_to_ppt"),
    path("ppt-compress/", powerpoint_views.ppt_compress, name="ppt_compress"),
]
