from django.urls import path

from pdfapp.views import word_views

urlpatterns = [
    path("", word_views.word_dashboard, name="word_dashboard"),
    path("word-to-pdf/", word_views.word_to_pdf, name="word_to_pdf"),
    path("word-merge/", word_views.word_merge, name="word_merge"),
    path("word-split/", word_views.word_split, name="word_split"),
    path("word-compress/", word_views.word_compress, name="word_compress"),
    path("word-edit/", word_views.word_edit, name="word_edit"),
]
